from nice_archive_coverage import assay_coverage


def test_assay_coverage_counts_native_endpoints_without_using_responses():
    rows = [
        {'DTXSID': 'known', 'Endpoint': 'hit call', 'Response': '1'},
        {'DTXSID': 'known', 'Endpoint': 'hit call', 'Response': '0'},
        {'DTXSID': 'known', 'Endpoint': 'point of departure', 'Response': '3'},
        {'DTXSID': 'unmapped', 'Endpoint': 'point of departure', 'Response': '5'},
    ]
    coverage, counts = assay_coverage(rows, {'known': 'full key'})
    assert coverage == {'known': {'hit call': 2, 'point of departure': 1}}
    assert counts == {'source_rows': 4, 'matched_rows': 3}
