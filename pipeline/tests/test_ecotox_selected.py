"""Selected-source normalization preserves result grain, qualifiers and approval gates."""
import json
from zipfile import ZipFile

import polars as pl
import pytest

from agrotox.ecotox_selected import (
    DICTIONARIES,
    identities,
    import_selected,
    normalize,
    policies_from,
    run,
)
from tests.test_ecotox_inventory import snapshot


def dictionaries():
    data = {name: {} for name in DICTIONARIES}
    for name, pairs in {
        'endpoint': {'LC50': 'Lethal concentration', 'EC50': 'Effective concentration'},
        'effect': {'MOR': 'Mortality', 'BEH': 'Behavior', 'IMM': 'Immunological', 'ITX': 'Intoxication'},
        'measurement': {'MORT': 'Mortality', 'IMBL': 'Immobile'},
        'duration_unit': {'h': 'Hour(s)', 'd': 'Day(s)', 'hph': 'Hours post hatch'},
        'media_type': {'FW': 'Fresh water'}, 'concentration_unit': {'ug/L': 'ug/L', 'mg/L': 'mg/L'},
        'concentration_type': {'A': 'Active ingredient'}, 'chemical_formulation': {'PU': 'Pure'},
        'chemical_analysis': {'M': 'Measured'}, 'exposure_type': {'S': 'Static'},
        'test_type': {'ACUTE': 'Acute'},
    }.items():
        data[name] = pairs
    return data


def rule():
    return {'endpoint': 'LC50', 'species': ['oncorhynchus mykiss'], 'effect_code': 'MOR',
            'measurement_code': 'MORT', 'duration_hours': 96, 'medium': ['FW'],
            'standard_unit': 'mg/L', 'concentration_types': ['A'], 'formulations': ['PU'],
            'analysis_codes': ['M']}


def native(**changes):
    result = {'endpoint': 'LC50', 'effect': 'MOR', 'measurement': 'MORT',
              'chem_analysis_method': 'M', 'obs_duration_mean': '4', 'obs_duration_unit': 'd',
              'conc1_mean': '1000', 'conc1_mean_op': '>', 'conc1_unit': 'ug/L', 'conc1_type': 'A',
              **changes}
    return {'source_result_id': 'snapshot:result:1', 'source_chemical_id': 'ECOTOX:chemical:50',
            'result_json': json.dumps(result), 'test_json': json.dumps({
                'media_type': 'FW', 'exposure_type': 'S', 'test_type': 'ACUTE', 'test_formulation': 'PU'}),
            'species_json': json.dumps({'latin_name': 'Oncorhynchus mykiss'})}


def test_units_inequalities_multiple_slots_and_missing_duration():
    rows = normalize(native(conc2_mean = '2', conc2_unit = 'mg/L', conc2_type = 'A'), dictionaries())
    assert len(rows) == 2 and len({r['measurement_id'] for r in rows}) == 2
    assert rows[0]['value'] == 1 and rows[0]['qualifier'] == '>'
    assert rows[0]['duration_hours'] == 96 and rows[0]['compound_id'] is None
    assert normalize(native(obs_duration_unit = 'hph'), dictionaries())[0]['duration_hours'] is None
    bad = normalize(native(effect = 'NEW'), dictionaries())[0]
    assert bad['parse_status'] == 'review' and 'unknown_effect_code' in bad['review_reasons']
    assert normalize(native(conc1_unit = 'kg/ha'), dictionaries())[0]['value'] is None


def test_elapsed_weeks_require_dictionary_and_preserve_separate_times():
    source = native(obs_duration_mean = '2', obs_duration_unit = 'wk')
    test = json.loads(source['test_json'])
    test.update(exposure_duration_mean = '1', exposure_duration_unit = 'wk')
    source['test_json'] = json.dumps(test)
    assert normalize(source, dictionaries())[0]['duration_hours'] is None
    codes = dictionaries()
    codes['duration_unit'].update(wk = 'Week(s)', wph = 'Weeks post hatch')
    row = normalize(source, codes)[0]
    assert row['duration_hours'] == 336 and row['exposure_hours'] == 168
    assert json.loads(source['result_json'])['obs_duration_unit'] == 'wk'
    assert normalize(native(obs_duration_unit = 'wph'), codes)[0]['duration_hours'] is None
    assert normalize(native(obs_duration_unit = 'wk', obs_duration_mean_op = '>'),
                     codes)[0]['duration_hours'] is None


