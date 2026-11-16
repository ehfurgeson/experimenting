"""Deliberately relaxed record/study weighting sensitivities; never a baseline update."""
import csv,json,sys
from collections import defaultdict
from pathlib import Path
from statistics import median
import numpy as np
sys.path.insert(0,'analysis')
from screen import hashes,write_csv
from weekly_report import verify_manifest
root=Path(__file__).parent
out=root/'sensitivity-v1'
if out.exists():raise ValueError('Use fresh output')
baseline=Path('analysis/outputs/weekly-toxicity-2026-11-10')
verify_manifest(baseline/'manifest.json');verify_manifest(root/'curation-v1/manifest.json')
old=[r for r in csv.DictReader((baseline/'evidence.csv').open()) if r['status']=='exact']
bounds=[r for r in csv.DictReader((baseline/'evidence.csv').open()) if r['status']=='censored']
assert len(old)==43 and len(bounds)==25
facts=list(csv.DictReader((root/'curation-v1/rat_eligibility.csv').open()));assert len(facts)==2
byid=defaultdict(list)
for r in old:byid[r['compound_id']].append(float(r['value_mg_kg']))
original=list(csv.DictReader((baseline/'compounds.csv').open()))
meta={r['compound_id']:r for r in original}
assert len(original)==49 and len(byid)==34 and byid['PUBCHEM:1486']==[375.0]
assert all(r['compound_id']=='PUBCHEM:1486' and r['qualifier']=='=' and r['observation_hours']=='336' and r['status']=='provisional' and r['review_level']=='AI_experimental' for r in facts)
ae=[float(r['reported_acid_equivalent_mg_kg']) for r in facts]
material=[float(r['material_ld50_mg_kg']) for r in facts]
assert sorted(ae)==[607,726] and sorted(material)==[639,764]
scenarios=[('historical_exact',[],43,'Historical EPA retained evidence; own undocumented dose-basis/lineage limits'),('experimental_record_pool_mixed_basis',ae,45,'Intentionally relaxed pooling: original375basis unknown plus primary male607/female726acid-equivalent; source/sex weighting unresolved; not harmonized'),('experimental_primary_study_first_mixed_basis',[median(ae)],44,'Collapse two source sexes to one descriptive study median666.5 before pooling with375; demonstrates weighting assumption; still mixed basis; not harmonized')]
rows=[];summaries=[]
for scenario,added,recordn,limits in scenarios:
 medians=[];pending=[]
 for cid,values in sorted(byid.items()):
  vs=values+(added if cid=='PUBCHEM:1486' else [])
  val=median(vs);medians.append(val)
  pending.append(dict(scenario=scenario,compound_id=cid,group=meta[cid]['group'],input_exact_values_json=json.dumps(vs),descriptive_median_mg_kg=val,historical_median_mg_kg=float(meta[cid]['median_mg_kg']),historical_bin=meta[cid]['ld50_bin'],fixed_historical_bin='low' if val<=1080 else 'medium' if val<=3400 else 'high',limits=limits))
 cutoffs=[float(x) for x in np.quantile(medians,[1/3,2/3],method='linear')]
 for r in pending:r['new_scenario_bin']='low' if r['descriptive_median_mg_kg']<=cutoffs[0] else 'medium' if r['descriptive_median_mg_kg']<=cutoffs[1] else 'high'
 rows.extend(pending)
 summaries.append(dict(scenario=scenario,exact_input_rows_or_study_aggregates=recordn,compounds=len(pending),censored_baseline_unchanged=len(bounds),lower_tertile=cutoffs[0],upper_tertile=cutoffs[1],new_bin_changes=sum(r['new_scenario_bin']!=r['historical_bin'] for r in pending),fixed_bin_changes=sum(r['fixed_historical_bin']!=r['historical_bin'] for r in pending),d24_median=next(r['descriptive_median_mg_kg'] for r in pending if r['compound_id']=='PUBCHEM:1486'),limits=limits))
# Separate source-only strata do not merge tested material and active-acid-equivalent dose.
primary=[]
for r in facts:
 for basis,key in [('material_tested','material_ld50_mg_kg'),('reported_acid_equivalent','reported_acid_equivalent_mg_kg')]:
  primary.append(dict(compound_id=r['compound_id'],sex=r['sex'],dose_basis=basis,ld50_mg_kg=float(r[key]),material_95cl_lower=float(r['material_95cl_lower']) if basis=='material_tested' else None,material_95cl_upper=float(r['material_95cl_upper']) if basis=='material_tested' else None,qualifier=r['qualifier'],source_locator=r['source_locator'],source_sha256=r['source_sha256'],limits='Source-specific single-dose oral estimate;95%active technical material;no acid-equivalent CI derived;5rats/sex/dose not total;not independent experiments per estimate'))
out.mkdir()
write_csv(out/'retained_censored_observations.csv',bounds,list(bounds[0]))
write_csv(out/'primary_basis_strata.csv',primary,list(primary[0]));write_csv(out/'compound_sensitivities.csv',rows,list(rows[0]));write_csv(out/'scenario_summary.csv',summaries,list(summaries[0]))
inputs=[Path(__file__),baseline/'manifest.json',baseline/'evidence.csv',baseline/'compounds.csv',root/'curation-v1/manifest.json',root/'curation-v1/rat_eligibility.csv']
(out/'manifest.json').write_text(json.dumps(dict(input_hashes=hashes(inputs),output_hashes=hashes(list(out.iterdir())),baseline_modified=False,historical_new_admissions=0,new_harmonized_comparison_compounds=0,models_fitted=0,scope='Source-specific strata plus deliberately unharmonized experimental arithmetic sensitivities; primary review remains AI only',summaries=summaries),indent=2)+'\n')
print(json.dumps(summaries,indent=2))
