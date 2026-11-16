"""Audit an unapproved verification release and apply identity holds without fitting models."""

import argparse
import csv
import json
import re
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import numpy as np
import polars as pl
from rdkit import Chem, DataStructs
from rdkit.Chem import Draw, rdMolDescriptors

from ablations import _splits
from labels import attach_labels
from screen import HERE, hashes, write_csv
from structure import structure_features
from triage_dietary import Text

SOURCE_FIELDS = ('compound_id', 'activity_id', 'assay_chembl_id', 'document_chembl_id',
                 'molecule_url', 'assay_url', 'doi_url', 'source_compound_name', 'canonical_smiles',
                 'assay_description', 'standard_type', 'standard_relation', 'standard_value',
                 'standard_units', 'source_comment', 'source_snapshot_sha256')
CONSISTENT = 'PAPER_SUBSTITUENT_AND_SMILES_CONSISTENT_NOT_FINAL_STRUCTURE_ATTESTATION'
EXACT = 'EXACT_FULL_STEREO_INCHIKEY'
CONNECTIVITY = 'CONNECTIVITY_ONLY_STEREOCHEMISTRY_NOT_ESTABLISHED'


def read(path):
    with Path(path).open(encoding = 'utf-8-sig', newline = '') as stream:
        return list(csv.DictReader(stream))


def unique(rows, key):
    values = [r[key] for r in rows]
    if any(not v for v in values) or len(values) != len(set(values)):
        raise ValueError(f'Unique nonempty {key} values required')
    return {r[key]: r for r in rows}


def comparison(a, b):
    if a == b:
        return EXACT
    if a.split('-')[0] == b.split('-')[0]:
        return CONNECTIVITY
    return 'STRUCTURE_MISMATCH'


def parse_reference(snapshot):
    if snapshot.get('status') != 200:
        return None, 'source_unavailable', ''
    if snapshot['kind'] == 'pubchem_json':
        try:
            props = json.loads(snapshot['body'])['PropertyTable']['Properties']
            if len(props) != 1:
                return None, 'ambiguous_reference', ''
            return props[0]['InChIKey'], 'retrieved', ''
        except (KeyError, TypeError, json.JSONDecodeError):
            return None, 'malformed_reference', ''
    parser = Text()
    parser.feed(snapshot['body'])
    plain = ' '.join(' '.join(parser.parts).split())
    match = re.search(r'InChIKey\)?\s*([A-Z]{14}-[A-Z]{10}-[A-Z])', plain)
    origin = re.search(r'Substance origin\s+(.{0,100})', plain)
    return (match[1] if match else None, 'retrieved' if match else 'key_not_found',
            origin[1] if origin else '')


def reject_held_activity(labels, hold_ids):
    """A schema-valid proposal must not override a current source-identity hold."""
    for row in labels:
        if row['compound_id'] in hold_ids and row.get('herbicidal_activity', '').strip() in {
            'active', 'inactive'
        }:
            raise ValueError(f"Activity assignment blocked by identity hold: {row['compound_id']}")


