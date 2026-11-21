import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_report import CORRECTED, require_corrected_release


def test_report_guard_requires_corrected_counts_not_the_retracted_run():
    assert CORRECTED['plant_observations'] == 733
    assert CORRECTED['all_three_structures'] == 49
    assert CORRECTED['plant_observations'] != 2260
    assert CORRECTED['all_three_structures'] != 120
    require_corrected_release(733, 49)
    with pytest.raises(ValueError, match = 'Retracted'):
        require_corrected_release(2260, 120)
    with pytest.raises(ValueError, match = 'corrected'):
        require_corrected_release(733, 50)
