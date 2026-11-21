"""Conditional whole-block randomization check for binary forest OOB F1."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

from data_sprint import read_csv, sha256
from evidence_models import SEED, merged_groups, toxicity_forest
from evidence_release import FEATURES, write_csv
from sprint_report import verify_bundle


def block_strata(groups):
    blocks = defaultdict(list)
    for index, group in enumerate(groups):
        blocks[group].append(index)
    sizes = defaultdict(list)
    for indexes in blocks.values():
        sizes[len(indexes)].append(indexes)
    return {size: np.asarray(members, dtype=int) for size, members in sorted(sizes.items())}


def permute_labels(labels, strata, rng):
    shuffled = labels.copy()
    for blocks in strata.values():
        if len(blocks) > 1:
            shuffled[blocks] = labels[blocks[rng.permutation(len(blocks))]]
    return shuffled


def randomization_pvalue(observed, null_scores):
    return (1 + sum(score >= observed for score in null_scores)) / (1 + len(null_scores))


def oob_f1(features, labels):
    model = toxicity_forest().set_params(oob_score=True).fit(features, labels)
    probability = model.oob_decision_function_
    if (list(model.classes_) != [0, 1] or not np.isfinite(probability).all()
            or not np.allclose(probability.sum(axis=1), 1.0)):
        raise ValueError('Binary OOB predictions must cover every structure')
    return float(f1_score(labels, probability[:, 1] >= .5, zero_division=0))


def evaluate(records, pathway, repeats):
    records = sorted(records, key=lambda row: row['full_key'])
    if len({row['full_key'] for row in records}) != len(records):
        raise ValueError('Each target cohort must have unique full structure keys')
    features = np.asarray([[float(row[field]) for field in FEATURES] for row in records])
    classes = [int(row['ld50_bin']) for row in records]
    labels = (np.asarray(classes) == 0).astype(int)
    if set(classes) - {0, 1, 2} or len(set(labels)) != 2 or not np.isfinite(features).all():
        raise ValueError('A finite two-class forest experiment is required')
    strata = block_strata(merged_groups(records))
    movable = [blocks for blocks in strata.values() if len(blocks) > 1]
    if not any(np.any(labels[blocks] != labels[blocks[0]]) for blocks in movable):
        raise ValueError('No exchangeable blocks can alter the target assignment')
    rng = np.random.default_rng(SEED)
    observed = oob_f1(features, labels)
    null = []
    for i in range(repeats):
        null.append(oob_f1(features, permute_labels(labels, strata, rng)))
        if (i + 1) % 10 == 0 or i + 1 == repeats:
            print(f'{pathway}: {i + 1} of {repeats} randomized refits', flush=True)
    return {
        'pathway': pathway, 'observed_oob_binary_f1': observed,
        'permutation_p_one_sided': randomization_pvalue(observed, null),
        'permutations': len(null), 'null_mean_f1': float(np.mean(null)),
        'null_max_f1': max(null), 'structures': len(labels),
        'structures_in_movable_size_strata': sum(blocks.size for blocks in movable),
        'structures_in_fixed_size_strata': len(labels) - sum(blocks.size for blocks in movable),
    }, null


def run(release, output, repeats=49):
    if repeats < 1:
        raise ValueError('Request at least one randomized refit')
    release, output = map(Path, (release, output))
    verify_bundle(release)
    output.mkdir(parents=True, exist_ok=False)
    sources = {p: release / f'{p}_compounds.csv' for p in ('A', 'B')}
    results = []
    for pathway, source in sources.items():
        result, null = evaluate(read_csv(source), pathway, repeats)
        result['p_bonferroni_two_pathways'] = min(1., 2 * result['permutation_p_one_sided'])
        results.append(result)
        write_csv(output / f'{pathway}_null_f1.csv',
                  [{'replicate': i, 'binary_oob_f1': score} for i, score in enumerate(null, 1)])
    write_csv(output / 'summary.csv', results)
    manifest = {
        'inputs': {str(p): sha256(p) for p in (*sources.values(), release / 'manifest.json')},
        'products': {p.name: sha256(p) for p in output.iterdir()},
        'seed': SEED, 'features': FEATURES, 'permutations': repeats,
        'null': 'Exchange whole scaffold/connectivity label vectors across equal-sized blocks.',
        'scope': 'Global binary OOB F1; tests conditional on equal-size block exchangeability.',
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=49)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
