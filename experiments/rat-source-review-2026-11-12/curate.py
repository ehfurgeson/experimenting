"""AI experimental transcription of visually inspected primary pages 424/426."""
import csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'analysis')
from expansion_toxicity import duplicate_exclusions,adopt_duplicate_decisions
from screen import write_csv,hashes
from agrotox.ecotox_selected import normalize
root=Path(__file__).parent
out=root/'curation-v1'
if out.exists():raise ValueError('Use fresh output')
source=root/'sources/gorzinski1987.pdf'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
assert digest=='8c9ca688757250abc954294545473c77e75044ba167e00f8e0cb263c384306c5'
ref=Path('notes/handoffs/research-2026-11-11/reference_inputs/toxicity')
native=json.loads((ref/'ecotox_native_context_excerpt.json').read_text())['records']
queue=json.loads((ref/'rat_priority_overlap_pairs.json').read_text())['records']
counterparts=json.loads((ref/'epa_rat_overlap_counterparts.json').read_text())['records']
# Transcribe all material/sex cells, preserving the noncalculable isooctyl female result.
data=[
 ('2,4-D acid',None,95.0,639,555,736,607,764,663,879,726,'Thompson and Weil (1952)'),
 ('Isooctyl ester',66.4,94.0,982,865,1114,612,None,None,None,None,'Thompson and Weil (1952)'),
 ('Dimethylamine salt',83.7,67.9,1090,959,1241,619,863,816,913,490,'Thompson and Weil (1952)'),
 ('Isobutyl ester',79.8,96.1,700,652,751,536,553,513,597,424,'Litchfield and Wilcoxon (1949)'),
 ('Sodium salt',94.9,90.8,876,671,1143,754,975,856,1111,840,'Litchfield and Wilcoxon (1949)'),
 ('Butoxyethanol ester',65.6,97.1,887,810,951,564,831,688,1002,565,'Litchfield and Wilcoxon (1949)'),
 ('Butyl ester',79.8,98.6,732,593,904,575,600,545,798,519,'Litchfield and Wilcoxon (1949)'),
]
rows=[]
for material,ratio,purity,male,ml,mh,ma,female,fl,fh,fa,method in data:
 for sex,value,low,high,ae in [('male',male,ml,mh,ma),('female',female,fl,fh,fa)]:
  rows.append(dict(paper_record_id=f'GORZ1987:T1:{material}:{sex}',material=material,sex=sex,material_ld50_mg_kg=value,material_95cl_lower=low,material_95cl_upper=high,material_qualifier='=' if value else 'not_calculable_reported_bounds',material_raw=str(value) if value else '>720–<864',reported_acid_equivalent_mg_kg=ae,molecular_weight_ratio_percent=ratio,active_ingredient_percent=purity,estimation_method=method,source_sha256=digest,source_locator=f'printed p426 Table1;{material};{sex};footnotes a-f',review_level='AI_experimental',limits='Material and acid-equivalent bases separate; CI is reported only for material tested; no derived ae CI; no new canonical identity for salts/esters'))
