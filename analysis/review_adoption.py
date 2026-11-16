"""Adopt explicit human review into fresh policy-specific labels and audit records."""
import argparse
import csv
import json
import posixpath
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

import polars as pl

from labels import LABEL_FIELDS, attach_labels
from screen import HERE, hashes, write_csv
from structure import structure_features
from structure_models import REPRESENTATIONS, evaluate
from weekly_report import verify_manifest

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
K1998 = 'HUMAN-K1998-TWO-SPECIES-VERY-ACTIVE-1MM-v1'
CONSISTENT = 'PAPER_SUBSTITUENT_AND_SMILES_CONSISTENT_NOT_FINAL_STRUCTURE_ATTESTATION'
LEGACY_CONTEXT = {
    'HE2011': 'Amaranthus retroflexus, 2–3-leaf postemergence foliar spray; 1500 g active ingredient/ha; 20-day greenhouse fresh-weight response; three randomized replicates; A=90–100 and B=75–89 active; D<=50 bounded low response; C=50–74 unknown. Acetone/Tween vehicle, 1000 L/ha; grade edges are not exact values.',
    'LI2006': 'Amaranthus retroflexus, two-leaf postemergence foliar spray; 150 g active ingredient/ha; day-15 visual injury; author >80 band active, <50 band bounded low response; intermediate unknown. Untreated and DMF controls; source band, not exact effect.',
    'OKAMOTO': 'Amaranthus lividus, pre-emergence upland soil pot; 10 g active ingredient/are; two-week greenhouse visual ordinal 0–5; grades 4/5 active, 0/1 bounded low response, 2/3 unknown. Replication unreported in inspected source; not measured percentages.'
}



def read_csv(path):
    with Path(path).open(encoding = 'utf-8-sig', newline = '') as handle:
        return list(csv.DictReader(handle))


