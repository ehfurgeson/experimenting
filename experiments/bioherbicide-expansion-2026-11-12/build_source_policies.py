"""Provisional single-source labels, retaining missing identities and bounded responses."""
import sys,csv,json,hashlib,zipfile
from pathlib import Path
sys.path.insert(0,'analysis')
from activity_preflight import run
from labels import LABEL_FIELDS
from screen import write_csv
from structure import structure_features
root=Path('experiments/bioherbicide-expansion-2026-11-12')
out=root/'source-policies-v1'
if out.exists():raise ValueError('Use a new version')
out.mkdir()
policies={
 'AMBROSIA2019': {'policy':'EXPERIMENT-AMBROSIA2019-LETTUCE-1MM-7D-ORDINAL-v1','species':'Lactuca sativa','dose':'1000 micromolar','time':'7 days','endpoint':'ordinal germination/growth 0-5','active':'grade >=4','low_response':'grade <=1','unknown':'grades2/3 or missing/conflicting response','status':'AI experimental adoption only; source structure mappings provisional'},
 'OPHIOBOLINS2021': {'policy':'EXPERIMENT-OPHIOBOLINS2021-INTACT-1MGML-48H-v1','species':'Setaria viridis','dose':'1 mg/mL; 5 microliters per droplet','time':'48 hours','endpoint':'lesion diameter in mm on intact detached leaf','active':'exact value >=2 mm or entire reported interval >=2 mm','low_response':'exact0 mm only','unknown':'intermediate or ambiguous bounded response; do not assign <1 a zero','controls':'0.1% Tween-80 plus1% acetone; 3droplets per segment,3segments,3experimental repetitions','status':'AI experimental adoption only; three missing machine structures excluded from modeling'},
}
(out/'policies.json').write_text(json.dumps(policies,indent=2)+'\n')
pool=root/'pooled-v2-corrected-doi'
all_c=list(csv.DictReader((pool/'pooled_compounds.csv').open()));all_l=list(csv.DictReader((pool/'pooled_labels.csv').open()))
compounds=[r for r in all_c if r['compound_id'].startswith('AMBROSIA2019:')]
labels=[dict(r,activity_policy=policies['AMBROSIA2019']['policy']) for r in all_l if r['compound_id'].startswith('AMBROSIA2019:')]
write_csv(out/'ambrosia_compounds.csv',compounds,['compound_id','smiles'])
write_csv(out/'ambrosia_labels.csv',labels,['compound_id']+sorted(LABEL_FIELDS-{'compound_id'}))
run(out/'ambrosia_compounds.csv',out/'ambrosia_labels.csv',[root/'identity_holds.csv'],out/'ambrosia_preflight')

names=['3-anhydro-ophiobolin A','6-epi-ophiobolin A','6-epi-ophiobolin B','3-anhydro-6-epi-ophiobolin B','ophiobolin I']
raw_values=['3','<1','0','0','0'];activities=['active','unknown','inactive','inactive','inactive']
compounds=[];labels=[];identity=[]
for name,raw,activity in zip(names,raw_values,activities,strict=True):
    cid='OPHIOBOLINS2021:'+name
    p=root/'sources'/(name.replace(' ','_')+'.pubchem.json')
    props=json.loads(p.read_text())['PropertyTable']['Properties'] if p.exists() else []
    prop=props[0] if len(props)==1 else {}
    compounds.append({'compound_id':cid,'smiles':prop.get('SMILES','')})
    chem=structure_features(prop.get('SMILES'))
    assert not prop or prop['InChIKey']==chem['structure_inchikey']
    identity.append({'compound_id':cid,'name':name,'pubchem_cid':prop.get('CID'),'pubchem_inchikey':prop.get('InChIKey'),
        'identity_status':'single_database_hit_key_agrees_source_stereo_provisional' if prop else 'missing_after_literal_and_alternate_name_queries',
        'source_doi':'10.47371/mycosci.2020.11.002','source_locator':'structures Figs2/3; isolation and NMR section3.1',
        'decision_status':'AI experimental; not independent review'})
    labels.append({'compound_id':cid,'natural_origin':'natural','origin_reference':'10.47371/mycosci.2020.11.002 section3.1; isolated from B.setariae culture; database mapping provisional',
        'herbicidal_activity':activity,'activity_reference':'10.47371/mycosci.2020.11.002 Table1 intact leaves; section2.6',
        'activity_context':f'Setaria viridis; intact detached leaf;1mg/mL;5microliters/droplet;48h;lesion diameter {raw} mm;0.1%Tween80+1%acetone control;3segments x3repetitions; provisional AI experimental policy',
        'activity_policy':policies['OPHIOBOLINS2021']['policy']})
write_csv(out/'ophiobolin_compounds.csv',compounds,['compound_id','smiles'])
write_csv(out/'ophiobolin_labels.csv',labels,['compound_id']+sorted(LABEL_FIELDS-{'compound_id'}))
write_csv(out/'ophiobolin_identity.csv',identity,list(identity[0]))
m=run(out/'ophiobolin_compounds.csv',out/'ophiobolin_labels.csv',[root/'identity_holds.csv'],out/'ophiobolin_preflight')
print(m['reports'][0])
validation={'file':'sources/dittrichia2025_supplement.zip','http_status':200,'valid_zip':zipfile.is_zipfile(root/'sources/dittrichia2025_supplement.zip'),'disposition':'HTML download landing page; not a usable supplementary archive; no scientific data ingested'}
(out/'supplement_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
files=[p for p in out.iterdir() if p.is_file()]
(out/'manifest.json').write_text(json.dumps({'output_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'input_hashes':{str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'new_human_approved_labels':0,'scope':'User-authorized provisional AI source-policy experiments; do not overwrite or merge frozen human policies.'},indent=2)+'\n')
