import csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'analysis')
import polars as pl
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from labels import attach_labels
from screen import prepare,read_records,write_csv,hashes,HERE
from publication_transfer import run
from verification_release import reject_held_activity
root=Path(__file__).parent
out=root/'external-inputs-v1'
if out.exists():raise ValueError('Use fresh output')
protocol=json.loads((root/'external_protocol.json').read_text())
oldfeatures=Path('analysis/outputs/experimental-heterogeneous-activity-2026-11-12/structural_features.parquet')
oldlineage=Path('experiments/bioherbicide-expansion-2026-11-12/pooled-v2-corrected-doi/pooled_lineage.csv')
old=read_records(oldfeatures);assert len(old)==73 and sum(r['activity_target'] for r in old)==41
labels=list(csv.DictReader((root/'analysis-v2/raphanus_labels.csv').open()))
reject_held_activity(labels,{'CHEMBL2253236','CHEMBL2253237','CHEMBL2253255'})
new=attach_labels(prepare(read_records(root/'analysis-v2/compounds.csv')),labels)
assert len(new)==27 and sum(r['activity_target']==1 for r in new)==2 and sum(r['activity_target']==0 for r in new)==18
assert not {r['canonical_structure'] for r in old}&{r['canonical_structure'] for r in new}
rows=old+new
parents={r['compound_id']:r['activity_policy'] for r in rows}
for r in rows:r['activity_policy']=protocol['policy']
# Select shared structural feature schema only; old and new chemistry computed by same code.
columns=list(old[0]);assert all(all(k in r for k in columns) for r in new)
rows=[{k:r[k] for k in columns} for r in rows]
lineage=read_records(oldlineage)+[dict(compound_id=r['compound_id'],publication='Flavonoids2012',parent_policy=parents[r['compound_id']],evidence_status='AI experimental; primary source mean responses; provisional name structure mapping') for r in new]
out.mkdir()
pl.DataFrame(rows,schema_overrides={'fingerprint':pl.List(pl.Int8)}).write_parquet(out/'features.parquet')
write_csv(out/'lineage.csv',lineage,['compound_id','parent_policy','publication','evidence_status'])
# Structural distance to old training cohort; radius2/2048 same as maintained models.
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
fps=[gen.GetFingerprint(Chem.MolFromSmiles(r['canonical_structure'])) for r in old]
nearest=[]
for r in new:
 fp=gen.GetFingerprint(Chem.MolFromSmiles(r['canonical_structure']));similarity=DataStructs.BulkTanimotoSimilarity(fp,fps);i=max(range(len(old)),key=similarity.__getitem__)
 nearest.append(dict(compound_id=r['compound_id'],activity_target=r['activity_target'],nearest_training_id=old[i]['compound_id'],maximum_tanimoto=similarity[i],shared_scaffold=r['scaffold'] in {x['scaffold'] for x in old}))
write_csv(out/'nearest_training.csv',nearest,list(nearest[0]))
inputs=[Path(__file__),root/'external_protocol.json',oldfeatures,oldlineage,root/'analysis-v2/compounds.csv',root/'analysis-v2/raphanus_labels.csv']
(out/'manifest.json').write_text(json.dumps(dict(input_hashes=hashes(inputs),output_hashes=hashes(list(out.iterdir())),code_hashes=hashes(list(HERE.glob('*.py'))),lock_hashes=hashes([HERE/'uv.lock',HERE/'pyproject.toml']),old_labeled=73,new_labeled=20,new_unknown=7,primary_test='Flavonoids2012',canonical_overlap=0,scope=protocol['assumptions']),indent=2)+'\n')
manifest=run(out/'features.parquet',out/'lineage.csv',Path('analysis/outputs/experimental-flavonoid-transfer-2026-11-12'))
print(json.dumps([r for r in manifest['reports'] if r['publication']=='Flavonoids2012'],indent=2))
