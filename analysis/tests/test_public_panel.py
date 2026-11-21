from public_panel import benchmark_panel, literature_panel, reviewed_panel


def test_hrac_aliases_do_not_hide_conflicting_forms():
    raw = [(12, {'ACTIVE': 'Form A=Form B ', 'HRAC GLOBAL': '4'})]
    [row] = benchmark_panel(raw, {'form a': {'keyA'}, 'form b': {'keyB'}})
    assert row['source_locator'] == 'row 12'
    assert row['identity_status'] == 'ambiguous_name'
    assert row['candidate_full_keys'] == 'keyA;keyB'
    assert row['full_key'] == ''
    [row] = benchmark_panel(raw, {'form a': {'keyA'}, 'form b': {'keyA'}})
    assert row['full_key'] == 'keyA'
    assert row['identity_status'] == 'unambiguous_source_name_lead'


def test_reviewed_panel_keeps_rows_with_conflicting_structure():
    structures = {}
    [row] = reviewed_panel([{'structure_inchikey': 'wrong', 'structure_status': 'valid',
                             'input_smiles': 'CCO', 'chemical_group': 'natural_product',
                             'compound_id': 'x1', 'query': 'ethanol'}], structures)
    assert structures == {}
    assert row['full_key'] == ''
    assert row['candidate_full_keys'] == 'wrong'
    assert row['identity_status'] == 'structure_key_conflict'


def test_literature_panel_keeps_studies_separate_and_holds_disagreement():
    common = {'compound_name': 'standard', 'doi': 'doi', 'source_locator': 'table',
              'smiles': 'CCO', 'identity_status': 'structure_supported'}
    rows = [common | {'panel': 'study A'}, common | {'panel': 'study B'},
            common | {'panel': 'study B', 'smiles': 'CCN'}]
    supported, conflict = literature_panel(rows, {})
    assert supported['panel'] == 'study A'
    assert supported['full_key'] == 'LFQSCWFLJHTTHZ-UHFFFAOYSA-N'
    assert conflict['panel'] == 'study B'
    assert conflict['identity_status'] == 'source_identity_conflict'
    assert conflict['full_key'] == ''