def allyl_hypothesis(smiles):
    """Illustrate the reported alternative; do not claim it is an approved source correction."""
    mol = Chem.MolFromSmiles(smiles)
    matches = mol.GetSubstructMatches(Chem.MolFromSmarts('[#7]-[CH]1[CH2][CH2]1')) if mol else []
    if len(matches) != 1:
        raise ValueError('Illustration requires exactly one N-cyclopropyl group')
    _, a, b, c = matches[0]
    edit = Chem.RWMol(mol)
    edit.RemoveBond(a, c)
    edit.GetBondBetweenAtoms(b, c).SetBondType(Chem.BondType.DOUBLE)
    candidate = edit.GetMol()
    Chem.SanitizeMol(candidate)
    if rdMolDescriptors.CalcMolFormula(mol) != rdMolDescriptors.CalcMolFormula(candidate):
        raise ValueError('Illustrative isomers must have identical formula')
    frozen = structure_features(smiles)
    hypothetical = structure_features(Chem.MolToSmiles(candidate))
    a_bits, b_bits = [DataStructs.CreateFromBitString(''.join(map(str, r['fingerprint'])))
                      for r in (frozen, hypothetical)]
    result = {'status': 'hypothetical_representation_demo_not_an_approved_correction',
              'frozen_smiles': frozen['canonical_structure'],
              'hypothetical_allyl_smiles': hypothetical['canonical_structure'],
              'frozen_inchikey': frozen['structure_inchikey'],
              'hypothetical_allyl_inchikey': hypothetical['structure_inchikey'],
              'formula': frozen['derived_formula'], 'same_formula': True,
              'different_full_inchikey': frozen['structure_inchikey'] != hypothetical['structure_inchikey'],
              'morgan_tanimoto': DataStructs.TanimotoSimilarity(a_bits, b_bits),
              'different_morgan_bits': sum(x != y for x, y in zip(
                  frozen['fingerprint'], hypothetical['fingerprint'], strict = True)),
              'activity_transfer_approved': False}
    svg = Draw.MolsToGridImage([mol, candidate], molsPerRow = 2, subImgSize = (500, 350),
                              legends = ['Frozen CHEMBL2253255: N-cyclopropyl',
                                         'Illustrative N-allyl hypothesis: NOT verified'], useSVG = True)
    return result, svg


def support(name, chosen, features):
    y = np.array([label for _, label in chosen], dtype = int)
    groups = np.array([features[c]['scaffold'] for c, _ in chosen])
    x = np.zeros((len(y), 1))
    return {'scenario_NOT_APPROVED': name, 'n': len(y), 'positives': int(y.sum()),
            'negatives': int(len(y) - y.sum()), 'scaffolds': len(set(groups)),
            'positive_scaffolds': len(set(groups[y == 1])),
            'negative_scaffolds': len(set(groups[y == 0])),
            'three_fold_support': _splits(x, y, groups, 3)[0],
            'five_fold_support': _splits(x, y, groups, 5)[0], 'model_fitted': False}


