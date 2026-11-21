import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import f1_score, mean_absolute_error

from joint_catalog_diagnostics import oob_importance


@pytest.mark.parametrize('classifier', [True, False])
def test_oob_permutation_reproduces_builtin_oob_baseline(classifier):
    signal = np.tile(np.arange(3), 30)
    x = np.column_stack((signal, np.ones(len(signal))))
    model = (RandomForestClassifier if classifier else RandomForestRegressor)(
        n_estimators=40, random_state=8, bootstrap=True, oob_score=True).fit(x, signal)
    if classifier:
        baseline = f1_score(signal, model.oob_decision_function_.argmax(axis=1), average='macro')
    else:
        baseline = mean_absolute_error(signal, model.oob_prediction_)
    result = list(oob_importance(model, x, signal, ['signal', 'constant'],
                                 'classification' if classifier else 'regression'))
    assert result[0]['baseline'] == pytest.approx(baseline)
    assert result[0]['mean_performance_loss'] > 0
    assert result[1]['mean_performance_loss'] == 0
    assert result[0]['rows_with_oob_votes'] == len(signal)
