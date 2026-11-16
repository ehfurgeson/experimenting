"""Offline provisional transcription of complete selected plant-response tables.

Run from repository root after fetch_sources.py and inspect_html.py.
No source correction, digitization, label promotion or inferred inactivity.
"""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path('experiments/bioherbicide-expansion-2026-11-12')
SOURCES = ROOT / 'sources'
OUTPUT = ROOT / 'transcription-v1'
if OUTPUT.exists():
    raise ValueError('Use a new version; existing transcriptions are immutable')

CONTEXT = {
    'AMBROSIA2019': {
        'file': 'ambrosia2019.html', 'doi': '10.3390/molecules24050835',
        'locator': 'Table 2; sections 2.1, 3.3 and 3.7.1',
        'sample_type': 'isolated_compound', 'application': '24-well germination/growth assay',
        'controls': 'solvent wells; solvent identity/final proportion not stated in inspected subsection',
        'replication': 'not reported in inspected subsection',
        'quality_gaps': 'provisional PubChem name-to-structure mapping; replication and vehicle detail',
    },
    'NONENOLIDES2021': {
        'file': 'nonenolides2021.html', 'doi': '10.3390/jof7100829',
        'locator': 'Table 2; sections 2.2, 2.3 and 2.4.1-2.4.5',
        'sample_type': 'isolated_or_semisynthetic_compound_or_herbicide_control',
        'application': 'endpoint-specific; see observation application',
        'controls': '5% EtOH for leaf puncture; microalgae DMSO stated 0.01%; Sf9 DMSO 1%',
        'replication': '12 leaf discs; lettuce 3 wells x 5 seeds, 2 experiments',
        'quality_gaps': 'relative stereo for some derivatives; non-target assays not EPA endpoints; stated microalgae solvent proportion requires check against volumes',
    },
    'SORBICILLINOIDS2019': {
        'file': 'sorbicillinoids2019.html', 'doi': '10.3389/fchem.2019.00435',
        'locator': 'Table 5; Phytotoxicity Assay; Biological Activity',
        'sample_type': 'isolated_compound_or_glyphosate_control',
        'application': 'seed elongation assay; protocol cited to Lu et al. 2015',
        'controls': 'blank control; glyphosate positive control',
        'replication': 'three replicates; table footnote mean +/- SD',
        'quality_gaps': 'exposure time and vehicle not recovered from cited protocol; bisvertinolone and trichodimerol multiple PubChem hits',
    },
    'CLEOMSIDE2020': {
        'file': 'cleomside2020.html', 'doi': '10.3390/molecules25194461',
        'locator': 'Table 2; sections 2.1 and 3.3',
        'sample_type': 'isolated_compound_or_extract',
        'application': '20 imbibed lettuce seeds per dish; 5 mL test solution on filter paper',
        'controls': 'distilled water; methanol dilution stated; solvent evaporation explicit only in cytogenotoxic subsection',
        'replication': 'N=3; statistical section; dish independence not independently verified',
        'quality_gaps': 'Table caption seven days versus germination counts over six days in methods; no matched vehicle verified; cleomside/cleomoside spelling varies',
    },
    'ROSEMARY2018': {
        'file': 'rosemary2018.html', 'doi': '10.3390/toxins10120498',
        'locator': 'Table 2; germination bioassay methods',
        'sample_type': 'carnosic_acid_reagent',
        'application': 'filter-paper germination assay; 250 micrograms/mL carnosic acid',
        'controls': 'control-relative elongation; species-specific protocol requires further check',
        'replication': 'three replications; mean +/- SD',
        'quality_gaps': 'species not compounds are the rows; cannot add 21 independent structures or same-policy negatives',
    },
}

def tables(stem):
    return json.loads((SOURCES / f'{stem}.tables.json').read_text())


def numeric(raw):
    match = re.fullmatch(r'\s*([<>]=?)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:±\s*([0-9]+(?:\.[0-9]+)?))?\s*([a-z ]*\*?)\s*', raw)
    if not match:
        return {'value': None, 'qualifier': '', 'dispersion': None,
                'significance_group': '', 'parse_status': 'unparsed_categorical_or_bound'}
    return {'value': float(match[2]), 'qualifier': match[1] or '=',
            'dispersion': float(match[3]) if match[3] else None,
            'significance_group': match[4].strip(), 'parse_status': 'numeric'}


plant, other = [], []
def add(study, compound, species, endpoint, time, dose, dose_unit, raw, unit,
        sample_type = None, application = None, destination = plant):
    ctx = CONTEXT[study]
    identity = [study, compound, species, endpoint, str(time), str(dose), dose_unit]
    obs_id = study + ':' + hashlib.sha256('|'.join(identity).encode()).hexdigest()[:20]
    destination.append({
        'observation_id': obs_id, 'study_id': study, 'compound_id': f'{study}:{compound}',
        'source_compound': compound, 'species': species, 'endpoint': endpoint,
        'assessment_hours': time, 'dose': dose, 'dose_unit': dose_unit,
        'raw_response': raw, 'response_unit': unit, **numeric(raw),
        'sample_type': sample_type or ctx['sample_type'], 'application': application or ctx['application'],
        'source_doi': ctx['doi'], 'source_locator': ctx['locator'],
        'source_file': str(SOURCES / ctx['file']),
        'source_sha256': hashlib.sha256((SOURCES / ctx['file']).read_bytes()).hexdigest(),
        'controls': ctx['controls'], 'replication': ctx['replication'],
        'quality_gaps': ctx['quality_gaps'], 'extractor': 'Codex AI',
        'extraction_date': '2026-11-12', 'checker': 'not_independently_checked',
        'decision_status': 'provisional_experimental_transcription',
    })