def audit(release, prior, feature_rows, snapshots = ()):
    if release['manifest'].get('training_use_approved') is not False:
        raise ValueError('This audit requires an explicitly unapproved release')
    matrix = unique(release['matrix'], 'compound_id')
    features = unique(feature_rows, 'compound_id')
    if set(matrix) != set(features):
        raise ValueError('Release and frozen feature IDs must match')
    labels = attach_labels(feature_rows, release['labels'])
    if len(labels) != len(release['labels']) or any(
        r['activity_target'] is not None or r['origin_target'] is not None for r in labels
    ):
        raise ValueError('Unapproved working labels must remain unknown')
    previous = unique(prior, 'activity_id')
    observations = unique(release['log'], 'activity_id')
    if set(previous) != set(observations):
        raise ValueError('Observation IDs must match prior release')
    if any(r[k] != previous[i][k] for i, r in observations.items() for k in SOURCE_FIELDS):
        raise ValueError('Original observation fields changed')
    if {r['compound_id'] for r in observations.values()} != set(matrix):
        raise ValueError('Observation and matrix compound IDs must match')
    for cid, r in matrix.items():
        if r['critical_hold'] not in ('YES', 'NO'):
            raise ValueError('Critical hold must be explicitly YES or NO')
        mol = Chem.MolFromSmiles(r['canonical_smiles'])
        if mol is None or Chem.MolToInchiKey(mol) != r['rdkit_inchikey']:
            raise ValueError(f'Invalid computed identity: {cid}')
        if Chem.MolToSmiles(mol) != features[cid]['canonical_structure']:
            raise ValueError(f'Frozen structure changed: {cid}')
        if r['approved_herbicidal_activity'] != 'unknown' or r['approved_natural_origin'] != 'unknown':
            raise ValueError('Matrix must not promote unapproved labels')
    if len({r['rdkit_inchikey'] for r in matrix.values()}) != len(matrix):
        raise ValueError('Duplicate full InChIKey')
    source = unique(release['crosswalk'], 'compound_id')
    unique(release['crosswalk'], 'source_compound')
    historical = unique(release['conditional'], 'compound_id')
    if set(historical) != set(matrix) or not set(source) <= set(matrix):
        raise ValueError('Conditional/crosswalk IDs do not match release')
    critical = {c for c, r in matrix.items() if r['critical_hold'] == 'YES'}
    source_critical = {c for c, r in source.items() if r['crosswalk_status'] == 'CLEAR_STRUCTURE_CONFLICT'}
    if critical != source_critical:
        raise ValueError('Critical hold flags disagree across release tables')
    for cid, r in source.items():
        if r['frozen_smiles'] != matrix[cid]['canonical_smiles'] or r['frozen_inchikey'] != matrix[cid]['rdkit_inchikey']:
            raise ValueError('Crosswalk frozen identity differs from matrix')
    saved = unique(list(snapshots), 'key') if snapshots else {}
    references = []
    unique(release['references'], 'compound_id')
    for r in release['references']:
        cid = r['compound_id']
        if cid not in matrix or r['frozen_inchikey'] != matrix[cid]['rdkit_inchikey']:
            raise ValueError('Reference frozen identity differs from matrix')
        if r['frozen_smiles'] != matrix[cid]['canonical_smiles']:
            raise ValueError('Reference frozen SMILES differ from matrix')
        derived = comparison(r['frozen_inchikey'], r['reference_inchikey'])
        if matrix[cid]['full_inchikey_external_match'] != derived:
            raise ValueError('Matrix and reference comparison disagree')
        if derived != r['comparison']:
            raise ValueError('Declared reference comparison is inconsistent')
        external = saved.get('reference:' + cid)
        actual_key, state, origin = parse_reference(external) if external else (None, 'not_retrieved', '')
        if external and external['reference_url'] != r['reference_url']:
            raise ValueError('Reference snapshot URL mismatch')
        references.append({'compound_id': cid, 'name': r['claimed_name'],
                           'released_comparison': derived, 'reference_url': r['reference_url'],
                           'frozen_inchikey': r['frozen_inchikey'],
                           'released_reference_inchikey': r['reference_inchikey'],
                           'retrieved_reference_inchikey': actual_key, 'source_status': state,
                           'independently_retrieved_comparison': comparison(r['frozen_inchikey'], actual_key)
                                                               if actual_key else 'not_verified',
                           'source_origin_excerpt': origin, 'origin_approved': False})
    if {c for c, r in matrix.items() if r['full_inchikey_external_match'] == EXACT} != {
        r['compound_id'] for r in references if r['released_comparison'] == EXACT
    }:
        raise ValueError('Matrix exact-match claims lack matching references')
    for cid, r in source.items():
        observed = [e for e in observations.values() if e['compound_id'] == cid and
                    e['assay_chembl_id'] == 'CHEMBL3066645']
        if len(observed) != 1:
            raise ValueError('Li crosswalk requires one corresponding frozen observation')
        e = observed[0]
        expected = {('>', '80.0', '%'): 'over_80_band',
                    ('<', '50.0', '%'): 'under_50_band'}.get(
                        (e['standard_relation'], e['standard_value'], e['standard_units']))
        if expected is None or r['chEMBL_frozen_recorded_band'] != expected:
            raise ValueError('Li band differs from frozen observation')
        if r['reported_response_band_agrees_with_paper_narrative'] == 'YES' and \
           r['source_paper_reported_A_retroflexus_post_emergence'] != expected:
            raise ValueError('Claimed paper-band agreement is inconsistent')
    reference_by_id = {r['compound_id']: r for r in references}
    effective, queue = [], []
    for cid in sorted(matrix):
        r = matrix[cid]
        effective.append({'compound_id': cid,
                          'historical_conditional_NOT_LABEL': historical[cid]['conditional_activity_NOT_A_LABEL'],
                          'effective_conditional_NOT_LABEL': 'identity_hold' if cid in critical else
                              historical[cid]['conditional_activity_NOT_A_LABEL'],
                          'critical_hold': cid in critical, 'approved_activity': 'unknown'})
        status = ('critical_identity_hold' if cid in critical else 'live_reference_conflict'
                  if reference_by_id.get(cid, {}).get('independently_retrieved_comparison') == 'STRUCTURE_MISMATCH'
                  else 'li_source_check_pending'
                  if cid in source and source[cid]['crosswalk_status'] != CONSISTENT else
                  'li_substituent_consistent_visual_check_pending' if cid in source else
                  'external_identity_match_policy_pending' if r['full_inchikey_external_match'] == EXACT
                  else 'source_structure_review_pending')
        queue.append({'compound_id': cid, 'priority': status,
                      'source_compound': source.get(cid, {}).get('source_compound', ''),
                      'source_crosswalk_status': r['primary_paper_crosswalk_state'],
                      'full_inchikey_external_match': r['full_inchikey_external_match'],
                      'next_action': r['remaining_required_verification'],
                      'approved_activity': 'unknown', 'approved_origin': 'unknown'})
    band = lambda r: int(r['chEMBL_frozen_recorded_band'] == 'over_80_band')
    scenarios = [support('Li historical 24: unapproved', [(c, band(r)) for c, r in source.items()], features),
                 support('Li without critical hold: still unapproved',
                         [(c, band(r)) for c, r in source.items() if c not in critical], features),
                 support('Li 21 consistency leads: still not visually verified',
                         [(c, band(r)) for c, r in source.items() if r['crosswalk_status'] == CONSISTENT], features)]
    exact_refs = [r for r in release['references'] if r['comparison'] == EXACT]
    scenarios.append(support('Hypothetical occurrence/manufacturing-provenance contrast: NOT origin truth',
                             [(r['compound_id'], int(r['claimed_origin'].startswith('natural'))) for r in exact_refs], features))
    return {'references': references, 'effective': effective, 'queue': queue, 'support': scenarios,
            'summary': {'n': len(matrix), 'observations': len(observations), 'critical_holds': sorted(critical),
                        'released_reference_counts': dict(Counter(r['released_comparison'] for r in references)),
                        'retrieved_reference_counts': dict(Counter(r['independently_retrieved_comparison'] for r in references)),
                        'effective_conditional_counts_NOT_APPROVED': dict(Counter(r['effective_conditional_NOT_LABEL'] for r in effective)),
                        'approved_activity_labels': 0, 'approved_origin_labels': 0,
                        'model_fits': 0, 'activity_model_status': 'blocked_unapproved_labels',
                        'original_source_field_changes': 0}}


