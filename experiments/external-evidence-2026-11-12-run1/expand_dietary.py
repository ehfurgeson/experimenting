"""Use the established credential location without logging or copying it."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path('analysis').resolve()))
from expand_test_evidence import expand

for line in Path('.env').read_text().splitlines():
    name, sep, value = line.partition('=')
    if sep and name.strip() == 'COMPTOX_API_KEY':
        os.environ['COMPTOX_API_KEY'] = value.strip().strip('"').strip("'")
        break
result = expand('analysis/outputs/dietary-review-2026-11-04-final/features.parquet',
                'experiments/external-evidence-2026-11-12-run1/dietary-test-v1')
print(result['states'])
