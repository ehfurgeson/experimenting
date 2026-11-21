import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_sprint import sha256
from sprint_report import summarize_overlap, verify_bundle


def test_tier_counts_preserve_alias_denominators_and_reviewed_distinction():
    fields = ['coconut_exact', 'npass_exact', 'either_catalog_exact',
              'taxon_publication_linked_unreviewed', 'adopted_occurrence',
              'measured_a', 'adopted_plant_response', 'catalog_measured_plant',
              'linked_occurrence_measured_plant', 'adopted_occurrence_measured_plant']
    row = dict.fromkeys(fields, False) | {'cohort': 'selection', 'full_inchikey': 'KEY',
                                         'coconut_exact': True, 'either_catalog_exact': True,
                                         'taxon_publication_linked_unreviewed': True}
    result = {r['metric']: r for r in summarize_overlap([row, row.copy()])}
    assert result['coconut_exact']['rows_with_evidence'] == 2
    assert result['coconut_exact']['unique_full_structures'] == 1
    assert result['adopted_occurrence']['rows_with_evidence'] == 0
    assert result['catalog_measured_plant']['rows_with_evidence'] == 0


def test_report_rejects_changed_upstream_input_even_with_valid_products(tmp_path):
    source = tmp_path / 'raw'
    source.write_text('original')
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    product = bundle / 'product'
    product.write_text('normalized')
    (bundle / 'manifest.json').write_text(json.dumps({
        'products': {'product': sha256(product)}, 'inputs': {str(source): sha256(source)}}))
    verify_bundle(bundle)
    source.write_text('changed')
    with pytest.raises(ValueError, match = 'Upstream input hash mismatch'):
        verify_bundle(bundle)
