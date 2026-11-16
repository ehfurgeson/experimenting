"""The proposal walkthrough must reject biological approval or model fitting claims."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expansion_report import build


@pytest.mark.parametrize('field', ['accepted_activity_labels','accepted_origin_labels','models_fitted'])
def test_report_does_not_silently_present_approved_or_fitted_results(tmp_path,field):
    roots = []
    for name in ('ecotox','toxicity','review','sources','cohort'):
        root = tmp_path/name
        root.mkdir()
        data = {'input_hashes':{},'output_hashes':{}}
        if name == 'review':
            data.update(accepted_activity_labels = 0, accepted_origin_labels = 0,models_fitted = 0)
            data[field] = 1
        (root/'manifest.json').write_text(json.dumps(data))
        roots.append(root)
    output = tmp_path/'output'
    with pytest.raises(ValueError,match = 'unapproved evidence'):
        build(*roots,output)
    assert not output.exists()
