import numpy as np
import polars as pl
from sklearn.ensemble import RandomForestClassifier

from catalog_bulk_screen import merge_catalog, predict_batches
from catalog_screen_inventory import featured
from evidence_release import FEATURES, structure
from nice_endpoint_models import feature_arrays


def test_catalog_fingerprints_and_descriptors_match_endpoint_training():
    molecules = [structure(smiles) for smiles in ('CCO', 'c1ccccc1O', 'C[C@H](O)C(=O)O')]
    by_key = {r['full_key']: r for r in molecules}
    keys = list(by_key)
    rows = [featured(('source', r['full_key'], r['smiles'], 'name'))[0] for r in molecules]
    x = np.array([[r[f] for f in FEATURES] for r in rows])
    packed = np.frombuffer(b''.join(r['fingerprint'] for r in rows), dtype=np.uint8).reshape(-1, 256)
    train_x, train_bits, _ = feature_arrays(keys, by_key)
    np.testing.assert_array_equal(x, train_x)
    model = RandomForestClassifier(n_estimators=5, random_state=0).fit(train_bits, [0, 1, 0])
    np.testing.assert_allclose(predict_batches(model, x, packed, task='binary'),
                               model.predict_proba(train_bits)[:, 1])


def test_merge_catalog_preserves_both_source_identifiers_for_exact_overlap():
    first = pl.DataFrame({'full_key': ['one', 'two'], 'name': ['first', ''], 'coconut_identifier': ['C1', 'C2']})
    added = pl.DataFrame({'full_key': ['one', 'two', 'three'], 'name': ['other', 'second', 'third'],
                         'lotus_identifier': ['L1', 'L2', 'L3']})
    result = merge_catalog(first, added, 'lotus_identifier')
    assert result.rows() == [('one', 'first', 'C1', 'L1'), ('two', 'second', 'C2', 'L2'),
                             ('three', 'third', None, 'L3')]
