"""Independent result/basis/decision checks; the PDF extraction remains AI-reviewed."""
import csv,hashlib,json,math
from pathlib import Path
from statistics import median
root=Path(__file__).parent
read=lambda p:list(csv.DictReader(p.open()))
cur=root/'curation-v1';sens=root/'sensitivity-v1'
table=read(cur/'table1.csv');facts=read(cur/'rat_eligibility.csv');projection=read(cur/'native_duration_projection.csv');pairs=read(cur/'duplicate_decisions.csv')
assert len(table)==14 and sum(bool(r['material_ld50_mg_kg']) for r in table)==13
unknown=next(r for r in table if r['material']=='Isooctyl ester' and r['sex']=='female')
assert unknown['material_raw']=='>720–<864' and not unknown['material_ld50_mg_kg'] and not unknown['reported_acid_equivalent_mg_kg']
for r in table:
 if r['material_ld50_mg_kg']:
  assert float(r['material_95cl_lower'])<float(r['material_ld50_mg_kg'])<float(r['material_95cl_upper'])
  ratio=float(r['molecular_weight_ratio_percent'] or 100)/100
  expected=float(r['material_ld50_mg_kg'])*float(r['active_ingredient_percent'])/100*ratio
  # Source rounded molecular weights/purity can differ slightly; retain paper values.
  difference=abs(expected-float(r['reported_acid_equivalent_mg_kg']))
  flagged=(r['material'],r['sex']) in {('Butoxyethanol ester','female'),('Butyl ester','female')}
  assert (difference>1)==flagged
assert {r['sex'] for r in facts}=={'male','female'}
for r in facts:
 expected=(607,639,555,736) if r['sex']=='male' else (726,764,663,879)
 assert tuple(float(r[k]) for k in ['reported_acid_equivalent_mg_kg','material_ld50_mg_kg','material_95cl_lower','material_95cl_upper'])==expected
 assert r['strict_gavage_capsule_policy']=='unresolved_technique_not_named'
 assert r['observation_hours']=='336' and r['review_level']=='AI_experimental'
for r in projection:
 assert float(r['normalized_observation_hours'])==336 and r['native_observation_unit']=='wk'
 assert r['native_exposure_type']=='DT' and not r['normalized_unit'] and not r['normalized_dose']
full=read(Path('analysis/outputs/rat-source-reconciliation-2026-11-12/study_overlap_review.csv'))
assert len(full)==18992 and len(pairs)==4
byid={r['pair_id']:r for r in full}
for p in pairs:
 assert byid[p['pair_id']]['decision']=='different_observation'
 assert 'AI' in byid[p['pair_id']]['reviewer'] and not byid[p['pair_id']]['retain_id']
assert sum(r['decision']=='different_observation' for r in full)==4
original=read(Path('analysis/outputs/weekly-toxicity-2026-11-10/evidence.csv'))
assert read(sens/'retained_censored_observations.csv')==[r for r in original if r['status']=='censored']
summary=read(sens/'scenario_summary.csv')
expected={'historical_exact':375,'experimental_record_pool_mixed_basis':607,'experimental_primary_study_first_mixed_basis':520.75}
for r in summary:
 assert math.isclose(float(r['d24_median']),expected[r['scenario']])
 assert float(r['lower_tertile'])==1080 and float(r['upper_tertile'])==3400
 assert r['new_bin_changes']=='0' and r['fixed_bin_changes']=='0' and r['compounds']=='34' and r['censored_baseline_unchanged']=='25'
assert median([607,726])==666.5 and median([375,607,726])==607 and median([375,666.5])==520.75
strata=read(sens/'primary_basis_strata.csv')
for r in strata:
 if r['dose_basis']=='reported_acid_equivalent':assert not r['material_95cl_lower'] and not r['material_95cl_upper']
checked=0
for path in [cur/'manifest.json',sens/'manifest.json',root/'conversion-audit-v1/manifest.json',Path('analysis/outputs/rat-source-reconciliation-2026-11-12/manifest.json')]:
 m=json.loads(path.read_text())
 for section in ['input_hashes','output_hashes','code_hashes','lock_hashes']:
  for name,digest in m.get(section,{}).items():
   assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,(path,name)
   checked+=1
result=dict(source_material_sex_cells=14,uncensored_material_estimates=13,displayed_conversion_discrepancies_preserved=2,source_cases_checked=2,adopted_pair_decisions=4,rat_baseline_admissions=0,changed_native_fields=0,baseline_censored_preserved=25,arithmetic_scenarios_checked=3,hashes_checked=checked,independent_scientific_review=False)
(root/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
