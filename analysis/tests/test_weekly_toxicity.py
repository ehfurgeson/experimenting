"""Rat oral eligibility, provenance, censoring and pooled bins."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from weekly_toxicity import summarize


def record(cid, value, **changes):
    return {'compound_id': cid, 'dtxsid': cid, 'toxval_type': 'LD50',
            'value_numeric': value, 'value_units': 'mg/kg', 'qualifier': '=',
            'latin_name': 'Rattus norvegicus', 'species_supercategory': 'Mammals',
            'exposure_route': 'oral', 'study_type': 'acute', 'experimental_record': 'experimental',
            'reference': 'Study A', 'source': 'EPA', 'retrieved_at': '2026-11-10', **changes}


def pilot(rows, labels = ()):
    ids = sorted({r['compound_id'] for r in rows})
    crosswalk = [{'compound_id': cid, 'dtxsid': cid, 'status': 'approved'} for cid in ids]
    traits = [{'compound_id': cid, 'chemical_group': 'natural_product'} for cid in ids]
    return summarize(rows, crosswalk, traits, labels)


def test_conversions_context_and_censoring():
    result = pilot([record('a', 1, value_units = 'g/kg'), record('a', 1000, source = 'Other source'),
                    record('b', 3000, qualifier = '>'), record('c', 1, value_units = 'mg/L'),
                    record('d', 4, latin_name = 'Mus musculus'),
                    record('e', 5, exposure_route = 'dermal'),
                    record('f', 6, experimental_record = 'predicted'),
                    record('g', 7, study_type = 'chronic')])
    assert [r['status'] for r in result['evidence']] == [
        'exact', 'duplicate', 'censored', *['excluded'] * 5]
    assert result['compounds'][0]['median_mg_kg'] == 1000
    assert result['compounds'][1]['ld50_bin'] is None
    assert result['policy']['collapsed_cutoffs']
    assert all(r['natural_origin'] == 'unknown' for r in result['inventory'])


def test_ties_stay_together_and_median_has_one_compound_vote():
    result = pilot([record('a', 10), record('a', 30, reference = 'Study B'),
                    record('b', 20), record('c', 30), record('d', 40)])
    assert result['policy']['cutoffs'] == [20, 30]
    assert [r['ld50_bin'] for r in result['compounds']] == ['low', 'low', 'medium', 'high']
    assert result['compounds'][0]['discordant_exact_values']
    reordered = pilot([record('d', 40), record('c', 30), record('b', 20),
                       record('a', 30, reference = 'Study B'), record('a', 10)])
    assert result['compounds'] == reordered['compounds']
    assert result['policy'] == reordered['policy']


def test_identity_and_activity_are_independent_and_validated():
    row = record('a', 10)
    assert summarize([row], [], [{'compound_id': 'a'}])['compounds'] == []
    result = pilot([row], [{'compound_id': 'a', 'natural_origin': 'natural',
                           'origin_reference': 'isolation study'}])
    assert result['inventory'][0]['herbicidal_activity'] == 'unknown'
    assert result['compounds'][0]['group'] == 'unreviewed_natural_product_selection'
    with pytest.raises(ValueError, match = 'activity_reference'):
        pilot([row], [{'compound_id': 'a', 'herbicidal_activity': 'inactive'}])


def test_empty_exact_population_has_no_invented_cutoffs():
    result = pilot([record('a', 1000, qualifier = '>')])
    assert result['policy']['cutoffs'] == []
    assert result['policy']['bin_status'] == 'no_exact_compounds'
    assert all(r['proportion'] is None for r in result['groups'])
