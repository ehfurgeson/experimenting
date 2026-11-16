"""Inequality boundary semantics and explicit duplicate-review requirements."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expansion_toxicity import (
    adopt_duplicate_decisions,
    compatible_bins,
    duplicate_exclusions,
    publication,
    scenario,
)


@pytest.mark.parametrize('value,operator,expected', [
    (1080, '>', ['medium', 'high']), (1080, '>=', ['low', 'medium', 'high']),
    (3400, '>', ['high']), (3400, '>=', ['medium', 'high']),
    (1080, '<', ['low']), (1080, '<=', ['low']), (3400, '<', ['low', 'medium']),
    (3401, '<', ['low', 'medium', 'high']), (1080, '=', ['low']), (3400, '=', ['medium']),
])
def test_censored_observation_bins_preserve_strict_boundaries(value, operator, expected):
    assert compatible_bins(value, operator) == expected


def test_only_signed_approved_source_duplicate_decisions_exclude():
    queue = [{'pair_id': 'pair', 'left_id': 'EPA:a', 'right_id': 'ECOTOX:b',
              'identity_link_status': 'candidate'}]
    assert duplicate_exclusions(queue, []) == set()
    decision = {'pair_id': 'pair', 'decision': 'same_observation', 'retain_id': 'EPA:a'}
    with pytest.raises(ValueError, match = 'signed'):
        duplicate_exclusions(queue, [decision])
    decision.update(reviewer = 'Reviewer', review_date = '2026-11-11', decision_reference = 'Paper Table 1')
    with pytest.raises(ValueError, match = 'identity approval'):
        duplicate_exclusions(queue, [decision])
    queue[0]['identity_link_status'] = 'approved'
    assert duplicate_exclusions(queue, [decision]) == {'ECOTOX:b'}
    with pytest.raises(ValueError, match = 'known unique'):
        duplicate_exclusions(queue, [decision, decision])


def test_publication_matching_never_uses_missing_titles_or_dois():
    assert publication('', '-') is None
    assert publication('https://doi.org/10.1000/Test.', '') == 'doi:10.1000/test'


def test_queue_adoption_rejects_unknown_duplicate_pairs_and_conflicting_retention():
    queue = [{'pair_id': 'a|b', 'left_id': 'a', 'right_id': 'b', 'identity_link_status': 'approved'},
             {'pair_id': 'b|c', 'left_id': 'b', 'right_id': 'c', 'identity_link_status': 'approved'}]
    def decision(pair_id, keep):
        return {'pair_id': pair_id, 'decision': 'same_observation', 'retain_id': keep,
                'reviewer': 'Fixture', 'review_date': '2026-11-12', 'decision_reference': 'Table'}
    with pytest.raises(ValueError, match = 'Conflicting'):
        adopt_duplicate_decisions(queue, [decision('a|b', 'a'), decision('b|c', 'b')])
    with pytest.raises(ValueError, match = 'known unique'):
        adopt_duplicate_decisions(queue, [decision('missing', 'a')])
    with pytest.raises(ValueError, match = 'unique pair'):
        adopt_duplicate_decisions([queue[0], queue[0]], [])


def test_compound_medians_give_each_compound_one_tertile_vote():
    rows = [{'compound_id': 'a', 'status': 'exact', 'value_mg_kg': x} for x in (100,300)]
    rows += [{'compound_id': 'b', 'status': 'censored', 'value_mg_kg': 5000}]
    compounds, report = scenario(rows, 'test', [1080.,3400.])
    assert len(compounds) == 1 and compounds[0]['median_mg_kg'] == 200
    assert report['cohort_tertiles'] == [200.,200.]
    assert report['fixed_cutoffs'] == [1080.,3400.]