def lead_candidates(leads, snapshots, features):
    saved = {s['key']: s for s in snapshots}
    identities, chemistry = [], []
    known = {r['structure_inchikey']: r['compound_id'] for r in features if r.get('structure_inchikey')}
    for i, row in enumerate(leads):
        s = saved.get('lead:' + row['name'])
        prop, status = None, 'not_retrieved'
        if s:
            status = 'name_not_resolved' if s['status'] == 404 else 'source_unavailable'
            if s['status'] == 200:
                try:
                    properties = json.loads(s['body'])['PropertyTable']['Properties']
                    if len(properties) == 1:
                        prop, status = properties[0], 'name_lookup_candidate_requires_source_match'
                    else:
                        status = 'ambiguous_name_result'
                except (KeyError, TypeError, json.JSONDecodeError):
                    status = 'malformed_result'
        smiles = (prop.get('SMILES') or prop.get('IsomericSMILES')) if prop else None
        computed = structure_features(smiles)
        if prop and (computed['structure_status'] != 'valid' or
                     computed['structure_inchikey'] != prop['InChIKey']):
            status = 'identity_consistency_failure'
            computed = structure_features(None)
        identity = f"verification-lead:{i + 1:02d}"
        identities.append({'compound_id': identity, 'name': row['name'], 'status': status,
                           'pubchem_cid': prop.get('CID') if prop else None,
                           'resolved_inchikey': computed['structure_inchikey'],
                           'source_reference': row['source_reference'],
                           'reported_evidence_NOT_LABEL': row['reported_evidence'],
                           'source_structure_match': 'not_reviewed',
                           'existing_frozen_match': known.get(computed['structure_inchikey'], ''),
                           'request_url': s['url'] if s else '',
                           'approved_activity': 'unknown', 'approved_origin': 'unknown'})
        chemistry.append({'compound_id': identity, 'query': row['name'],
                          'selection_target': None, 'activity_target': None, 'origin_target': None,
                          **computed})
    return identities, chemistry


