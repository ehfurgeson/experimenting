from io import BytesIO
from zipfile import ZipFile

from evidence_release import structure
from nice_assay_model import assay_calls
from nice_endpoint_models import aggregate, target_value
from npass_label_model import source_links, trusted_labels


def test_nice_keeps_inactive_distinct_from_omitted_and_interfering_calls():
    assay_data = (
        'DTXSID\tAssay\tEndpoint\tResponse\tResponseUnit\tRecordID\n'
        'one\tgood\tCall\tInactive\tunitless\t1\n'
        'one\tomit\tCall\tQC-Omit\tunitless\t2\n'
        'one\tomit\tAC50\t1.2\tuM\t2\n'
        'one\tflagged\tCall\tActive\tunitless\t3\n'
        'one\tflagged\tAC50\t1.2\tuM\t3\n'
        'one\tconflict\tCall\tActive\tunitless\t4\n'
        'two\tconflict\tCall\tInactive\tunitless\t5\n'
        'one\tactive\tCall\tActive\tunitless\t6\n'
        'one\tactive\tAC50\t100\tuM\t6\n'
    )
    flags = ('DTXSID\tAssay\tInterference Flags\n'
             'one\tflagged\tblue (experimental)\n')
    package = BytesIO()
    with ZipFile(package, 'w') as archive:
        for name, data in (('cHTS_InterferenceFlags.zip', flags), ('cHTS_DataDownload.zip', assay_data)):
            member = BytesIO()
            with ZipFile(member, 'w') as nested:
                nested.writestr('data.tsv', data)
            archive.writestr(name, member.getvalue())
    potency = {}
    with ZipFile(package) as archive:
        calls, counts = assay_calls(archive, {'one': 'structure', 'two': 'structure'}, potency)
    assert calls == {('structure', 'good'): 0, ('structure', 'active'): 1}
    assert potency == {('structure', 'active'): 4.}
    assert counts['interference_omitted_rows'] == 1
    assert counts['omitted_structure_assay_pairs'] == 2


def test_npass_join_preserves_censoring_and_normalizes_mass_units():
    npass = {'endpoint': 'LD50', 'test_species': 'Rattus norvegicus', 'full_inchikey': 'key',
             'unit': 'g/Kg', 'value': '5', 'qualifier': '>', 'source_record_id': 'n',
             'citation': 'Database:ToxVal'}
    epa = {'full_inchikey': 'key', 'value': '5000', 'qualifier': '=',
           'source_record_id': 'e', 'source_chemical_name': 'example', 'source_table': 'EPA',
           'status': 'endpoint_eligible_exact', 'source_study_id': 's', 'citation': '',
           'source_url': '', 'tested_form': ''}
    bound = {**epa, 'qualifier': '>', 'status': 'endpoint_eligible_censored',
             'source_record_id': 'bound'}
    leads, matches, exact = source_links([npass], [epa, bound], set())
    assert leads[0]['normalized_mg_kg'] == 5000
    assert [r['epa_record'] for r in matches] == ['bound']
    assert exact['key'] == {5000}


def test_trusted_npass_bounds_assign_a_class_without_inventing_a_point():
    key = structure('CCCCCC')['full_key']
    identity = {'full_inchikey': key, 'identity_status': 'valid', 'original_structure': 'CCCCCC'}
    leads = [{'full_inchikey': key, 'normalized_mg_kg': 3400., 'qualifier': '>'}]
    labels, _ = trusted_labels(leads, [identity])
    assert [(r['ld50_bin'], r['dose_mg_kg']) for r in labels] == [(2, None)]
    labels, decisions = trusted_labels([{**leads[0], 'qualifier': '>='}], [identity])
    assert not labels
    assert decisions[0]['disposition'] == 'ambiguous_or_conflicting_bounds'


def test_other_endpoint_aggregation_keeps_numeric_units_and_binary_disagreement():
    assert target_value({'Response': '3', 'Response_Modifier': '>'}, 'mg/L', None) is None
    assert target_value({'Response': 'Positive; Negative'}, 'binary', {'Positive': 1, 'Negative': 0}) is None
    rows = [{'endpoint': 'irritation', 'full_key': 'one', 'unit': 'binary', 'value': v} for v in (0, 1)]
    rows += [{'endpoint': 'inhalation', 'full_key': 'one', 'unit': 'mg/L', 'value': v} for v in (1, 100)]
    cohorts, conflicts = aggregate(rows)
    assert set(cohorts) == {'inhalation'} and cohorts['inhalation'][0]['target'] == 1.
    assert [r['endpoint'] for r in conflicts] == ['irritation']
