"""Independent checks of counts, raw-cell transcription, policies, structures and hashes."""
import csv,hashlib,json,math
from pathlib import Path
from rdkit import Chem
root=Path(__file__).parent
out=root/'analysis-v2'
obs=list(csv.DictReader((root/'transcription-v1/observations.csv').open()))
tables=json.loads((root/'sources/flavonoids2012.tables.json').read_text())
assert len(obs)==324 and len({r['observation_id'] for r in obs})==324 and len({r['compound_id'] for r in obs})==27
for r in obs:
 ti=0 if r['endpoint']=='germinated_seed_count' else 1
 ri=int(r['compound_id'].split(':')[1]);ci=[1,10,100].index(int(r['concentration_uM']))+1+(3 if r['species']=='Lepidium sativum' else 0)
 assert r['raw']==tables[ti][ri+5][ci]
 assert r['source_name']==tables[ti][ri+5][0]
 assert r['control_raw']==tables[ti][5][ci]
 assert math.isclose(float(r['derived_inhibition_percent']),100-100*float(r['mean'])/float(r['control_mean']),abs_tol=1e-10)
 assert r['unit']==('seeds' if ti==0 else 'cm')
 assert r['natural_origin']=='unknown' and r['observation_hours']=='120'
for p in json.loads((root/'transcription-v1/policies.json').read_text()):
 assert p['active']+p['low_inhibition']+p['intermediate']==27 and p['active']<=2
labels=list(csv.DictReader((root/'transcription-v1/labels_by_assay.csv').open()))
for r in labels:
 v=float(r['inhibition_percent']);assert r['activity']==('active' if v>=50 else 'inactive' if v<=20 else 'unknown')
compounds={r['compound_id']:r['smiles'] for r in csv.DictReader((out/'compounds.csv').open())}
def without_methyls(s):
 m=Chem.MolFromSmiles(s);remove=[]
 for a in m.GetAtoms():
  if a.GetAtomicNum()!=6 or a.GetDegree()!=1 or a.GetTotalNumHs()!=3:continue
  o=a.GetNeighbors()[0]
  if o.GetAtomicNum()==8 and o.GetDegree()==2 and any(x.GetIsAromatic() for x in o.GetNeighbors()):remove.append(a.GetIdx())
 m=Chem.RWMol(m)
 for i in sorted(remove,reverse=True):m.RemoveAtom(i)
 # Reparse after clearing stereochemistry: this checks constitutional O-demethylation only.
 m=m.GetMol();Chem.SanitizeMol(m);Chem.RemoveStereochemistry(m)
 return Chem.MolToSmiles(m)
pairs=list(csv.DictReader((out/'methylation_pairs.csv').open()))
assert len(pairs)==36
for r in pairs:
 assert without_methyls(compounds[r['parent_id']])==without_methyls(compounds[r['methylated_id']])
 assert math.isclose(float(r['difference_percentage_points']),float(r['methylated_inhibition_percent'])-float(r['parent_inhibition_percent']),abs_tol=1e-10)
for report in json.loads((out/'support.json').read_text()):
 assert report['active']==2 and report['inactive']==18 and report['active_scaffolds']==2 and report['inactive_scaffolds']==9 and report['folds']==0
checked=0
for manifest in [root/'transcription-v1/manifest.json',*out.rglob('manifest.json')]:
 data=json.loads(manifest.read_text())
 for section in ['input_hashes','output_hashes','source_hashes','code_hashes']:
  for name,digest in data.get(section,{}).items():
   path=Path(name)
   if not path.is_absolute():path=Path.cwd()/path
   assert path.is_file(),path
   assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,(manifest,path)
   checked+=1
report=dict(observations_checked=324,assay_policies=12,unique_compounds=27,name_hits=27,methylation_comparisons=36,constitutional_methylation_pairs=6,stereochemical_equivalence_asserted=False,hashes_checked=checked,models_fitted=0,scope='Internal consistency and constitutional identity checks; not independent scientific/source review')
(root/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
