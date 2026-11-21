import csv
import gzip
import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_sprint import sha256
from sprint_catalog_cross import run


def write_gzip(path, rows):
    with gzip.open(path, 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_catalog_cross_excludes_held_provider_ids_and_preserves_stereo_candidates(tmp_path):
    npass, coconut = tmp_path / 'npass', tmp_path / 'coconut'
    npass.mkdir()
    coconut.mkdir()
    identities = npass / 'npass_identity.csv.gz'
    write_gzip(identities, [
        {'source_compound_id': 'N1', 'full_inchikey': 'ABC-STEREO-N', 'identity_status': 'valid'},
        {'source_compound_id': 'N2', 'full_inchikey': 'ABC-OTHER-N', 'identity_status': 'valid'},
        {'source_compound_id': 'N3', 'full_inchikey': 'XYZ-FORM-N',
         'identity_status': 'provider_key_conflict'}])
    (npass / 'manifest.json').write_text(json.dumps({
        'products': {identities.name: sha256(identities)}, 'inputs': {}, 'identity_records': 3}))
    conflicts = coconut / 'coconut_identity_conflicts.csv.gz'
    write_gzip(conflicts, [{'source_compound_id': 'C2'}])
    archive = tmp_path / 'coconut-lite'
    with ZipFile(archive, 'w') as z:
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames = ['identifier', 'standard_inchi_key'])
        writer.writeheader()
        writer.writerows([{'identifier': 'C1', 'standard_inchi_key': 'ABC-STEREO-N'},
                          {'identifier': 'C2', 'standard_inchi_key': 'ABC-OTHER-N'},
                          {'identifier': 'C3', 'standard_inchi_key': 'XYZ-FORM-N'}])
        z.writestr('source.csv', stream.getvalue())
    (coconut / 'manifest.json').write_text(json.dumps({
        'products': {conflicts.name: sha256(conflicts)},
        'inputs': {str(archive): sha256(archive)}, 'source_records': 3}))
    result = run(npass, coconut, tmp_path / 'output')
    assert result['source_id_match_counts'] == {
        'exact_full_key': 1, 'connectivity_only_review': 1, 'identity_hold': 1}
    with gzip.open(tmp_path / 'output/npass_coconut_overlap.csv.gz', 'rt') as stream:
        rows = list(csv.DictReader(stream))
    assert rows[1]['coconut_ids'] == 'C1'
    assert all('C2' not in r['coconut_ids'] for r in rows)
