"""Generate local researcher documents from the frozen review artifacts."""
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path.cwd()
SOURCE = BASE / 'analysis/outputs/chembl-review-2026-10-29-final'
OUT = BASE / 'analysis/outputs/chembl-researcher-handoff-2026-10-29'
GUIDE = BASE / 'analysis/docs/label_review_guide.md'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def md(value):
    return str(value or '').replace('|', r'\|').replace('\n', ' ')

def compound_url(identity):
    return f'https://www.ebi.ac.uk/chembl/explore/compound/{identity}'

def assay_url(identity):
    return f'https://www.ebi.ac.uk/chembl/explore/assay/{identity}'

def expression(row):
    if not row['standard_value']:
        return 'No numeric outcome' + (f"; {row['activity_comment']}" if row['activity_comment'] else '')
    return ' '.join(v for v in (row['standard_relation'], row['standard_value'], row['standard_units']) if v)

labels = read(SOURCE / 'label_review_template.csv')
candidates = {r['compound_id']:r for r in read(SOURCE / 'candidates.csv')}
activities = read(SOURCE / 'activity_review.csv')
by_id = defaultdict(list)
for row in activities:
    by_id[row['molecule_chembl_id']].append(row)
ids = [r['compound_id'] for r in labels]
assert len(ids) == len(set(ids)) == len(candidates) == 154
assert len(activities) == 157 and set(ids) == set(candidates) == set(by_id)
assert all(r['herbicidal_activity'] == r['natural_origin'] == 'unknown' for r in labels)
source_paths = [SOURCE / n for n in ['label_review_template.csv', 'candidates.csv', 'activity_review.csv', 'manifest.json']]
source_paths += sorted({Path(r['snapshot_path']) for r in activities})
source_hashes = {str(p.relative_to(BASE)):digest(p) for p in source_paths}
for row in activities:
    assert digest(Path(row['snapshot_path'])) == row['snapshot_sha256']
if OUT.exists():
    raise FileExistsError(f'Preserve the existing researcher pack: {OUT}')
OUT.mkdir(parents=True)
shutil.copyfile(SOURCE / 'label_review_template.csv', OUT / 'reviewed_labels.csv')

index = []
log = []
assays = {r['assay_chembl_id']:r for r in activities}
lines = ['# Compound evidence packets — 2026-10-29', '',
    'Start with the [research guide](../../docs/label_review_guide.md). This packet covers every ID in the frozen worksheet.', '',
    '**All working labels remain unknown.** These are cached source observations, not verified biological conclusions. Primary publications and identity mappings still require review.', '',
    'Sources: ChEMBL_37; 154 molecule IDs, 157 observations, 14 assays/publications. The working label CSV and evidence log are separate files in this directory.', '',
    '## Navigation', '', '| Worksheet row | Compound | Observations |', '|---|---|---:|']
