from catalog_hazard_review import comparison_rows, ld50_support, summarize_catalog


def test_cross_bin_reports_and_censored_points_stay_separate():
    rows = [
        {'status': 'exact', 'value_mg_kg': '1000', 'reference': 'source'},
        {'status': 'exact', 'value_mg_kg': '1000', 'reference': 'source'},
        {'status': 'exact', 'value_mg_kg': '2000', 'reference': 'other'},
        {'status': 'censored', 'value_mg_kg': '5000', 'reference': 'another'},
    ]
    evidence = ld50_support(rows)
    assert evidence['exact_point_records'] == 3
    assert evidence['distinct_exact_values'] == 2
    assert evidence['distinct_exact_reference_strings'] == 2
    assert evidence['censored_records'] == 1
    assert evidence['exact_report_bins'] == 'low;medium'


def test_catalog_membership_does_not_promote_an_origin_claim():
    measured = {'full_key': 'KEY', 'coconut_exact': 'True', 'npass_exact': 'False',
                'npass_taxon_reference_lead': 'True', 'hrac_name_lead': 'False',
                'ld50_bin': '0'}
    exact = {'status': 'exact', 'value_mg_kg': '100', 'reference': 'source'}
    row = summarize_catalog(measured, [exact], None)
    assert row['origin_review'] == 'unreviewed'
    assert row['screen_disposition'] == 'exclude_from_low_acute_lethality_shortlist'
    assert row['low_bin_report_agreement'] == 'all_exact_reports_low'


def test_lotus_links_track_doi_and_manual_validation_separately():
    leads = [{'full_key': 'one', 'npass_taxon_reference_lead': 'False'},
             {'full_key': 'two', 'npass_taxon_reference_lead': 'True'}]
    records = [{'structure_inchikey': 'one', 'reference_doi': '', 'manual_validation': 'Y'},
               {'structure_inchikey': 'one', 'reference_doi': ' doi ', 'manual_validation': ''}]
    one, two = comparison_rows(leads, records)
    assert one == {'full_key': 'one', 'npass_taxon_reference_lead': False,
                   'lotus_links': 2, 'lotus_rows_with_doi': 1, 'lotus_manual_validation_rows': 1}
    assert two == {'full_key': 'two', 'npass_taxon_reference_lead': True,
                   'lotus_links': 0, 'lotus_rows_with_doi': 0, 'lotus_manual_validation_rows': 0}
