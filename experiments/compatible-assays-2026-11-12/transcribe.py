"""Full fixed-table transcription; means only, never per-seed pseudo-replication."""
import csv,hashlib,json,re
from pathlib import Path
root=Path(__file__).parent
out=root/'transcription-v1'
if out.exists():raise ValueError('Use fresh output')
out.mkdir()
tables=json.loads((root/'sources/flavonoids2012.tables.json').read_text())
rows=[]
for ti,endpoint,unit in [(0,'germinated_seed_count','seeds'),(1,'radicle_length','cm')]:
 table=tables[ti]
 assert len(table)==33 and len(table[5])==7 and table[5][0]=='Control'
 for ri,row in enumerate(table[6:],1):
  assert len(row)==7
  for col in range(1,7):
   raw=row[col];m=re.fullmatch(r'(\d+(?:\.\d+)?) ± (\d+(?:\.\d+)?)(?: (\*+))?',raw)
   assert m,raw
   cm=re.fullmatch(r'(\d+(?:\.\d+)?) ± (\d+(?:\.\d+)?)',table[5][col]);assert cm
   mean,sd=float(m[1]),float(m[2]);control,controlsd=float(cm[1]),float(cm[2])
   rows.append(dict(observation_id=f'FLAV2012:T{ti+1}:R{ri}:C{col}',compound_id=f'FLAV2012:{ri:02}',source_name=row[0],source_doi='10.3390/ijms13055406',source_locator=f'Table {ti+1}; compound row {ri}; column {col}; methods3.2/3.3/3.5',species='Raphanus sativus' if col<=3 else 'Lepidium sativum',endpoint=endpoint,concentration_uM=[1,10,100][(col-1)%3],observation_hours=120,mean=mean,sd=sd,unit=unit,control_mean=control,control_sd=controlsd,control_raw=table[5][col],raw=raw,reported_significance=m[3] or '',derived_inhibition_percent=100*(1-mean/control),n_pet_dishes=3,seeds_per_dish=10,vehicle='water or water:acetone99.5:0.5; compound-specific vehicle not specified',review_status='AI experimental; not independent review',natural_origin='unknown',limits='Ratio of reported means; no derived SE/CI or significance; SD not SE; negative inhibition retained as stimulation; table rounding retained'))
assert len(rows)==324
with (out/'observations.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
policies=[];labels=[]
for species in ['Raphanus sativus','Lepidium sativum']:
 for endpoint in ['germinated_seed_count','radicle_length']:
  for dose in [1,10,100]:
   key=f'EXPERIMENT-FLAV2012-{species.split()[0].upper()}-{endpoint.upper()}-{dose}UM-120H-v1'
   subset=[r for r in rows if r['species']==species and r['endpoint']==endpoint and r['concentration_uM']==dose]
   assert len(subset)==27
   outcomes=[]
   for r in subset:
    value=r['derived_inhibition_percent'];label='active' if value>=50 else 'inactive' if value<=20 else 'unknown'
    outcomes.append(label)
    labels.append(dict(compound_id=r['compound_id'],policy=key,activity=label,inhibition_percent=value,observation_id=r['observation_id']))
   policies.append(dict(policy=key,species=species,endpoint=endpoint,dose_uM=dose,hours=120,active=outcomes.count('active'),low_inhibition=outcomes.count('inactive'),intermediate=outcomes.count('unknown'),thresholds='active >=50% mean inhibition; low inhibition <=20% including stimulation; intermediate unknown',interpretation='AI experimental analyst-defined thresholds on rounded group means; low inhibition is not general biological inactivity or lack of herbicidal activity',threshold_tuning=False))
(out/'policies.json').write_text(json.dumps(policies,indent=2)+'\n')
with (out/'labels_by_assay.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(labels[0]));w.writeheader();w.writerows(labels)
source_files=[root/'sources/flavonoids2012.html',root/'sources/flavonoids2012.tables.json',Path(__file__)]
(out/'manifest.json').write_text(json.dumps(dict(source_hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},output_hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},observations=324,unique_compounds=27,models_fitted=0,frozen_labels_changed=0),indent=2)+'\n')
print(json.dumps(policies,indent=2))
