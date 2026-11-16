"""Initialize editable human-review worksheets without assigning any known labels."""
import csv
import hashlib
import json
import shutil
from pathlib import Path

root = Path.cwd()
pack = root / 'analysis/outputs/manual-verification-2026-11-05'
assert not pack.exists(), 'Use a fresh working-pack path'
source = root / 'notes/compound_review_deeper_2026-10-29'
dietary = root / 'analysis/outputs/dietary-review-2026-11-04-final'
triage = root / 'analysis/outputs/dietary-triage-2026-11-04-final'
read = lambda p: list(csv.DictReader(p.open()))
log = read(source / 'evidence_log.csv')
labels = read(source / 'reviewed_labels.csv')
assert len(labels) == 154 and all(r['herbicidal_activity'] == r['natural_origin'] == 'unknown' for r in labels)
for name in ('assays', 'dietary', 'sources'):
    (pack / name).mkdir(parents=True)
copies = {
    source / 'reviewed_labels.csv': pack / 'assays/reviewed_labels.csv',
    source / 'evidence_log.csv': pack / 'assays/evidence_log_reference.csv',
    source / 'policy_draft.md': pack / 'assays/policy_working.md',
    source / 'study_source_index.csv': pack / 'assays/study_source_index_reference.csv',
    dietary / 'review.csv': pack / 'dietary/review.csv',
    triage / 'triage.csv': pack / 'dietary/triage_reference.csv',
}
for src, dst in copies.items():
    shutil.copyfile(src, dst)
    assert src.read_bytes() == dst.read_bytes()
fields = ['compound_id','activity_id','assay_id','source_doi','cached_name_NOT_VERIFIED',
          'frozen_smiles','frozen_relation','frozen_value','frozen_units','cached_assay_context',
          'source_compound_number','structure_page_or_SI','structure_match',
          'result_table_page','table_row','table_column','source_response_exact',
          'species_stage','application_rate_and_units','application_mode','duration',
          'controls','replication','conflicts_or_missing_details','saved_evidence_path',
          'proposed_decision','accepted_policy_id','human_reviewer','human_review_date',
          'scientific_approval_reference']
counts = {}
for name, aid in [('li2006', 'CHEMBL3066645'), ('he2011', 'CHEMBL3050362')]:
    rows = [r for r in log if r['assay_chembl_id'] == aid]
    counts[name] = len(rows)
    with (pack / f'assays/{name}_source_mapping.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                'compound_id':r['compound_id'], 'activity_id':r['activity_id'], 'assay_id':aid,
                'source_doi':r['doi_url'], 'cached_name_NOT_VERIFIED':r['source_compound_name'],
                'frozen_smiles':r['canonical_smiles'], 'frozen_relation':r['standard_relation'],
                'frozen_value':r['standard_value'], 'frozen_units':r['standard_units'],
                'cached_assay_context':r['assay_description'], 'structure_match':'unknown',
                'proposed_decision':'unknown'})
assert counts == {'li2006':24, 'he2011':58}
(pack / 'README.md').write_text('''# Editable manual verification pack

Initialized 2026-11-05. No scientific approval or known labels have been assigned.

Follow `analysis/docs/verification-checklist.md` from the repository root.

- `assays/li2006_source_mapping.csv`: 24 source-row/structure checks to complete.
- `assays/he2011_source_mapping.csv`: 58 source-row/structure checks to complete.
- `assays/reviewed_labels.csv`: exact seven-column working label copy; all 154 rows remain unknown.
- `assays/policy_working.md`: explicitly unapproved source-policy draft to discuss and version.
- `assays/*_reference.csv`: earlier AI-assisted source annotations, not human sign-off.
- `dietary/review.csv`: 40-row editable dietary review copy; no high-dose/plant labels accepted.
- `dietary/triage_reference.csv`: automated prioritization only; not a label file.
- `sources/`: save legally obtained papers/SI and annotated source excerpts here, with source citations.

Human fields in the source-mapping worksheets start blank. Do not mistake the
AI-assisted reviewer names in reference files for scientific acceptance.
Do not combine different activity policies in the seven-column label copy:
use it for one accepted policy at a time and save separately versioned files.

The initialization manifest records starting bytes. Editing these working copies
is expected; preserve dated copies of completed decisions instead of treating the
initial output hashes as ongoing proof that a working file must never change.
The notebook does not read these editable files as accepted evidence. Its frozen
source/result checks are independent of this working pack.
''')
shutil.copyfile(__file__, pack / 'prepare_pack.py')
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {'initialized_date':'2026-11-05', 'status':'editable_working_copies_not_approved',
            'source_hashes':{str(p):digest(p) for p in copies},
            'mapping_source_hashes':{str(source/'evidence_log.csv'):digest(source/'evidence_log.csv')},
            'initial_output_hashes':{str(p):digest(p) for p in sorted(pack.rglob('*')) if p.is_file()},
            'mapping_counts':counts, 'known_activity_labels':0, 'known_origin_labels':0,
            'scope':'Editable human-review preparation; no training or source modifications.'}
(pack / 'initialization_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(pack)
print(counts)
