"""Versioned aquatic context overlays; preserve native observations and review uncertainty."""

import argparse
import hashlib
import json
import math
import re
import shutil
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import polars as pl

from ecotox_comparison import MISSING, documented_context, summarize_strata
from screen import HERE, hashes, write_csv
from weekly_report import verify_manifest

FIELDS = {'exposure_type', 'exposure_hours', 'medium', 'control_type_raw',
          'initial_ph', 'temperature_c'}
NUMERIC = {'exposure_hours', 'initial_ph', 'temperature_c'}
STATUSES = {'verified_from_primary_source', 'provisional', 'not_reported', 'access_gap',
            'ambiguous', 'contradiction'}
KINDS = {'primary_fulltext', 'primary_abstract', 'secondary'}
LEVELS = {'scientific_review', 'AI_experimental'}


def value_check(field, value):
    if field in NUMERIC:
        if (type(value) not in {int, float} or not math.isfinite(value) or
                field == 'exposure_hours' and value <= 0 or
                field == 'initial_ph' and not 0 <= value <= 14):
            raise ValueError(f'Invalid numeric context: {field}')
    elif not isinstance(value, str) or not value.strip() or value.strip().upper() in MISSING:
        raise ValueError(f'Known context requires a nonmissing text value: {field}')


def load_sources(directory):
    """Verify the caller's evidence registry; a hash does not verify scientific claims."""
    directory = Path(directory).resolve()
    registry = directory / 'sources.json'
    sources, files = {}, [registry]
    for record in json.loads(registry.read_text()):
        sid = record.get('source_id')
        if not isinstance(sid, str) or not sid.strip() or sid in sources:
            raise ValueError('Source registry requires unique nonempty IDs')
        if record.get('kind') not in KINDS:
            raise ValueError('Unknown source kind')
        relative = Path(record.get('file', ''))
        path = (directory / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(directory) or not path.is_file():
            raise ValueError('Source files must be inside the evidence directory')
        expected = record.get('sha256', '')
        if not re.fullmatch(r'[0-9a-f]{64}', expected) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Source file hash mismatch')
        if not re.fullmatch(r'[1-9][0-9]*', str(record.get('reference_number', ''))):
            raise ValueError('Source registry requires an ECOTOX reference number')
        sources[sid] = record
        files.append(path)
    return sources, files


def apply_overlays(observations, decisions, sources, mode = 'reviewed'):
    """Apply explicit field decisions in memory, never changing raw values or identifiers."""
    if mode not in {'reviewed', 'experimental'}:
        raise ValueError('Mode must be reviewed or experimental')
    by_id = {r['measurement_id']: r for r in observations}
    if len(by_id) != len(observations):
        raise ValueError('Unique measurement IDs required')
    seen, accepted, audit = set(), {}, []
    test_rows = defaultdict(set)
    for row in observations:
        test_rows[row['test_id']].add(row['measurement_id'])
    for decision in decisions:
        cid, field = decision.get('measurement_id'), decision.get('field')
        if cid not in by_id or field not in FIELDS or (cid, field) in seen:
            raise ValueError('Context decisions require known unique measurement/allowed-field pairs')
        seen.add((cid, field))
        source = sources.get(decision.get('source_id'))
        if not source or source.get('kind') not in KINDS:
            raise ValueError('Context decision requires a registered source')
        if str(source['reference_number']) != str(by_id[cid]['reference_number']):
            raise ValueError('Source reference does not match the observation')
        status, level = decision.get('status'), decision.get('review_level')
        if status not in STATUSES or level not in LEVELS:
            raise ValueError('Unknown context status or review level')
        for key in ('source_locator', 'rationale', 'reviewer', 'review_date'):
            if not isinstance(decision.get(key), str) or not decision[key].strip():
                raise ValueError(f'Context decision requires {key}')
        if date.fromisoformat(decision['review_date']).isoformat() != decision['review_date']:
            raise ValueError('Use an ISO review date')
        original = by_id[cid].get(field)
        if ('original' not in decision or type(original) is bool or
                type(decision['original']) is bool or decision['original'] != original):
            raise ValueError('Original context does not match the frozen observation')
        proposed = decision.get('proposed')
        if proposed is not None or status in {'verified_from_primary_source', 'provisional'}:
            value_check(field, proposed)
        if status == 'verified_from_primary_source' and source['kind'] != 'primary_fulltext':
            raise ValueError('Verified primary-source context requires primary full text')
        apply = (status == 'verified_from_primary_source' and level == 'scientific_review' or
                 mode == 'experimental' and status in {'verified_from_primary_source', 'provisional'}
                 and source['kind'] in {'primary_fulltext', 'primary_abstract'})
        # A native nonmissing disagreement is a contradiction, never a silent correction.
        missing = original is None or isinstance(original, str) and original.strip().upper() in MISSING
        conflict = not missing and proposed is not None and proposed != original
        if apply and conflict:
            raise ValueError('Nonmissing native contradiction requires unresolved review, not an override')
        if apply:
            accepted[cid, field] = proposed
        audit.append({
            'measurement_id': cid, 'test_id': by_id[cid]['test_id'], 'field': field,
            'original_json': json.dumps(original), 'proposed_json': json.dumps(proposed),
            'status': status, 'review_level': level, 'source_id': decision['source_id'],
            'source_kind': source['kind'], 'source_sha256': source['sha256'],
            'source_locator': decision['source_locator'], 'rationale': decision['rationale'],
            'reviewer': decision['reviewer'], 'review_date': decision['review_date'],
            'native_disagreement': conflict, 'applied': apply,
        })
    # These fields describe a test, not a concentration slot. Require explicit coverage.
    for (cid, field), proposed in accepted.items():
        for sibling in test_rows[by_id[cid]['test_id']]:
            if (sibling, field) not in accepted or accepted[sibling, field] != proposed:
                raise ValueError('Test-level overlays require consistent decisions for every admitted sibling slot')
    changed = []
    for row in observations:
        edits = {field: value for (cid, field), value in accepted.items() if cid == row['measurement_id']}
        result = {**row, **edits}
        result['original_context_json'] = json.dumps({field: row.get(field) for field in sorted(FIELDS)}, sort_keys = True)
        result['applied_context_fields'] = ';'.join(sorted(edits))
        result['context_overlay_mode'] = mode
        gaps = documented_context(result, {'control_type': result.get('control_type_raw')})
        result['reported_context_complete'] = not gaps
        result['context_gaps'] = ';'.join(gaps)
        changed.append(result)
    return changed, audit


def run(comparison, overlays, sources, output, mode = 'reviewed'):
    comparison, overlays, sources, output = [Path(p).resolve() for p in (comparison, overlays, sources, output)]
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output)
                              for p in (comparison, overlays, sources)):
        raise ValueError('Use a new output directory separate from inputs')
    verify_manifest(comparison / 'manifest.json')
    registry, evidence_files = load_sources(sources)
    inputs = [comparison / 'manifest.json', comparison / 'aquatic_observations.csv', overlays, *evidence_files]
    before = hashes(inputs)
    original = pl.read_csv(comparison / 'aquatic_observations.csv', infer_schema_length = None).to_dicts()
    adjudicated, audit = apply_overlays(original, json.loads(overlays.read_text()), registry, mode)
    summaries, coverage = [], []
    for name, rows in [('original', original), ('source_adjudicated', adjudicated)]:
        for documented in (False, True):
            scenario = name + ('_reported_context_only' if documented else '_all_core')
            summaries.extend({**r, 'scenario': scenario} for r in summarize_strata(rows, documented_only = documented))
            for policy in sorted({r['policy'] for r in rows}):
                selected = [r for r in rows if r['policy'] == policy and
                            (not documented or r['reported_context_complete'])]
                coverage.append({'scenario': scenario, 'policy': policy, 'slots': len(selected),
                                 'compounds': len({r['compound_id'] for r in selected})})
    output.parent.mkdir(parents = True, exist_ok = True)
    stage = Path(tempfile.mkdtemp(prefix = '.context-overlay-', dir = output.parent))
    try:
        shutil.copyfile(comparison / 'aquatic_observations.csv', stage / 'original_aquatic_observations.csv')
        if adjudicated:
            columns = list(dict.fromkeys(key for row in adjudicated for key in row))
            write_csv(stage / 'source_adjudicated_observations.csv', adjudicated, columns)
        columns = ['measurement_id', 'test_id', 'field', 'original_json', 'proposed_json', 'status',
                   'review_level', 'source_id', 'source_kind', 'source_sha256', 'source_locator',
                   'rationale', 'reviewer', 'review_date', 'native_disagreement', 'applied']
        write_csv(stage / 'context_decisions.csv', audit, columns)
        write_csv(stage / 'coverage.csv', coverage, ['scenario', 'policy', 'slots', 'compounds'])
        if summaries:
            write_csv(stage / 'compound_context_summaries.csv', summaries, list(summaries[0]))
        if hashes(inputs) != before:
            raise ValueError('Inputs changed during context adjudication')
        manifest = {'input_hashes': before,
            'output_hashes': {str(output / Path(k).name): v for k, v in hashes(list(stage.iterdir())).items()},
            'code_hashes': hashes([Path(__file__), HERE / 'ecotox_comparison.py']),
            'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
            'mode': mode, 'decisions': len(audit), 'applied_field_decisions': sum(r['applied'] for r in audit),
            'coverage': coverage, 'new_rat_admissions': 0,
            'scope': 'Separate context sensitivity; source kinds/reviewer identities are caller assertions. '
                     'Experimental mode can apply provisional primary abstracts and AI reviews. '
                     'Reported context does not establish study quality or exposure equivalence. '
                     'No native values, identities, core admissions or rat baseline changed. '
                     'Duplicate decisions are not applied by this standalone context comparison.'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
        if output.exists():
            raise ValueError('Output appeared before publication')
        stage.rename(output)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('comparison', 'overlays', 'sources', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--mode', choices = ['reviewed', 'experimental'], default = 'reviewed')
    args = parser.parse_args()
    result = run(args.comparison, args.overlays, args.sources, args.output, args.mode)
    print(json.dumps({key: result[key] for key in ('mode', 'decisions', 'applied_field_decisions', 'coverage')}, indent = 2))