# Ambrosia Table 2: preserve both plant species and all three doses.
t = tables('ambrosia2019')[1]
assert t[0] == ['Compounds', 'C (µM)', 'L. sativa', 'A. stolonifera']
assert len(t) == 7
compound = None
for row in t[1:]:
    assert len(row) == 4
    compound = row[0] or compound
    for i, species, hours in [(2, 'Lactuca sativa', 168), (3, 'Agrostis stolonifera', 240)]:
        add('AMBROSIA2019', compound, species, 'ordinal_germination_growth_0_to_5',
            hours, float(row[1]), 'micromolar', row[i], 'ordinal_grade')

# Nonenolides Table 2: every phytotoxic and non-target row, including controls.
t = tables('nonenolides2021')[1]
assert len(t) == 16 and t[3][0] == '1' and t[-1][0] == 'metsulfuron-methyl'
for row in t[3:]:
    assert len(row) == 8
    compound = row[0]
    for column, hours in [(1, 48), (2, 120)]:
        add('NONENOLIDES2021', compound, 'Sonchus arvensis', 'necrotic_lesion_diameter',
            hours, 2., 'mg/mL; 10 microliters per disc', row[column], 'mm',
            application = 'punctured leaf disc; 20 micrograms per disc')
    add('NONENOLIDES2021', compound, 'Lactuca sativa', 'seedling_length_ID50',
        72, None, 'dose_response; 5-200 micrograms/seed', row[3], '1e-8 mol/seed',
        application = 'water agar; root plus shoot length; solvents evaporated before seed placement')
    for column, species, endpoint, hours, unit in [
        (4, 'Haematococcus lacustris', 'cell_viability_LC50', 48, 'micrograms/mL (micromolar)'),
        (5, 'Bacillus subtilis', 'growth_inhibition_zone_radius', 24, 'mm'),
        (6, 'Spodoptera frugiperda Sf9 cells', 'cell_death_LC50', 24, 'micrograms/mL (micromolar)'),
    ]:
        add('NONENOLIDES2021', compound, species, endpoint, hours, None,
            'dose_response_or_100_micrograms_per_disc_for_bacteria', row[column], unit,
            destination = other)

# Sorbicillinoids Table 5: all compounds/doses, radicle and germ, rice and lettuce.
t = tables('sorbicillinoids2019')[4]
assert len(t) == 22 and len(t[2]) == 6
compound = None
for row in t[2:]:
    assert len(row) == 6
    compound = row[0] or compound
    for i, species, endpoint in [(2, 'Oryza sativa Zhonghua11', 'radicle_elongation_inhibition'),
                                  (3, 'Oryza sativa Zhonghua11', 'germ_elongation_inhibition'),
                                  (4, 'Lactuca sativa var. ramose', 'radicle_elongation_inhibition'),
                                  (5, 'Lactuca sativa var. ramose', 'germ_elongation_inhibition')]:
        add('SORBICILLINOIDS2019', compound, species, endpoint, None,
            float(row[1]), 'micrograms/mL', row[i], 'percent_inhibition')

# Cleomside Table 2: normalize rowspans while retaining extract as a separate sample type.
t = tables('cleomside2020')[1]
assert len(t) == 10
for row in t[2:]:
    row = row[1:] if len(row) == 8 else row
    assert len(row) == 7
    compound = row[0]
    for i, dose in enumerate([50, 100, 200, 400, 800], 1):
        add('CLEOMSIDE2020', compound, 'Lactuca sativa', 'germination_index_percent_control',
            None, dose, 'micrograms/mL', row[i], 'percent_of_control',
            sample_type = 'extract' if compound == 'EtOAc Extract' else 'isolated_compound')

# Rosemary Table 2: rows are species, all at the same carnosic-acid dose.
t = tables('rosemary2018')[1]
assert len(t) == 23
for row in t[2:]:
    # Missing family rowspans mean some rows have 5 cells and some have 6.
    row = row[1:] if len(row) == 6 else row
    assert len(row) == 5
    species = row[1]
    for i, endpoint in [(2, 'radicle_elongation'), (3, 'hypocotyl_elongation')]:
        add('ROSEMARY2018', 'carnosic acid', species, endpoint, None, 250,
            'micrograms/mL', row[i], 'percent_of_control')

assert len(plant) == 213, len(plant)
assert len(other) == 39
assert len({r['observation_id'] for r in plant + other}) == len(plant + other)
OUTPUT.mkdir()
for name, rows in [('plant_observations', plant), ('nontarget_observations', other)]:
    with (OUTPUT / f'{name}.csv').open('w', newline = '') as stream:
        w = csv.DictWriter(stream, fieldnames = list(rows[0])); w.writeheader(); w.writerows(rows)
summary = {
    'plant_observations': len(plant), 'nontarget_observations': len(other),
    'plant_rows_by_study': dict(Counter(r['study_id'] for r in plant)),
    'plant_parse_status': dict(Counter(r['parse_status'] for r in plant)),
    'models_fitted': 0, 'human_approved_new_labels': 0,
    'limits': 'AI provisional transcription; source tables have not received independent review. '
              'Controls/extracts retained; observations are not independent compounds. '
              'n/a remains categorical, not zero or a numerical LC50 bound. '
              'Missing times remain null; percent control is not percent inhibition. '
              'Omitted figure-only responses were not digitized.',
}
(OUTPUT / 'summary.json').write_text(json.dumps(summary, indent = 2) + '\n')
files = list(SOURCES.glob('*.html')) + list(SOURCES.glob('*.tables.json')) + [Path(__file__), ROOT/'EXPERIMENT_PROTOCOL.json']
manifest = {'input_hashes': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'output_hashes': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.iterdir()},
            **summary}
(OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
print(json.dumps(summary, indent = 2))
