import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_sprint import freeze_baseline, read_csv, sha256, write_csv


def baseline_inputs(tmp_path):
    release = tmp_path / 'release'
    release.mkdir()
    for cohort in ('A', 'B'):
        write_csv(release / f'{cohort}_compounds.csv', [
            {'full_key': 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N', 'smiles': 'CCO',
             'target_log10_mg_kg': 3}], ['full_key', 'smiles', 'target_log10_mg_kg'])
    (release / 'manifest.json').write_text(json.dumps({'outputs': {
        p.name: sha256(p) for p in release.glob('*.csv')}}))
    selection = tmp_path / 'selection.parquet'
    pl.DataFrame([{'compound_id': 'original:1', 'structure_inchikey': None,
                   'input_smiles': 'unresolved', 'structure_status': 'invalid',
                   'chemical_group': 'natural product'}]).write_parquet(selection)
    return release, selection


def test_freeze_retains_unresolved_selection_and_refuses_overwrite(tmp_path):
    release, selection = baseline_inputs(tmp_path)
    output = tmp_path / 'freeze'
    result = freeze_baseline(release, selection, output)
    assert result['counts'] == {'A': 1, 'B': 1, 'selection': 1}
    rows = read_csv(output / 'cohort_membership.csv')
    assert rows[-1]['identity_status'] == 'invalid'
    assert rows[-1]['full_inchikey'] == ''
    with pytest.raises(FileExistsError):
        freeze_baseline(release, selection, output)


def test_freeze_rejects_tampered_upstream(tmp_path):
    release, selection = baseline_inputs(tmp_path)
    with (release / 'A_compounds.csv').open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError, match = 'hash mismatch'):
        freeze_baseline(release, selection, tmp_path / 'freeze')
    assert not (tmp_path / 'freeze').exists()


def test_acquisition_preserves_native_bytes_and_failure_status(tmp_path, monkeypatch):
    import gzip
    import hashlib

    from collect_data_sprint import collect

    class Response:
        status_code = 503
        url = 'https://example.test/source'
        ok = False

        def __init__(self):
            self.headers = {'Content-Type': 'text/plain'}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def iter_content(self, size):
            yield b'provider failure body\n'

    monkeypatch.setattr('collect_data_sprint.requests.get', lambda *a, **kw: Response())
    record = collect(tmp_path, ['npass-toxicity'])[0]
    assert record['status'] == 'http_error'
    assert gzip.decompress((tmp_path / record['file']).read_bytes()) == b'provider failure body\n'
    assert record['native_sha256'] == hashlib.sha256(b'provider failure body\n').hexdigest()
    with pytest.raises(ValueError, match = 'overwrite'):
        collect(tmp_path, ['npass-toxicity'])
