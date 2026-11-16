"""Visual audit of exact parent versus hydrolyzed bound chemistry."""
import json,hashlib
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Draw
root=Path('experiments/binding-pilot-2026-11-12')
out=root/'figures-v1'
if out.exists():raise ValueError('Use a fresh figure version')
paths=[root/'sources/TTX_chemcomp.json',root/'sources/cornexistin_pubchem.json',root/'sources/UP0_chemcomp.json']
smiles=[json.loads(paths[0].read_text())['rcsb_chem_comp_descriptor']['SMILES_stereo'],json.loads(paths[1].read_text())['PropertyTable']['Properties'][0]['SMILES'],json.loads(paths[2].read_text())['rcsb_chem_comp_descriptor']['SMILES_stereo']]
labels=['Tentoxin / TTX: exact parent','Cornexistin parent: anhydride','UP0: bound hydrolyzed diacid']
mols=[Chem.MolFromSmiles(s) for s in smiles]
svg=Draw.MolsToGridImage(mols,molsPerRow=3,subImgSize=(400,330),legends=labels,useSVG=True)
out.mkdir()
(out/'bound_forms.svg').write_text(svg)
(out/'manifest.json').write_text(json.dumps({'input_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[Path(__file__)]},'output_hashes':{str((out/'bound_forms.svg').resolve()):hashlib.sha256(svg.encode()).hexdigest()},'scope':'Deposited ligand/parent graphs; not calculated protein contacts or an affinity/safety prediction.'},indent=2)+'\n')
import vl_convert as vlc
Path('/private/tmp/agrotox-bound-forms.png').write_bytes(vlc.svg_to_png(svg))