def test_ranges_are_distinct_from_scalars_and_daphnia_effects_do_not_alias():
    row = normalize(native(conc1_mean = 'NR', conc1_min = '2', conc1_max = '5'), dictionaries())[0]
    assert row['qualifier'] == 'range' and row['value'] is None
    assert row['lower'] == .002 and row['upper'] == .005
    from agrotox.ecotox_selected import policy_reasons
    r = normalize(native(endpoint = 'EC50', effect = 'IMM', measurement = 'IMBL'), dictionaries())[0]
    rules = {**rule(), 'endpoint': 'EC50', 'effect_code': 'ITX', 'measurement_code': 'IMBL'}
    assert 'effect' in policy_reasons(r, rules)


def test_identity_candidates_cannot_attach_canonical_ids():
    selected = {'ECOTOX:chemical:50'}
    row = {'source_chemical_id': next(iter(selected)), 'compound_id': 'KNOWN:1', 'status': 'candidate'}
    assert identities([row], selected)[1] == {}
    with pytest.raises(ValueError, match = 'exact structure'):
        identities([{**row, 'status': 'approved'}], selected)
    approved = {**row, 'status': 'approved', 'match_type': 'exact_structure',
                'source_identity_reference': 'Paper structure + exact key comparison',
                'reviewer': 'Scientific reviewer', 'review_date': '2026-11-11'}
    assert identities([approved], selected)[1] == {'ECOTOX:chemical:50': 'KNOWN:1'}
    with pytest.raises(ValueError, match = 'unique'):
        identities([approved, row], selected)


def archive(tmp_path):
    result = json.loads(native()['result_json'])
    keys = ['result_id', 'test_id', *result]
    source = snapshot(tmp_path, **{
        'validation/chemicals.txt': 'cas_number|chemical_name|dtxsid\n50|Alpha|DTXSID1\n51|Zero|\n',
        'validation/species.txt': 'species_number|kingdom|latin_name\n1|Animalia|Oncorhynchus mykiss\n',
        'tests.txt': 'test_id|test_cas|reference_number|species_number|media_type|exposure_type|test_type|test_formulation\n1|50|1|1|FW|S|ACUTE|PU\n',
        'results.txt': '|'.join(keys) + '\n' + '|'.join(['10', '1', *result.values()]) + '\n' +
                       '|'.join(['11', '1', *result.values()]) + '\n'})
    with ZipFile(source, 'a') as z:
        for name, content in dictionaries().items():
            z.writestr(f'ecotox_fixture/validation/{name}_codes.txt',
                       'code|description\n' + ''.join(f'{k}|{v}\n' for k, v in content.items()))
    return source


def test_all_equal_source_results_preserved_and_zero_hits_are_assessed(tmp_path):
    source = archive(tmp_path)
    ids = ['ECOTOX:chemical:50', 'ECOTOX:chemical:51']
    native_rows, measurements, coverage, admission, _, _ = import_selected(source, ids, [], {'trout': rule()})
    assert len(native_rows) == len(measurements) == 2
    assert native_rows[0]['source_result_id'] != native_rows[1]['source_result_id']
    assert coverage[1]['source_results'] == 0 and coverage[1]['canonical_coverage'] is None
    assert coverage[0]['eligible_results'] == 2
    assert not any(r['canonical_comparison_eligible'] for r in admission)


def test_failed_publication_is_atomic_and_existing_output_is_preserved(tmp_path, monkeypatch):
    import yaml
    source = archive(tmp_path)
    ids, crosswalk, policies = [tmp_path / name for name in ('ids.csv', 'crosswalk.csv', 'policies.yaml')]
    pl.DataFrame({'source_chemical_id': ['ECOTOX:chemical:50']}).write_csv(ids)
    pl.DataFrame({'source_chemical_id': ['ECOTOX:chemical:50'], 'status': ['candidate']}).write_csv(crosswalk)
    policies.write_text(yaml.safe_dump({'trout': rule()}))
    assert policies_from(policies)['trout'] == rule()
    output = tmp_path / 'products'
    original = pl.DataFrame.write_parquet
    def fail(self, *args, **kwargs):
        raise OSError('interrupted publication')
    monkeypatch.setattr(pl.DataFrame, 'write_parquet', fail)
    with pytest.raises(OSError, match = 'interrupted'):
        run(source, ids, crosswalk, policies, output)
    assert not output.exists()
    assert not list(tmp_path.glob('.ecotox-stage-*'))
    monkeypatch.setattr(pl.DataFrame, 'write_parquet', original)
    manifest = run(source, ids, crosswalk, policies, output)
    assert manifest['counts']['native_observations'] == 2
    before = (output / 'manifest.json').read_bytes()
    with pytest.raises(ValueError, match = 'new output'):
        run(source, ids, crosswalk, policies, output)
    assert (output / 'manifest.json').read_bytes() == before
