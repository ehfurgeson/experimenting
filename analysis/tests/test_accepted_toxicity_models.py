import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from accepted_toxicity_models import fixed_partitions


def test_matched_partitions_keep_transitive_connectivity_and_scaffolds_together():
    rows = [{'connectivity': f'C{i}', 'scaffold': f'S{i}'} for i in range(12)]
    rows += [{'connectivity': 'C0', 'scaffold': 'S1'},
             {'connectivity': 'C1', 'scaffold': 'S2'}]
    groups, fold = fixed_partitions(rows)
    assert groups[0] == groups[1] == groups[2] == groups[-1] == groups[-2]
    assert len(set(fold)) == 5 and np.all(fold >= 0)
    for held in range(5):
        assert not set(groups[fold == held]) & set(groups[fold != held])
