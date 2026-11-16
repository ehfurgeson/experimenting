"""Source-first preflight preserves unresolved chemicals and rejects broken links."""
import json
from zipfile import ZipFile

import pytest

from agrotox.ecotox_inventory import inspect, run


def snapshot(tmp_path, **changes):
    tables = {
        'validation/chemicals.txt': 'cas_number|chemical_name|dtxsid\n50|Alpha|DTXSID1\n51|Beta|\n',
        'validation/references.txt': 'reference_number|doi\n1|10.example/study\n',
        'validation/species.txt': 'species_number|kingdom\n1|Plantae\n',
        'tests.txt': 'test_id|test_cas|reference_number|species_number\n1|50|1|1\n2|51|1|1\n',
        'results.txt': 'result_id|test_id|endpoint|conc1_mean\n10|1|LD50|>5\n11|2|NR|NC\n',
        'release_notes_test.txt': 'synthetic offline fixture; not chemical evidence\n'}
    tables.update(changes)
    archive = tmp_path / 'inputs' / 'source.zip'
    archive.parent.mkdir(exist_ok = True)
    with ZipFile(archive, 'w') as out:
        for name, content in tables.items():
            out.writestr('ecotox_fixture/' + name, content)
    return archive


def test_source_first_keys_raw_evidence_and_candidate_matches(tmp_path):
    source = snapshot(tmp_path)
    before = source.read_bytes()
    result = inspect(source, [{'compound_id': 'KNOWN:1', 'dtxsid': 'DTXSID1',
                               'status': 'approved'}], sample_per_kind = 1)
    assert result['manifest']['counts']['chemicals'] == 2
    assert result['manifest']['candidate_selection_overlap'] == 1
    assert result['chemicals'][1]['identity_status'] == 'unresolved'
    assert result['chemicals'][1]['result_records'] == 1
    assert all(r['herbicidal_activity'] == 'unknown' for r in result['chemicals'])
    assert {r['sample_kind'] for r in result['samples']} == {'LD50', 'plant_other'}
    assert json.loads(result['samples'][0]['result_json'])['conc1_mean'] == '>5'
    assert json.loads(result['samples'][0]['test_json'])['test_cas'] == '50'
    assert source.read_bytes() == before


@pytest.mark.parametrize('table,content,message', [
    ('results.txt', 'result_id|test_id|endpoint\n1|9|LC50\n', 'Unresolved result'),
    ('results.txt', 'result_id|test_id|endpoint\n1|1|LC50\n1|2|LD50\n', 'duplicate result'),
    ('tests.txt', 'test_id|test_cas|reference_number|species_number\n1|99|1|1\n', 'foreign key'),
    ('results.txt', 'result_id|test_id|endpoint\n1|1|LC50|extra\n', 'field count'),
    ('validation/chemicals.txt', 'other|name\n1|test\n', 'header'),
])
def test_invalid_source_is_rejected_before_publication(tmp_path, table, content, message):
    source = snapshot(tmp_path, **{table: content})
    output = tmp_path / 'elsewhere' / 'output'
    with pytest.raises(ValueError, match = message):
        run(source, output)
    assert not output.exists()


def test_empty_samples_and_frozen_output_guard(tmp_path):
    source = snapshot(tmp_path)
    output = tmp_path / 'elsewhere' / 'output'
    manifest = run(source, output, sample_per_kind = 0)
    assert manifest['sample_counts'] == {}
    assert manifest['input_hashes']
    assert (output / 'samples.parquet').exists()
    with pytest.raises(ValueError, match = 'empty output'):
        run(source, output)
    with pytest.raises(ValueError, match = 'integer'):
        inspect(source, sample_per_kind = True)


def test_unsafe_archive_paths_are_rejected(tmp_path):
    source = snapshot(tmp_path)
    with ZipFile(source, 'a') as archive:
        archive.writestr('../escape.txt', 'unsafe')
    with pytest.raises(ValueError, match = 'Unsafe ZIP'):
        inspect(source)


def test_quoted_embedded_pipes_are_single_field(tmp_path):
    source = snapshot(tmp_path, **{
        'results.txt': 'result_id|test_id|endpoint|comment\n10|1|LD50|"protein A|B"\n'})
    result = inspect(source)
    assert json.loads(result['samples'][0]['result_json'])['comment'] == 'protein A|B'
