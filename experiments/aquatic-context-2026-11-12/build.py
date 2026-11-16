"""Provisional study-to-row pH sensitivity; never infer exposure duration from an abstract."""
import json,sys
from pathlib import Path
sys.path.insert(0,'analysis')
import polars as pl
from context_overlay import run
from weekly_report import verify_manifest
root=Path('experiments/aquatic-context-2026-11-12')
comparison=Path('analysis/outputs/ecotox-approved-comparison-2026-11-11-verified')
rows=pl.read_csv(comparison/'aquatic_observations.csv',infer_schema_length=None).to_dicts()
selected=[r for r in rows if str(r['reference_number'])=='80404']
assert len(selected)==8
path=root/'provisional_ph_decisions.json'
if path.exists():raise ValueError('Preserve the earlier proposal file')
decisions=[{'measurement_id':r['measurement_id'],'field':'initial_ph','original':r.get('initial_ph'),
 'proposed':7.45,'status':'provisional','review_level':'AI_experimental','source_id':'KAMAYA2005-ABSTRACT',
 'source_locator':'PubMed PMID15722097; author abstract; neutralized condition initial pH7.45+/-0.05',
 'rationale':'Study-level initial pH is provisionally associated with each of eight reference80404 rows. Original paper/table mapping and pH time course remain unverified. The abstract reports +/-0.05 without an uncertainty interpretation; retain this wording. No exposure duration or control response is inferred.',
 'reviewer':'Codex AI; user-authorized experimental proposal','review_date':'2026-11-12'} for r in selected]
path.write_text(json.dumps(decisions,indent=2)+'\n')
for mode in ['reviewed','experimental']:
 output=Path(f'analysis/outputs/aquatic-context-{mode}-2026-11-12')
 manifest=run(comparison,path,root/'sources',output,mode)
 verify_manifest(output/'manifest.json')
 print(mode,manifest['applied_field_decisions'],manifest['coverage'])