assert len(rows)==14
cases=[r for r in native if r['reference_number']=='93388'];assert len(cases)==2
facts=[];native_projection=[]
dictionaries_path=Path('analysis/outputs/ecotox-selected-approved-2026-11-11/dictionaries.json')
dictionaries=json.loads(dictionaries_path.read_text());assert dictionaries['duration_unit']['wk']
for r in cases:
 t=json.loads(r['test_json']);v=json.loads(r['result_json'])
 sex=t['organism_gender'].lower();cell=next(x for x in rows if x['material']=='2,4-D acid' and x['sex']==sex)
 assert float(v['conc1_mean'])==cell['reported_acid_equivalent_mg_kg'] and v['conc1_unit']=='ae mg/kg'
 assert t['test_purity_mean']=='95.0' and v['effect']=='MOR' and v['measurement']=='MORT' and v['endpoint']=='LD50'
 projection=normalize(r,dictionaries,compound_id='PUBCHEM:1486',identity_status='approved')[0]
 assert projection['duration_hours']==336 and projection['unit_standardized'] is None
 native_projection.append(dict(measurement_id=projection['measurement_id'],native_observation_value=v['obs_duration_mean'],native_observation_unit=v['obs_duration_unit'],normalized_observation_hours=projection['duration_hours'],native_exposure_type=t['exposure_type'],native_exposure_duration_value=t['exposure_duration_mean'],native_exposure_duration_unit=t['exposure_duration_unit'],normalized_native_exposure_hours=projection['exposure_hours'],source_primary_conflict='Dietary exposure/2wk not supported for Table1 single-dose oral LD50; retain native fields; no acute context inferred from conversion',raw_value=v['conc1_mean'],raw_unit=v['conc1_unit'],normalized_dose=projection['value'],normalized_unit=projection['unit_standardized']))
 facts.append(dict(measurement_id=projection['measurement_id'],source_result_id=r['source_result_id'],compound_id='PUBCHEM:1486',reference_number='93388',primary_doi='10.1016/0272-0590(87)90025-X',paper_record_id=cell['paper_record_id'],species='rattus norvegicus',strain='Fischer344',sex=sex,lifestage='young adult',endpoint='LD50',route='oral',administration='single_dose',administration_technique='not explicitly named in acute methods; do not import gavage wording from pharmacokinetic subsection',observation_hours=336,vehicle='corn oil',fasting_hours_approx=18,animals_per_sex_per_dose=5,tested_material='technical-grade2,4-D acid;95% active',material_ld50_mg_kg=cell['material_ld50_mg_kg'],material_95cl_lower=cell['material_95cl_lower'],material_95cl_upper=cell['material_95cl_upper'],reported_acid_equivalent_mg_kg=cell['reported_acid_equivalent_mg_kg'],qualifier='=',dose_denominator='kg body weight',source_sha256=digest,source_locator='printedp424 Acute(Single-Dose) Toxicological Studies;Single-dose oral LD50;printedp426 Table1 acid row/sex and footnotes b-d',status='provisional',review_level='AI_experimental',reviewer='Codex_AI_experimental',review_date='2026-11-12',strict_gavage_capsule_policy='unresolved_technique_not_named',experimental_single_dose_oral_policy='eligible_as_source_reported_acid_equivalent_only',native_conflict='Native DT/dietary and2wk exposure conflict with acute single-dose methods; original fields preserved',limits='No independent review; controls not specified for acute subsection; do not mix material/acid-equivalent doses or subchronic protocol'))
# Four pair decisions: chronic repeated-dose LOEL reports are not acute LD50 observations.
ids={r['measurement_id'] for r in facts};decisions=[];evidence=[]
for pair in queue:
 if pair['right_id'] not in ids:continue
 epa=next(r for r in counterparts if r['annotation_id']==pair['left_id'] or r['annotation_id']==pair['right_id'])
 raw=json.loads(epa['context_json'])
 assert raw['toxval_type']=='LOEL' and raw['study_duration_value']==91 and raw['value_numeric']==15
 decisions.append(dict(pair_id=pair['pair_id'],decision='different_observation',retain_id='',reviewer='Codex_AI_experimental',review_date='2026-11-12',decision_reference=f'AI experimental source adjudication;DOI10.1016/0272-0590(87)90025-X;PDFsha256={digest};printedpp424-426 acute vs13-weekdietary methods;Table1 LD50 vsEPA91day15mg/kg-dayLOEL;see companion evidence;not independent human review'))
 evidence.append(dict(pair_id=pair['pair_id'],ecotox_measurement_id=pair['right_id'],epa_annotation_id=epa['annotation_id'],ecotox_endpoint='LD50',ecotox_observation_hours=336,epa_endpoint=raw['toxval_type'],epa_duration_days=91,epa_dose_mg_kg_day=15,epa_effect=raw['toxicological_effect'],rationale='Different administration/endpoints: acute single-dose death estimate versus repeated dietary subchronic LOEL; equal DOI alone is not duplication',source_sha256=digest,review_level='AI_experimental'))
assert len(decisions)==4 and duplicate_exclusions(queue,decisions)==set()
adopted=adopt_duplicate_decisions(queue,decisions);assert sum(r['decision']=='different_observation' for r in adopted)==4
out.mkdir()
for name,items in [('table1',rows),('rat_eligibility',facts),('native_duration_projection',native_projection),('duplicate_decisions',decisions),('duplicate_evidence',evidence),('priority_queue_adopted',adopted)]:write_csv(out/f'{name}.csv',items,list(items[0]))
inputs=[Path(__file__),source,dictionaries_path,ref/'ecotox_native_context_excerpt.json',ref/'rat_priority_overlap_pairs.json',ref/'epa_rat_overlap_counterparts.json']
(out/'manifest.json').write_text(json.dumps(dict(input_hashes=hashes(inputs),output_hashes=hashes(list(out.iterdir())),code_hashes=hashes([Path('pipeline/src/agrotox/units.py'),Path('pipeline/src/agrotox/ecotox_selected.py'),Path('analysis/expansion_toxicity.py')]),source_review='AI_experimental; visually inspected PDF pp423-427; no independent reviewer',pending_rat_cases_reviewed=2,priority_pair_decisions=4,new_historical_admissions=0,native_fields_changed=0),indent=2)+'\n')
print('14 source material/sex cells;2 pending cases;4 different-observation decisions;0 historical admissions')
