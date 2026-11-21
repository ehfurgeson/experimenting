import csv
import gzip
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint_plant_inventory import plant_candidate, run


def test_plant_filter_separates_algae_and_mechanistic_effects():
    vascular = {'kingdom': 'Plantae', 'ecotox_group': 'Flowers, Trees, Shrubs, Ferns'}
    assert plant_candidate(vascular, {'effect': 'GRO', 'measurement': 'LENG'})
    assert plant_candidate(vascular, {'effect': 'REP', 'measurement': 'GERM'})
    assert not plant_candidate(vascular, {'effect': 'BIO', 'measurement': 'CHLA'})
    assert not plant_candidate(vascular | {'ecotox_group': 'Algae'},
                               {'effect': 'GRO', 'measurement': 'BMAS'})


def test_native_bounds_and_unknown_labels_survive_export(tmp_path):
    adoption = tmp_path / 'adoption'
    adoption.mkdir()
    (adoption / 'policies.json').write_text(json.dumps({'test': {
        'status': 'human_adopted_bounded_policy', 'context': 'bounded test policy'}}))
    (adoption / 'accepted_activity_features.csv').write_text(
        'policy,structure_inchikey,structure_status,activity_target,scaffold,activity_reference\n'
        'test,KEY,valid,1,scaffold,doi\n')
    (adoption / 'identity_holds.csv').write_text('compound_id\nheld\n')
    (adoption / 'activity_observations.csv').write_text('observation_id\noriginal\n')
    test = {'test_id': '1', 'test_cas': '50', 'reference_number': '2', 'species_number': '3',
            'exposure_duration_mean': '7', 'exposure_duration_unit': 'd', 'control_type': 'C',
            'organism_habitat': 'Soil', 'media_type': 'SOIL'}
    result = {'result_id': '4', 'test_id': '1', 'effect': 'GRO', 'endpoint': 'NOEC',
              'measurement': 'LENG', 'response_site': 'ROOT', 'effect_pct_mean': '20',
              'effect_pct_mean_op': '<', 'trend': 'DEC', 'conc1_mean': '5', 'conc1_unit': 'mg/L',
              'obs_duration_mean': '7', 'obs_duration_unit': 'd'}
    species = {'species_number': '3', 'kingdom': 'Plantae',
               'ecotox_group': 'Flowers, Trees, Shrubs, Ferns', 'latin_name': 'Test plant',
               'ncbi_taxid': '999'}
    tables = {'tests.txt': test, 'results.txt': result, 'validation/species.txt': species,
              'validation/chemicals.txt': {'cas_number': '50', 'chemical_name': 'Test',
                                           'dtxsid': 'DTXSID1'},
              'validation/references.txt': {'reference_number': '2', 'doi': '10.example/test'}}
    source = tmp_path / 'source.zip'
    with ZipFile(source, 'w') as archive:
        for name, row in tables.items():
            stream = io.StringIO()
            writer = csv.DictWriter(stream, fieldnames = list(row), delimiter = '|')
            writer.writeheader()
            writer.writerow(row)
            archive.writestr('fixture/' + name, stream.getvalue())
    output = tmp_path / 'output'
    manifest = run(adoption, source, output)
    assert manifest['growth_germination_biomass_results'] == 1
    assert manifest['new_adopted_labels'] == 0
    with gzip.open(output / 'plant_activity_observations.csv.gz', 'rt') as stream:
        row = next(csv.DictReader(stream))
    assert row['activity_label'] == 'unknown'
    assert row['qualifier'] == '<'
    assert row['endpoint'] == 'NOEC'
    assert json.loads(row['source_record_json'])['result'] == result
    standalone = tmp_path / 'standalone'
    assert run(None, source, standalone)['includes_adopted_inputs'] is False
    assert not (standalone / 'accepted_policy_inventory.csv').exists()
    assert (standalone / 'plant_assay_registry.csv').read_bytes() == (
        output / 'plant_assay_registry.csv').read_bytes()
