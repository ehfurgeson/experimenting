"""Reviewed summaries cannot manufacture inactivity or move historical LD50 bins."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reviewed_progress import GROUPS, describe, natural_group, reclassify_ld50


def test_unknown_activity_is_separate_from_bounded_low_response():
    assert natural_group({'natural_origin': 'natural', 'herbicidal_activity': 'unknown'}) == GROUPS[1]
    assert natural_group({'natural_origin': 'natural', 'herbicidal_activity': 'inactive'}) == GROUPS[2]
    assert natural_group({'natural_origin': 'unknown', 'herbicidal_activity': 'active'}) is None
    summary = describe([{'group': GROUPS[0], 'mw': 100, 'halogen_present': 0},
                        {'group': GROUPS[0], 'mw': 200, 'halogen_present': 1}])
    mw = next(r for r in summary if r['group'] == GROUPS[0] and r['feature'] == 'mw')
    assert mw['median'] == 150
    assert all(r['n'] == 0 and r['median'] is None for r in summary if r['group'] == GROUPS[2])


def test_identity_join_reannotates_groups_without_changing_values_or_bounds():
    baseline = [{'compound_id': 'epa', 'group': 'unreviewed_natural_product_selection',
                 'median_mg_kg': '520', 'ld50_bin': 'low', 'censored_records': '0'},
                {'compound_id': 'bounds', 'group': 'unreviewed_natural_product_selection',
                 'median_mg_kg': '', 'ld50_bin': '', 'censored_records': '2'}]
    selection = [{'compound_id': 'epa', 'structure_inchikey': 'exact-key'},
                 {'compound_id': 'bounds', 'structure_inchikey': 'another-key'}]
    members = [{'compound_id': 'reviewed', 'structure_inchikey': 'exact-key',
                'natural_origin': 'natural', 'group': GROUPS[0], 'activity_policy': 'bounded'}]
    result = reclassify_ld50(baseline, selection, members)
    assert result[0]['group'] == GROUPS[0] and result[0]['reviewed_compound_id'] == 'reviewed'
    assert result[0]['median_mg_kg'] == '520' and result[0]['ld50_bin'] == 'low'
    assert result[1]['median_mg_kg'] == '' and result[1]['ld50_bin'] == ''
    assert baseline[0]['group'] == 'unreviewed_natural_product_selection'
    baseline[0]['ld50_bin'] = 'high'
    with pytest.raises(ValueError, match = 'Historical LD50'):
        reclassify_ld50(baseline, selection, members)


@pytest.mark.parametrize('mutation', ['metrics', 'cohort', 'scaffold', 'labels'])
def test_saved_model_comparisons_require_consistent_predictions_and_folds(tmp_path, mutation):
    import csv

    from reviewed_progress import verify_model_predictions
    reports = [{'profile': p, 'target': 'provenance_comparator_target', 'status': 'evaluated',
                'n': 2, 'f1': 1, 'roc_auc': 1, 'balanced_accuracy': 1} for p in ('a','b')]
    oof = [{'profile': p, 'compound_id': c, 'fold': f, 'scaffold': c, 'label': y, 'probability': prob}
           for p in ('a','b') for c,f,y,prob in [('x',0,0,.2),('y',1,1,.8)]]
    if mutation == 'metrics':
        reports[0]['f1'] = .5
    elif mutation == 'cohort':
        oof[-1]['compound_id'] = 'different'
    elif mutation == 'scaffold':
        oof[-1]['scaffold'] = 'x'
    else:
        oof[-1]['label'] = 0
    for name, rows in [('reports.csv',reports),('oof.csv',oof)]:
        with (tmp_path/name).open('w',newline = '') as f:
            writer = csv.DictWriter(f,fieldnames = list(rows[0]));writer.writeheader();writer.writerows(rows)
    with pytest.raises(ValueError):
        verify_model_predictions(tmp_path)


def test_existing_output_is_refused_before_any_publication(tmp_path):
    from reviewed_progress import run
    existing = tmp_path/'existing';existing.mkdir()
    marker = existing/'preserve.txt';marker.write_text('preserve')
    with pytest.raises(ValueError,match = 'fresh output'):
        run(tmp_path/'adoption',tmp_path/'models',tmp_path/'baseline',tmp_path/'selection',existing)
    assert marker.read_text() == 'preserve'