for number, identity in enumerate(ids, start=2):
    rows = sorted(by_id[identity], key=lambda r:int(r['activity_id']))
    names = sorted({json.loads(r['raw_activity_json']).get('molecule_pref_name') for r in rows
                    if json.loads(r['raw_activity_json']).get('molecule_pref_name')})
    index.append({'worksheet_row':number, 'compound_id':identity, 'molecule_url':compound_url(identity),
                  'cached_name':'; '.join(names), 'canonical_smiles':candidates[identity]['canonical_smiles'],
                  'activity_count':len(rows), 'activity_ids':'; '.join(r['activity_id'] for r in rows),
                  'assay_ids':'; '.join(sorted({r['assay_chembl_id'] for r in rows})),
                  'doi_urls':'; '.join(sorted({'https://doi.org/'+r['doi'] for r in rows if r['doi']})),
                  'source_outcomes':'; '.join(f"{r['activity_id']}: {expression(r)}" for r in rows),
                  'multiple_observations':str(len(rows)>1).lower(),
                  'has_missing_numeric_outcome':str(any(not r['standard_value'] for r in rows)).lower(),
                  'has_nonpercent_numeric_outcome':str(any(r['standard_value'] and r['standard_units']!='%' for r in rows)).lower(),
                  'packet_section':f'compound_evidence_packets.md#{identity.lower()}'})
    lines.append(f'| {number} | [{identity}](#{identity.lower()}) | {len(rows)} |')
    for r in rows:
        raw = json.loads(r['raw_activity_json'])
        log.append({'compound_id':identity, 'activity_id':r['activity_id'],
            'assay_chembl_id':r['assay_chembl_id'], 'document_chembl_id':r['document_chembl_id'],
            'molecule_url':compound_url(identity), 'assay_url':assay_url(r['assay_chembl_id']),
            'doi_url':'https://doi.org/'+r['doi'] if r['doi'] else '',
            'source_compound_name':raw.get('molecule_pref_name') or '',
            'canonical_smiles':r['canonical_smiles'], 'assay_description':r['assay_description'],
            'standard_type':r['standard_type'], 'standard_relation':r['standard_relation'],
            'standard_value':r['standard_value'], 'standard_units':r['standard_units'],
            'source_comment':r['activity_comment'], 'source_snapshot_sha256':r['snapshot_sha256'],
            'review_status':'unreviewed',
            **dict.fromkeys(['reviewer','review_date','identity_verified','primary_source_access',
                'primary_source_location','verified_species_stage','verified_application_and_units',
                'verified_timing_duration','verified_controls_replication','eligible_under_policy',
                'activity_policy','proposed_activity_label','origin_evidence_reference','origin_policy',
                'proposed_origin_label','decision_rationale','corrections_conflicts_next_steps'], '')})
lines += ['', '## Source assay contexts', '',
    'The descriptions below are preserved as cached, including unusual units. They have not been corrected against the publications. Open the DOI, methods and supplementary information.', '',
    '| Assay | Cached context | Source publication |', '|---|---|---|']
for identity, row in sorted(assays.items()):
    lines.append(f"| [{identity}]({assay_url(identity)}) | {md(row['assay_description'])} | [{row['doi']}](https://doi.org/{row['doi']}) |")
for identity in ids:
    rows = sorted(by_id[identity], key=lambda r:int(r['activity_id']))
    entry = next(r for r in index if r['compound_id']==identity)
    lines += ['', f'## {identity}', '', f"Worksheet row: **{entry['worksheet_row']}**. [ChEMBL molecule]({compound_url(identity)}).",
        f"Cached preferred name(s): {md(entry['cached_name']) or 'Not supplied'} (a lookup aid; verify the exact structure).", '',
        'Source canonical SMILES:', '', '```text', candidates[identity]['canonical_smiles'] or '(missing)', '```', '',
        '| Activity ID | Assay | Source endpoint | Recorded outcome | Primary source | Frozen bundle |',
        '|---|---|---|---|---|---|']
    for r in rows:
        raw_link = f"../chembl-2026-10-28/raw/chembl/{r['assay_chembl_id']}.json"
        lines.append(f"| {r['activity_id']} | [{r['assay_chembl_id']}]({assay_url(r['assay_chembl_id'])}) | {md(r['standard_type'])} | {md(expression(r))} | [{r['doi']}](https://doi.org/{r['doi']}) | [JSON]({raw_link}) |")
    concerns = ['Confirm source compound number/structure, methods, policy eligibility and natural occurrence independently.']
    if len(rows)>1: concerns.append('Multiple observations: preserve each study and resolve under one explicit activity policy; do not choose a universal label from the maximum response.')
    if any(not r['standard_value'] for r in rows): concerns.append('Missing numeric outcome: do not turn this into an inactive label.')
    if any(r['standard_relation'] not in ('=','') for r in rows): concerns.append('Inequality qualifier: its entire possible range must satisfy a policy threshold before a known label is supported.')
    if any(r['standard_value'] and r['standard_units']!='%' for r in rows): concerns.append('Non-percent measurement: review the endpoint and do not pool it with percent growth inhibition.')
    lines += ['', 'Review focus: ' + ' '.join(concerns), '',
              'Record decisions and references in `evidence_log.csv`; update only the matching row of `reviewed_labels.csv` after applying an agreed policy.']
