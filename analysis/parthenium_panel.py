"""Reconcile the six measured response tables from Bashar et al. 2022."""

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from data_sprint import sha256

DOI = '10.3390/toxins14080561'
PANEL = 'Parthenium_hysterophorus'
CONTEXTS = {
    table: (species, outcome)
    for start, species in ((4, 'Digitaria sanguinalis'), (8, 'Eleusine indica'))
    for table, outcome in enumerate(('germination_percent', 'root_cm', 'shoot_cm'), start)
}
DOSES = (0, 100, 200, 400, 800, 1600)
IDENTITIES = {
    'Caffeic acid': ('', 'alkene_geometry_review'),
    'Vanillic acid': ('COc1cc(C(=O)O)ccc1O', 'structure_supported'),
    'Ferulic acid': ('COc1cc(/C=C/C(=O)O)ccc1O', 'structure_supported'),
    'Chlorogenic acid': ('', 'regioisomer_and_stereochemistry_review'),
    'Quinic acid': ('', 'stereochemistry_review'),
    'p-Anisic acid': ('COc1ccc(C(=O)O)cc1', 'structure_supported'),
    'Parthenin': ('', 'synonym_and_stereochemistry_review'),
    'Mixture (all compounds)': ('', 'mixture'),
}
NUMBER = r'-?\d+(?:\.\d+)?'
CELL = re.compile(rf'({NUMBER})(?:\s*±\s*({NUMBER}))?\s*[a-zA-Z]+\s*\(({NUMBER})\)')


def band(inhibition):
    if inhibition >= 40:
        return 'high'
    if inhibition <= 20:
        return 'low'
    return 'intermediate'


def compare_cell(control, treatment):
    """Keep both source estimates and withhold inconsistent response bands."""
    control_match, treatment_match = CELL.fullmatch(control), CELL.fullmatch(treatment)
    if not control_match or not treatment_match:
        raise ValueError(f'Unrecognized response cells: {control!r}, {treatment!r}')
    control_mean, treated_mean = float(control_match[1]), float(treatment_match[1])
    if control_mean <= 0 or treated_mean < 0 or float(control_match[3]) != 0:
        raise ValueError('Invalid control or treatment mean')
    reported = float(treatment_match[3])
    derived = 100 * (1 - treated_mean / control_mean)
    delta = abs(reported - derived)
    consistent = delta <= 1 and band(reported) == band(derived)
    return {'control_mean': control_mean, 'control_sem': control_match[2] or '',
            'treated_mean': treated_mean, 'treated_sem': treatment_match[2] or '',
            'reported_inhibition_percent': reported, 'derived_inhibition_percent': derived,
            'absolute_discrepancy_pp': delta,
            'context_response': band(derived) if consistent else 'review_discrepancy'}


def text_cells(row):
    return [' '.join(''.join(cell.itertext()).split()) for cell in row]


def extract(root):
    if DOI not in [n.text for n in root.findall('.//article-id[@pub-id-type="doi"]')]:
        raise ValueError('Unexpected article DOI')
    for table, (species, outcome) in CONTEXTS.items():
        tag = f'toxins-14-00561-t{table:03}'
        table_node = root.find(f'.//table-wrap[@id="{tag}"]')
        if table_node is None:
            raise ValueError(f'Missing table {table}')
        header = table_node.findall('.//thead/tr')
        if tuple(float(v) for v in text_cells(header[-1])) != DOSES:
            raise ValueError(f'Unexpected dose grid in {tag}')
        seen = set()
        for row in table_node.findall('.//tbody/tr'):
            name, *cells = text_cells(row)
            if name.startswith(('CV ', 'LSD ')):
                continue
            if name not in IDENTITIES or name in seen or len(cells) != len(DOSES):
                raise ValueError(f'Unexpected compound row in {tag}: {name}')
            seen.add(name)
            smiles, status = IDENTITIES[name]
            control = cells[0]
            for dose, treatment in zip(DOSES[1:], cells[1:], strict=True):
                yield {'panel': PANEL, 'doi': DOI, 'source_locator': f'Table {table}',
                       'compound_name': name, 'smiles': smiles, 'identity_status': status,
                       'test_species': species, 'endpoint': outcome,
                       'nominal_concentration_uM': dose, 'response_day': 7,
                       'control_cell': control, 'treated_cell': treatment,
                       **compare_cell(control, treatment)}
        if seen != IDENTITIES.keys():
            raise ValueError(f'Incomplete compound rows in {tag}')


def main(source, output):
    observations = list(extract(ET.parse(source).getroot()))
    output.mkdir(parents=True, exist_ok=False)
    products = {
        'observations.csv': observations,
        'panel.csv': [{'panel': PANEL, 'doi': DOI, 'source_locator': 'Table 3; dose series 4-6, 8-10',
                       'compound_name': name, 'smiles': smiles, 'identity_status': status}
                      for name, (smiles, status) in IDENTITIES.items()],
    }
    for name, rows in products.items():
        with (output / name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
    manifest = {'inputs': {str(source): sha256(source)},
                'products': {name: sha256(output / name) for name in products},
                'counts': Counter(r['context_response'] for r in observations)}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(main(**vars(parser.parse_args())), indent=2))
