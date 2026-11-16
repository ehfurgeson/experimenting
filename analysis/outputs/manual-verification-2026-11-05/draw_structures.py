"""Draw supplied frozen SMILES for manual source matching; these are not paper diagrams."""
import csv
import hashlib
import json
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Draw

pack = Path(__file__).resolve().parent
out = pack / 'assays/structure_drawings'
assert not out.exists(), 'Use a fresh drawing directory'
out.mkdir()
inputs, counts = {}, {}
for study in ('li2006', 'he2011'):
    source = pack / f'assays/{study}_source_mapping.csv'
    rows = list(csv.DictReader(source.open()))
    inputs[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
    counts[study] = len(rows)
    for start in range(0, len(rows), 12):
        group = rows[start:start+12]
        mols = [Chem.MolFromSmiles(r['frozen_smiles']) for r in group]
        assert all(m is not None for m in mols)
        svg = Draw.MolsToGridImage(mols, molsPerRow=3, subImgSize=(340,260),
                                  legends=[r['compound_id']+' / '+r['activity_id'] for r in group],
                                  useSVG=True)
        (out / f'{study}_{start//12+1:02d}.svg').write_text(svg)
manifest = {'source_hashes': inputs, 'compound_counts': counts,
            'output_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.svg')},
            'scope':'RDKit depictions of frozen SMILES for comparison; not independently verified original-paper structures.'}
(out / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(counts, 'SVG pages',len(manifest['output_hashes']))
