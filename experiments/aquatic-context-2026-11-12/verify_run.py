"""Check real-data overlay invariants against frozen comparison bytes."""
import sys,json
from pathlib import Path
sys.path.insert(0,'analysis')
import polars as pl
from weekly_report import verify_manifest
root=Path('experiments/aquatic-context-2026-11-12')
base=Path('analysis/outputs/ecotox-approved-comparison-2026-11-11-verified')
original=pl.read_csv(base/'aquatic_observations.csv',infer_schema_length=None).to_dicts()
by_id={r['measurement_id']:r for r in original}
assert len(by_id)==41
for mode in ['reviewed','experimental']:
 out=Path(f'analysis/outputs/aquatic-context-{mode}-2026-11-12')
 manifest=verify_manifest(out/'manifest.json')
 assert (out/'original_aquatic_observations.csv').read_bytes()==(base/'aquatic_observations.csv').read_bytes()
 rows=pl.read_csv(out/'source_adjudicated_observations.csv',infer_schema_length=None).to_dicts()
 assert {r['measurement_id'] for r in rows}==set(by_id)
 for row in rows:
  assert all(row[key]==value for key,value in by_id[row['measurement_id']].items()),row['measurement_id']
 if mode=='experimental':
  enriched=[r for r in rows if r.get('initial_ph') is not None]
  assert len(enriched)==8 and all(str(r['reference_number'])=='80404' and r['initial_ph']==7.45 for r in enriched)
 else:assert all(r.get('initial_ph') is None for r in rows)
 assert manifest['new_rat_admissions']==0
 print(mode,'all41 original row fields unchanged; hash verification passes')
verify_manifest(base/'manifest.json')
(root/'verification.json').write_text(json.dumps({'rows_compared':41,'original_fields_unchanged_in_both_modes':True,'experimental_ph_rows':8,'new_rat_admissions':0,'frozen_comparison_manifest_verified':True,'date':'2026-11-12'},indent=2)+'\n')