def run(release, prior, features, output, snapshots = None):
    release, prior, features, output = [Path(p).resolve() for p in (release, prior, features, output)]
    inputs = [release, prior, features] + ([Path(snapshots).resolve()] if snapshots else [])
    if any(p.is_relative_to(output) or output.is_relative_to(p) for p in inputs):
        raise ValueError('Output must be separate from input paths')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output directory')
    manifest = json.loads((release / 'release_manifest.json').read_text())
    source_files = sorted(release.iterdir())
    expected_files = set(manifest['file_sha256']) | {'release_manifest.json'}
    if {p.name for p in source_files} != expected_files:
        raise ValueError('Release inventory differs from manifest')
    for name, value in manifest['file_sha256'].items():
        if hashes([release / name])[str(release / name)] != value:
            raise ValueError(f'Release hash mismatch: {name}')
    data = {'manifest': manifest}
    for key, name in {'matrix': 'all_154_compound_verification_matrix.csv', 'labels': 'reviewed_labels.csv',
                      'log': 'evidence_log_with_verification.csv', 'crosswalk': 'li_2006_24_compound_source_crosswalk.csv',
                      'conditional': 'conditional_assay_screen_NOT_FOR_TRAINING.csv',
                      'references': 'independent_structure_origin_crosschecks.csv'}.items():
        data[key] = read(release / name)
    snapshot_paths = sorted(Path(snapshots).glob('[0-9]*.json')) if snapshots else []
    saved = [json.loads(p.read_text()) for p in snapshot_paths]
    feature_rows = pl.read_parquet(features).to_dicts()
    result = audit(data, read(prior), feature_rows, saved)
    leads, lead_features = lead_candidates(
        read(release / 'new_out_of_worksheet_compound_leads.csv'), saved, feature_rows)
    result['summary']['new_lead_identity_status'] = dict(Counter(r['status'] for r in leads))
    output.mkdir(parents = True, exist_ok = True)
    for name, key in [('reference_checks.csv', 'references'), ('effective_conditional_screen.csv', 'effective'),
                       ('review_priority.csv', 'queue'), ('model_readiness.csv', 'support')]:
        rows = result[key]
        write_csv(output / name, rows, list(rows[0]))
    hold_rows = [{'compound_id': cid, 'hold_type': 'activity_source_identity_conflict',
                  'status': 'unresolved_do_not_transfer_activity'}
                 for cid in result['summary']['critical_holds']]
    write_csv(output / 'identity_holds.csv', hold_rows, ['compound_id', 'hold_type', 'status'])
    held = 'CHEMBL2253255'
    if held in result['summary']['critical_holds']:
        source = next(r for r in data['matrix'] if r['compound_id'] == held)
        case, svg = allyl_hypothesis(source['canonical_smiles'])
        (output / 'identity_case.json').write_text(json.dumps(case, indent = 2) + '\n')
        (output / 'identity_case.svg').write_text(svg)
    write_csv(output / 'new_lead_identities.csv', leads, list(leads[0]))
    pl.DataFrame(lead_features).write_parquet(output / 'new_lead_features.parquet')
    (output / 'audit.json').write_text(json.dumps(result['summary'], indent = 2) + '\n')
    final = {'input_hashes': hashes([*source_files, prior, features, *snapshot_paths]),
             'code_hashes': hashes([Path(__file__), HERE / 'labels.py', HERE / 'structure.py',
                                    HERE / 'ablations.py', HERE / 'structure_models.py']),
             'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
             'output_hashes': hashes(list(output.iterdir())), 'summary': result['summary'],
             'versions': {n: version(n) for n in ('rdkit', 'scikit-learn', 'polars', 'numpy')},
             'scope': 'Unapproved verification-release audit; identity holds override historical scenarios. No models fitted or labels approved.'}
    (output / 'manifest.json').write_text(json.dumps(final, indent = 2) + '\n')
    return final


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--release', type = Path, required = True)
    parser.add_argument('--prior-log', type = Path, required = True)
    parser.add_argument('--features', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    parser.add_argument('--snapshots', type = Path)
    args = parser.parse_args()
    print(json.dumps(run(args.release, args.prior_log, args.features, args.output, args.snapshots)['summary'], indent = 2))
