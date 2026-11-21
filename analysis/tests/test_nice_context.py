import evidence_release


def test_context_identity_distinguishes_structure_evidence_and_identifier_leads():
    from nice_context import match

    key = evidence_release.structure('CCO')['full_key']
    other = evidence_release.structure('CCCO')['full_key']
    mappings = {'DTXSID1': {key}, 'DTXSID2': {key, other}}
    wanted = {key}
    assert match({'DTXSID': 'DTXSID1', 'SMILES': 'CCO'}, mappings, wanted, {}) == (
        'exact_structure', {key})
    assert match({'DTXSID': 'DTXSID1'}, mappings, wanted, {}) == (
        'identifier_only', {key})
    assert match({'DTXSID': 'DTXSID2'}, mappings, wanted, {}) == (
        'identity_hold', {key, other})
    assert match({'DTXSID': 'DTXSID1', 'SMILES': 'CCCO'}, mappings, wanted, {}) == (
        'identity_hold', {key, other})
    assert match({'DTXSID': 'DTXSID1', 'SMILES': {'formula': 'B2'}}, mappings, wanted, {}) == (
        'identity_hold', {key})
    assert match({'DTXSID': 'DTXSID3', 'SMILES': 'CCCO'}, mappings, wanted, {}) is None
