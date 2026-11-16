"""Preserve author-reported contacts and assay quantities without inventing affinities."""
import csv,hashlib,json,sys,copy
from pathlib import Path
sys.path.insert(0,'analysis')
from binding_catalog import run
from weekly_report import verify_manifest
root=Path('experiments/binding-pilot-2026-11-12')
out=root/'curation-v1'
if out.exists():raise ValueError('Use a new curation version')
out.mkdir()
rows=[]
def add(pdb,ligand,residue,protein,interaction,group,doi,locator):
 rows.append({'pdb_id':pdb,'ligand_component_id':ligand,'residue_literal':residue,
  'protein_role':protein,'author_reported_contact':interaction,'ligand_group':group,
  'source_doi':doi,'source_locator':locator,'evidence_class':'author_interpretation_of_experimental_structure',
  'distance_angstrom':None,'sequence_mapping_status':'paper numbering retained; not mapped to deposited sequence or author chain IDs',
  'review_status':'AI_experimental_not_independently_checked'})
add('1KMH','TTX','Asp83','beta subunit','hydrogen bond','tentoxin peptide','10.1073/pnas.052546099','Tentoxin-Binding Site at alpha/beta Interface')
for residue in ['Ile63','Leu65','Val75','Tyr237','Leu238','Met274']:
 add('1KMH','TTX',residue,'alpha subunit','hydrophobic contact','tentoxin','10.1073/pnas.052546099','Tentoxin-Binding Site at alpha/beta Interface')
for residue in ['Arg369','Ser396','His474','Arg533']:
 add('8CI0','UP0',residue,'first monomer in paper','carboxyl-group interaction','diacid carboxyl groups','10.1002/chem.202300199','X-ray co-crystal structure; Figure3a')
for residue,group,kind in [('Asp482B','C2 hydroxyl','hydrogen bond'),('Gly37A','C8 hydroxyl','backbone hydrogen bond'),('Gly276A','C8 hydroxyl','backbone hydrogen bond'),('His38A','C2 hydroxyl','water-mediated bridge')]:
 add('8CI0','UP0',residue,'paper monomer label; not PDB author-chain mapping',kind,group,'10.1002/chem.202300199','Design of simplified cornexistin analogues; Figure4')
assert len(rows)==15
with (out/'author_reported_contacts.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
quantities=[
 {'parent':'cornexistin','pdb_context':'8CI0','quantity_role':'functional_enzyme_inhibition','endpoint':'IC50','value':50.,'uncertainty':5.,'unit':'micromolar','qualifier':'=','organism':'Zea mays','target':'transketolase','source_doi':'10.1002/chem.202300199','source_locator':'In vitro target engagement; SchemeS1 referenced','limits':'Assay reports parent added; bound solution species not independently resolved. +/-5 uncertainty type/replicates not recovered. Not Kd/Ki; full assay conditions require SI.'},
 {'parent':'tentoxin','pdb_context':'1KMH','quantity_role':'complex_preparation','endpoint':'incubation_concentration','value':.05,'uncertainty':None,'unit':'mM','qualifier':'=','organism':'Spinacia oleracea','target':'chloroplast F1 ATPase','source_doi':'10.1073/pnas.052546099','source_locator':'Crystallization and Data Collection','limits':'Protein-complex preparation concentration; not Kd/Ki/IC50 or a plant efficacy dose.'}
]
with (out/'reported_quantities.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(quantities[0]));w.writeheader();w.writerows(quantities)
# Test the actual misleading default cofactor route with the same parent record.
resource=json.loads((root/'records.json').read_text())
bad=copy.deepcopy(resource['records'][1]);bad['ligand_component_id']='8EL'
(out/'wrong_cofactor_resource.json').write_text(json.dumps({'records':[bad]},indent=2)+'\n')
try:
 run(out/'wrong_cofactor_resource.json',root/'sources',out/'wrong_cofactor_output')
 raise AssertionError('Wrong cofactor was accepted')
except ValueError as error:
 (out/'wrong_cofactor_rejection.json').write_text(json.dumps({'status':'rejected_as_expected','reason':str(error),'output_created':(out/'wrong_cofactor_output').exists()},indent=2)+'\n')
 assert not (out/'wrong_cofactor_output').exists()
manifest=verify_manifest(Path('analysis/outputs/binding-structural-pilot-2026-11-12-final/manifest.json'))
assert manifest['interactions']==2 and manifest['protein_entities']==3 and manifest['models_fitted']==0
sources=[root/'sources/tentoxin_primary.html',root/'sources/cornexistin_primary.html',Path(__file__)]
record={'input_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
 'output_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},
 'contacts':15,'quantities':2,'Kd_or_Ki_labels_added':0,'scope':'Manual AI transcription of primary author interpretations; no new geometric contact calculations; no re-mapping of residue numbers; no affinity or safety model.'}
(out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
verify_manifest(out/'manifest.json')
print('2 structural records;3 protein sequences;15 author-reported contacts;0 Kd/Ki labels; wrong cofactor rejected')
