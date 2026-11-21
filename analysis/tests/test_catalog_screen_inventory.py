from catalog_screen_inventory import featured


def test_catalog_inventory_rejects_conflicting_keys_and_multicomponent_forms():
    assert featured(('id', 'wrong', 'CCO', '')) == (None, 'missing_or_conflicting_full_key')
    assert featured(('id', 'unused', 'CCO.O', '')) == (None, 'multiple_components')
    assert featured(('id', 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N', 'CCO', '', 'source_id_structure_conflict')) == (
        None, 'source_id_structure_conflict')
