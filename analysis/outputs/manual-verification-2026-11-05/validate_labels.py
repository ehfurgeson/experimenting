"""Check a working label CSV's structure only; no approval, model fitting or writes."""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import polars as pl

pack = Path(__file__).resolve().parent
root = pack.parents[2]
sys.path.insert(0, str(root / 'analysis'))
from labels import LABEL_FIELDS, attach_labels

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--labels', type=Path, default=pack / 'assays/reviewed_labels.csv')
args = parser.parse_args()
with args.labels.open(encoding='utf-8-sig', newline='') as stream:
    reader = csv.DictReader(stream)
    if len(reader.fieldnames or []) != len(LABEL_FIELDS) or set(reader.fieldnames or []) != LABEL_FIELDS:
        raise ValueError('Preserve exactly the seven label columns')
    labels = list(reader)
compounds = pl.read_parquet(root / 'analysis/outputs/chembl-review-screen-2026-10-29-final/structural_features.parquet').to_dicts()
if len(labels) != len(compounds) or {r['compound_id'] for r in labels} != {r['compound_id'] for r in compounds}:
    raise ValueError('Preserve all 154 original compound IDs exactly once')
attached = attach_labels(compounds, labels)
print('Rows:',len(attached))
print('Activity:',dict(Counter(r['activity_target'] for r in attached)))
print('Origin:',dict(Counter(r['origin_target'] for r in attached)))
print('Schema/identity-conflict checks passed. Scientific approval and assay comparability are NOT verified. No model fitted.')