def workbook_tables(path):
    """Read literal XLSX source cells without executing formulas or editing the workbook."""
    with zipfile.ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist()) > 50_000_000:
            raise ValueError('Workbook exceeds bounded uncompressed size')
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared = [''.join(t.text or '' for t in item.iter('{'+NS['m']+'}t'))
                      for item in root.findall('m:si', NS)]
        rels = {r.attrib['Id']: r.attrib['Target'] for r in
                ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
        sheets = ET.fromstring(archive.read('xl/workbook.xml')).findall('m:sheets/m:sheet', NS)
        result = {}
        for sheet in sheets:
            rid = sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            target = rels[rid]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            if not member.startswith('xl/') or '..' in member.split('/'):
                raise ValueError('Invalid worksheet relationship')
            rows = []
            for row in ET.fromstring(archive.read(member)).findall('m:sheetData/m:row', NS):
                values = {}
                for cell in row.findall('m:c', NS):
                    if cell.find('m:f', NS) is not None:
                        raise ValueError('Review workbook must contain literal decisions, not formulas')
                    column = re.sub(r'\d+', '', cell.attrib['r'])
                    value = cell.find('m:v', NS)
                    text = value.text or '' if value is not None else ''
                    kind = cell.attrib.get('t')
                    if kind == 's':
                        text = shared[int(text)]
                    elif kind == 'inlineStr':
                        text = ''.join(t.text or '' for t in cell.findall('.//m:t', NS))
                    if kind == 'e':
                        raise ValueError('Workbook contains an Excel error')
                    values[column] = text
                if any(values.values()):
                    rows.append((row.attrib['r'], values))
            if not rows:
                result[sheet.attrib['name']] = []
                continue
            header = rows[0][1]
            if len(set(header.values())) != len(header) or any(not v for v in header.values()):
                raise ValueError('Unique nonempty workbook headers required')
            result[sheet.attrib['name']] = [
                {**{name: values.get(col, '') for col, name in header.items()},
                 '_xlsx_row': number} for number, values in rows[1:]]
        return result


def blank_label(cid):
    return {'compound_id': cid, **{k: '' for k in LABEL_FIELDS-{'compound_id'}},
            'natural_origin': 'unknown', 'herbicidal_activity': 'unknown'}


def approved_policy(original):
    if original == 'PROPOSED-K1998-LETTUCE-1MM-6D-v1':
        return K1998
    if not original.startswith('PROPOSED-'):
        raise ValueError('Expected versioned source policy')
    return original.replace('PROPOSED-', 'HUMAN-', 1)


def workbook_decisions(tables, original, packets, approval):
    reviewed = tables['Reviewed Worksheet']
    key = lambda r: (r['compound_id'], r['axis'], r['proposed_policy'])
    if Counter(map(key, reviewed)) != Counter(map(key, original)) or any(
            n != 1 for n in Counter(map(key, reviewed)).values()):
        raise ValueError('Workbook must cover each original compound-axis-policy exactly once')
    by_id = {r['compound_id']: r for r in packets}
    previous = {key(r): r for r in original}
    labels, ledger = {}, []
    for row in reviewed:
        cid = row['compound_id']
        if row['name'] != by_id[cid]['name']:
            raise ValueError('Workbook compound name/ID disagreement')
        if row['approval_state'] not in {'approved', 'unreviewed', 'rejected'}:
            raise ValueError('Unknown approval state')
        decision = row['proposed_decision']
        if decision not in ({'natural', 'synthetic', 'unknown'} if row['axis'] == 'origin'
                            else {'active', 'low_response', 'inactive', 'unknown'}):
            raise ValueError('Invalid reviewed decision')
        accept = row['approval_state'] == 'approved' and decision != 'unknown'
        if accept and (row['identity_status'] != 'source_structure_checked_matches' or
                       not all(row.get(k) for k in ('reviewer', 'review_date', 'source_locator',
                                                    'scientific_approval_reference'))):
            raise ValueError('Approved decisions require checked identity and complete review provenance')
        if row.get('review_date'):
            date.fromisoformat(row['review_date'])
        policy = approved_policy(row['proposed_policy']) if row['axis'] == 'activity' else 'HUMAN-EXACT-NATURAL-OCCURRENCE-v1'
        if policy not in labels:
            labels[policy] = {c: blank_label(c) for c in by_id}
        if accept:
            field = 'natural_origin' if row['axis'] == 'origin' else 'herbicidal_activity'
            reference_field = 'origin_reference' if row['axis'] == 'origin' else 'activity_reference'
            label = labels[policy][cid]
            label[field] = 'inactive' if decision == 'low_response' else decision
            label[reference_field] = row['scientific_approval_reference'] + '; human adoption: ' + approval['approval_id']
            if row['axis'] == 'activity':
                label['activity_policy'] = policy
                label['activity_context'] = row['rationale']
        ledger.append({**row, 'prior_proposed_decision': previous[key(row)]['proposed_decision'], 'adopted_policy': policy, 'adopted_decision': decision if accept else 'unknown',
                       'adoption_status': 'accepted' if accept else 'unresolved_or_rejected',
                       'approval_basis': approval['approval_id'],
                       'approval_scope': 'Human session adoption supersedes historical AI-only signoff wording; evidence caveats preserved.'})
    origin = labels.pop('HUMAN-EXACT-NATURAL-OCCURRENCE-v1')
    for batch in labels.values():
        for cid, label in batch.items():
            label.update({k: origin[cid][k] for k in ('natural_origin', 'origin_reference')})
    return {k: list(v.values()) for k, v in labels.items()}, list(origin.values()), ledger


def legacy_decisions(release, audit, features, approval):
    """Adopt supported historical proposals under the user's asserted human review.

    Explicit identity conflicts, unreadable source assignments, unresolved stereo,
    unassessed outcomes and gray response bands remain unresolved.
    """
    conditional = read_csv(release / 'conditional_assay_screen_NOT_FOR_TRAINING.csv')
    effective = {r['compound_id']: r for r in read_csv(audit / 'effective_conditional_screen.csv')}
    crosswalk = {r['compound_id']: r for r in read_csv(release / 'li_2006_24_compound_source_crosswalk.csv')}
    holds = {r['compound_id'] for r in read_csv(audit / 'identity_holds.csv')}
    origins = read_csv(release / 'PROPOSED_ORIGIN_FULL_STRUCTURE_MATCHES_NOT_FOR_TRAINING.csv')
    origin = {cid: blank_label(cid) for cid in features}
    for row in origins:
        if row['proposed_origin'] == 'natural' and row['external_stereo_structure_match'] == 'exact':
            origin[row['compound_id']].update(natural_origin = 'natural',
                origin_reference = row['independent_origin_evidence'] + '; human adoption: ' + approval['approval_id'])
    batches, ledger = {}, []
    for row in conditional:
        cid, source_policy = row['compound_id'], row['scenario_policy_UNAPPROVED']
        decision = effective[cid]['effective_conditional_NOT_LABEL']
        explicit_hold = cid in holds or (cid in crosswalk and crosswalk[cid]['crosswalk_status'] != CONSISTENT)
        if not source_policy:
            continue
        policy = approved_policy(source_policy)
        if policy not in batches:
            batches[policy] = {c: dict(v) for c, v in origin.items()}
        accept = decision in {'active', 'inactive'} and not explicit_hold
        if accept:
            batches[policy][cid].update(herbicidal_activity = decision,
                activity_reference = row['source_doi'] + '; assay=' + row['assay_id'] + '; human adoption: ' + approval['approval_id'],
                activity_context = next(v for k, v in LEGACY_CONTEXT.items() if k in policy) + '; ' + row['interpretation'] + '; original outcomes=' + row['original_frozen_outcomes'] + '; bounded policy=' + policy,
                activity_policy = policy)
        ledger.append({'compound_id': cid, 'original_policy': source_policy, 'adopted_policy': policy,
                       'adopted_decision': decision if accept else 'unknown',
                       'status': 'accepted_user_asserted_source_review' if accept else
                                 'explicit_identity_gap' if explicit_hold else 'unresolved_response',
                       'source_reference': row['source_doi'], 'source_interpretation': row['interpretation'],
                       'original_structure_review_status': row['structure_to_source_verified'],
                       'approval_basis': approval['approval_id']})
    return {k: list(v.values()) for k, v in batches.items()}, list(origin.values()), origins, ledger


def run(workbook, review, release, audit, legacy_features, approval_path, output):
    workbook, review, release, audit, legacy_features, approval_path, output = [Path(p).resolve() for p in
        (workbook, review, release, audit, legacy_features, approval_path, output)]
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output)
                              for p in (workbook, review, release, audit, legacy_features, approval_path)):
        raise ValueError('Use a fresh output directory separate from inputs')
    verify_manifest(review / 'manifest.json')
    verify_manifest(audit / 'manifest.json')
    inputs = [workbook, approval_path, legacy_features, review / 'manifest.json', audit / 'manifest.json',
              *[release / n for n in ('conditional_assay_screen_NOT_FOR_TRAINING.csv',
                  'li_2006_24_compound_source_crosswalk.csv', 'PROPOSED_ORIGIN_FULL_STRUCTURE_MATCHES_NOT_FOR_TRAINING.csv')]]
    before = hashes(inputs)
    approval = json.loads(approval_path.read_text())
    if not all(approval.get(k) for k in ('approval_id', 'reviewer', 'review_date', 'statement')):
        raise ValueError('Explicit human adoption statement required')
    date.fromisoformat(approval['review_date'])
    tables = workbook_tables(workbook)
    packets = read_csv(review / 'compound_packets.csv')
    batches, origin, ledger = workbook_decisions(tables, read_csv(review / 'approval_worksheet.csv'), packets, approval)
    legacy_rows = pl.read_parquet(legacy_features).to_dicts()
    legacy_by_id = {r['compound_id']: r for r in legacy_rows}
    old_batches, old_origin, comparator_records, old_ledger = legacy_decisions(release, audit, legacy_by_id, approval)
    if set(batches) & set(old_batches):
        raise ValueError('Distinct source-policy datasets required')
    batches.update(old_batches)
    feature_rows = [{**structure_features(r['database_smiles']), 'compound_id': r['compound_id'],
                     'query': r['name']} for r in packets] + legacy_rows
    by_id = {r['compound_id']: r for r in feature_rows}
    if len(by_id) != len(feature_rows):
        raise ValueError('Duplicate compound IDs across source cohorts')
    if any(by_id[r['compound_id']]['structure_inchikey'] != r['database_inchikey'] for r in packets):
        raise ValueError('Reviewed database structure no longer matches')
    all_origin = origin + old_origin
    origin_by_id = {r['compound_id']: r for r in all_origin}
    support, labeled_features, activity_oof = [], [], []
    for policy, labels in sorted(batches.items()):
        attached = attach_labels([by_id[r['compound_id']] for r in labels], labels)
        for representation in REPRESENTATIONS:
            result = evaluate(attached, 'activity_target', representation)
            report = result['report']
            report.update(policy = policy, models_fitted = int(result['estimator'] is not None),
                positive_scaffolds = len({r['scaffold'] for r in result['training'] if r['activity_target'] == 1}),
                negative_scaffolds = len({r['scaffold'] for r in result['training'] if r['activity_target'] == 0}))
            support.append(report)
            activity_oof.extend({**r, 'policy': policy} for r in result['oof'])
        labeled_features.extend({**r, 'policy': policy} for r in attached if r['activity_target'] is not None)
    # This contrast is a cohort-membership target, not origin/activity truth.
    contrast = []
    for row in feature_rows:
        if origin_by_id[row['compound_id']]['natural_origin'] == 'natural':
            contrast.append({**row, 'provenance_comparator_target': 0,
                             'contrast_group': 'reviewed_natural_occurrence'})
    for record in comparator_records:
        if record['proposed_origin'] == 'synthetic_provenance_documented' and record['external_stereo_structure_match'] == 'exact':
            contrast.append({**by_id[record['compound_id']], 'provenance_comparator_target': 1,
                             'contrast_group': 'documented_commercial_herbicide_comparator'})
    canonical = {}
    for row in contrast:
        key = row['canonical_structure']
        if key in canonical:
            raise ValueError('Contrast groups require disjoint unique structures')
        canonical[key] = row
    output.parent.mkdir(parents = True, exist_ok = True)
    stage = Path(tempfile.mkdtemp(prefix = '.'+output.name+'-', dir = output.parent))
    try:
        for name, records in tables.items():
            write_csv(stage / (name.lower().replace(' ', '_')+'.csv'), records, list(records[0]))
        write_csv(stage / 'adoption_ledger.csv', ledger, list(ledger[0]))
        write_csv(stage / 'legacy_adoption_ledger.csv', old_ledger, list(old_ledger[0]))
        write_csv(stage / 'origin_labels.csv', all_origin, ['compound_id', *sorted(LABEL_FIELDS-{'compound_id'})])
        for policy, labels in batches.items():
            write_csv(stage / (policy+'.csv'), labels, ['compound_id', *sorted(LABEL_FIELDS-{'compound_id'})])
        pl.DataFrame(support).write_csv(stage / 'activity_models.csv')
        write_csv(stage / 'activity_out_of_fold.csv', activity_oof,
                  ['compound_id', 'target', 'representation', 'label', 'fold', 'scaffold',
                   'probability', 'baseline_prediction', 'policy'])
        definitions = {p: {'status': 'human_adopted_bounded_policy' if any(
            r['herbicidal_activity'] != 'unknown' for r in labels) else 'unresolved_no_labels_adopted',
            'context': next((v for k, v in LEGACY_CONTEXT.items() if k in p),
                            'Workbook study/treatment context; K1998 means authors’ two-species very-active category at 1 mM, lettuce day 6/millet day 4; no low-response rule.'),
            'approval_basis': approval['approval_id']} for p, labels in batches.items()}
        (stage / 'policies.json').write_text(json.dumps(definitions, indent = 2)+'\n')
        pl.DataFrame(contrast, infer_schema_length = None).write_parquet(stage / 'contrast_features.parquet')
        # Lists remain typed in parquet; CSV is a compact evidence/descriptor table.
        compact = [{k: v for k, v in r.items() if k != 'fingerprint'} for r in labeled_features]
        pl.DataFrame(compact, infer_schema_length = None).write_csv(stage / 'accepted_activity_features.csv')
        (stage / 'identity_holds.csv').write_bytes((audit / 'identity_holds.csv').read_bytes())
        (stage / 'approval_statement.json').write_bytes(approval_path.read_bytes())
        if hashes(inputs) != before:
            raise ValueError('Inputs changed during adoption')
        output_hashes = {str(output / p.name): value for p, value in
                         ((Path(k), v) for k, v in hashes(list(stage.iterdir())).items())}
        manifest = {'input_hashes': before, 'output_hashes': output_hashes,
                    'code_hashes': hashes([Path(__file__), HERE/'labels.py', HERE/'structure_models.py']),
                    'lock_hashes': hashes([HERE/'uv.lock', HERE/'pyproject.toml']),
                    'approval': approval, 'policies': sorted(batches),
                    'accepted_origin': sum(r['natural_origin'] != 'unknown' for r in all_origin),
                    'accepted_activity_per_policy': {p: dict(Counter(r['herbicidal_activity'] for r in rows))
                                                     for p, rows in batches.items()},
                    'activity_models_fitted': sum(r['models_fitted'] for r in support),
                    'contrast_counts': dict(Counter(r['contrast_group'] for r in contrast)),
                    'scope': 'Human adoption of supported proposals. Explicit gaps persist. Contrast predicts purposive group membership, not activity or natural occurrence.'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False)+'\n')
        if output.exists():
            raise ValueError('Output appeared before publication; refusing overwrite')
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('workbook', 'review', 'release', 'audit', 'legacy-features', 'approval', 'output'):
        parser.add_argument('--'+name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.workbook, args.review, args.release, args.audit,
                         args.legacy_features, args.approval, args.output), indent = 2))