write('compound_index.csv', index, list(index[0]))
write('evidence_log.csv', log, list(log[0]))
(OUT/'compound_evidence_packets.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
(OUT/'policy_draft.md').write_text('''# Activity and origin policy draft

Status: **UNAPPROVED / NOT YET DEFINED**. No known labels are authorized by this draft.
Complete this with the research lead before assigning policy-specific activity labels.

## Activity policy

- Policy ID and version:
- Written by / scientific reviewer / date / acceptance status:
- Intended biological claim and limits:
- Eligible assay IDs and publications (with reasons):
- Species and life stages:
- Endpoints and response interpretation:
- Application mode, pre/post-emergence timing and formulation:
- Eligible doses/concentrations, units and active-ingredient basis:
- Exposure duration and measurement time:
- Controls, replication and quality requirements:
- Active threshold and strict/inclusive boundary:
- Inactive/low-response threshold and strict/inclusive boundary:
- Intermediate/gray-zone rule:
- Inequality, interval, text-only and missing-value rules:
- Multiple-dose/replicate/publication conflict rule:
- Source identity/salt/stereochemistry and exclusion rules:
- Cross-assay pooling justification and exclusions:
- Independent publication/scaffold validation reservation:
- Limitations and further data needed:

## Natural-origin review definition

- Origin-policy name/version (tracked here and in the log, not a new label CSV column):
- What a natural label asserts and required affirmative occurrence evidence:
- What a synthetic label asserts and required affirmative provenance evidence:
- Exact-structure and stereochemistry requirements:
- Treatment of lab-synthesized naturally occurring compounds:
- Unresolved/conflicting occurrence records and search-coverage documentation:
- Reviewer/date/status:

Unknown is the outcome when the evidence or scope does not justify a known label.
Absence of an occurrence record does not establish synthetic origin.
''', encoding='utf-8')
(OUT/'README.md').write_text('''# Researcher handoff — 2026-10-29

Read the [comprehensive context and review guide](../../docs/label_review_guide.md) first.
Then open [the compound packets](compound_evidence_packets.md) or `compound_index.csv`.
Every one of the 154 worksheet IDs is included; 157 source observations are retained.

Edit `reviewed_labels.csv` as your working copy. It starts byte-identical to the frozen
unknown-label template. Record observation-level source checking and decisions in
`evidence_log.csv`; agree the written rules in `policy_draft.md`. Preserve source fields
and put proposed corrections in the review columns. Add log rows for newly found
assays or natural-occurrence evidence. No labels have been researched or assigned by
this handoff, and no primary-paper conclusion has been verified by its generation.

Keep the original review products and raw snapshots unchanged. The handoff manifest
records their hashes and hashes the initial supporting files. After manual annotation,
the initial handoff hashes will no longer describe the edited working files; save a
separate dated review release with reviewer/policy provenance rather than overwriting
the baseline manifest or claiming that the edited files match it.

This local pack and source data are ignored by Git. A complete researcher transfer
needs the guide, pack, frozen review files and raw bundles in the same relative layout.
''', encoding='utf-8')
manifest = {'prepared_date':'2026-10-29', 'source':'Frozen ChEMBL_37 review export',
    'compound_count':154, 'activity_count':157, 'assay_count':len(assays),
    'source_hashes':source_hashes, 'guide_sha256':digest(GUIDE),
    'generator_sha256':digest(Path(__file__)),
    'output_hashes':{p.name:digest(p) for p in sorted(OUT.iterdir())},
    'scope':'Researcher context only; all labels unknown; all decisions unreviewed. No source worksheet or source evidence modified.'}
(OUT/'handoff_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n', encoding='utf-8')
for name, expected in source_hashes.items():assert digest(BASE/name)==expected, name
assert digest(OUT/'reviewed_labels.csv')==digest(SOURCE/'label_review_template.csv')
print('Created',OUT)
print('154 compound packets/index rows; 157 review-log observations; working labels unchanged.')
