"""Check proposed labels against a frozen identity-hold audit; never approve labels or fit models."""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import polars as pl

from labels import LABEL_FIELDS, attach_labels
from verification_release import reject_held_activity


def validate(labels, features, audit):
    audit = Path(audit)
    manifest = json.loads((audit / 'manifest.json').read_text())
    holds = audit / 'identity_holds.csv'
    recorded = [v for k, v in manifest['output_hashes'].items() if Path(k).name == holds.name]
    if len(recorded) != 1 or hashlib.sha256(holds.read_bytes()).hexdigest() != recorded[0]:
        raise ValueError('Identity-hold hash mismatch')
    with Path(labels).open(encoding = 'utf-8-sig', newline = '') as stream:
        reader = csv.DictReader(stream)
        if len(reader.fieldnames or []) != len(LABEL_FIELDS) or set(reader.fieldnames or []) != LABEL_FIELDS:
            raise ValueError('Preserve exactly the seven label columns')
        proposed = list(reader)
    with holds.open(newline = '') as stream:
        hold_ids = {r['compound_id'] for r in csv.DictReader(stream)}
    compounds = pl.read_parquet(features).to_dicts()
    if len(proposed) != len(compounds) or {r['compound_id'] for r in proposed} != {r['compound_id'] for r in compounds}:
        raise ValueError('Preserve all frozen compound IDs exactly once')
    if not hold_ids <= {r['compound_id'] for r in compounds}:
        raise ValueError('Audit holds and feature cohort disagree')
    reject_held_activity(proposed, hold_ids)
    attached = attach_labels(compounds, proposed)
    return {'rows': len(attached), 'identity_holds': sorted(hold_ids),
            'activity_targets': dict(Counter(str(r['activity_target']) for r in attached)),
            'scientific_approval_verified': False, 'models_fitted': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--labels', type = Path, required = True)
    parser.add_argument('--features', type = Path, required = True)
    parser.add_argument('--audit', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(validate(args.labels, args.features, args.audit), indent = 2))
