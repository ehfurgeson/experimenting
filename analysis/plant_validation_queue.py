"""Choose a diverse research queue from measured-toxicity and occurrence gaps.

This is a proposed evidence/assay queue, not a calibrated active-learning policy
or an approved experimental protocol. No physical experiments are executed.
"""

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs

from accepted_plant_models import chemical_weights
from data_sprint import read_csv, sha256, write_csv
from plant_evidence_experiments import design_rows, model
from research_followup import GENERATOR
from sprint_report import verify_bundle


def pick_diverse(indices, fingerprints, selected, count):
    """Greedy maximum minimum fingerprint distance; input order resolves ties."""
    candidates = list(indices)
    chosen = []
    while candidates and len(chosen) < count:
        references = [fingerprints[i] for i in [*selected, *chosen]]
        scores = [1 - max(DataStructs.BulkTanimotoSimilarity(fingerprints[i], references))
                  if references else 1. for i in candidates]
        i = candidates.pop(int(np.argmax(scores)))
        chosen.append(i)
    return chosen


def run(experiments, prior, output):
    experiments, prior, output = map(Path, [experiments, prior, output])
    verify_bundle(experiments)
    verify_bundle(prior)
    paths = [experiments / 'combined_experimental_responses.csv',
             prior / 'natural_toxicity.csv', prior / 'lotus_occurrence_links.csv',
             prior / 'selection_screen.csv', experiments / 'manifest.json', prior / 'manifest.json']
    before = {str(p): sha256(p) for p in paths}
    training = [r for r in read_csv(paths[0]) if r['label'] != '']
    links = defaultdict(list)
    for r in read_csv(paths[2]):
        links[r['structure_inchikey']].append(r)
    herbicides = {r.get('full_key') or r['full_inchikey'] for r in read_csv(paths[3])
                  if r['selection_group'] == 'herbicide'}
    pool = [r for r in read_csv(paths[1]) if r['ld50_bin'] == '2' and not r['assumptions']
            and r['full_key'] in links and r['full_key'] not in herbicides
            and r['plant_evidence_band'] == 'no_plant_observations']
    pool.sort(key = lambda r: r['full_key'])
    if len(pool) < 24:
        raise ValueError('Insufficient qualified queue candidates; do not relax evidence rules silently')
    contexts = [{**r, 'plant_species': 'Lactuca sativa', 'endpoint': 'root_length',
                 'dose': '100', 'dose_unit': 'uM', 'duration': '120', 'duration_unit': 'h',
                 'reference_id': 'PROPOSED_NEW_STUDY'} for r in pool]
    x, query = design_rows(training), design_rows(contexts)
    y, w = np.array([int(r['label']) for r in training]), chemical_weights(training)
    probabilities = []
    for profile in ['chemistry', 'chemistry_context', 'chemistry_context_study']:
        fitted = model(profile).fit(x, y, logisticregression__sample_weight = w)
        if np.any(fitted[-1].n_iter_ >= fitted[-1].max_iter):
            raise ValueError('Logistic convergence failed')
        probabilities.append(fitted.predict_proba(query)[:, 1])
    probability = np.column_stack(probabilities)
    scores = np.median(probability, axis = 1)
    disagreement = np.ptp(probability, axis = 1)
    fingerprints = [GENERATOR.GetFingerprint(Chem.MolFromSmiles(r['smiles'])) for r in pool]
    train_fps = [GENERATOR.GetFingerprint(Chem.MolFromSmiles(r['smiles']))
                 for r in {r['full_key']: r for r in training}.values()]
    high = sorted(range(len(pool)), key = lambda i: (-scores[i], pool[i]['full_key']))
    selected = pick_diverse(high[:min(40, len(high))], fingerprints, [], 8)
    reasons = {i: 'higher_model_score_within_diverse_subset' for i in selected}
    uncertain = sorted((i for i in range(len(pool)) if i not in selected),
                       key = lambda i: (-disagreement[i], pool[i]['full_key']))
    chosen = pick_diverse(uncertain[:40], fingerprints, selected, 8)
    selected.extend(chosen)
    reasons.update({i: 'model_disagreement_probe_not_calibrated_uncertainty' for i in chosen})
    chosen = pick_diverse([i for i in range(len(pool)) if i not in selected], fingerprints, selected, 8)
    selected.extend(chosen)
    reasons.update({i: 'chemical_space_coverage' for i in chosen})
    queue = []
    for rank, i in enumerate(selected, 1):
        r = pool[i]
        refs = sorted({s['reference_doi'] for s in links[r['full_key']] if s['reference_doi']})
        queue.append({'priority': rank, 'full_key': r['full_key'], 'compound_name': r['compound_name'],
            'smiles': r['smiles'], 'selection_reason': reasons[i],
            'accepted_ld50_mg_kg': r['accepted_ld50_mg_kg'], 'toxicity_source_cohort': r['source_cohort'],
            'catalog_ids': r['catalog_ids'], 'lotus_rows': len(links[r['full_key']]),
            'lotus_doi_count': len(refs), 'occurrence_doi_examples': ';'.join(refs[:3]),
            'chemistry_probability': probability[i, 0], 'context_probability': probability[i, 1],
            'context_study_probability': probability[i, 2], 'model_score_median': scores[i],
            'model_score_range': disagreement[i],
            'nearest_plant_training_tanimoto': max(DataStructs.BulkTanimotoSimilarity(fingerprints[i], train_fps)),
            'proposed_context': 'Lactuca sativa root length;100uM;120h; hypothesis only',
            'queue_status': 'origin_form_chronic_hazard_solubility_review_required_before_assay',
            'interpretation': 'measured_acute_hazard_does_not_establish_human_safety; occurrence_link_not_biosynthesis'})
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'validation_queue.csv', queue, list(queue[0]))
    (output / 'proposed_assay_design.md').write_text('''# Proposed plant-validation design

This is a planning artifact; no compounds were purchased or physical assays run.
The 24 entries first require exact-form, biosynthetic-occurrence, chronic/non-target
hazard, availability and solubility review. Database links alone do not pass this gate.

Use the first assay round for a manageable subset of 8–12 reviewed compounds,
including a known phytotoxic comparator and explicit solvent/vehicle controls.
Choose concentration levels by solubility checks and range-finding, then collect
5–6 levels bracketing the observed response where feasible. Start with one
standard species and endpoint (for example lettuce root elongation); confirm hits
in a relevant weed and assess crop/non-target effects in a separate experiment.

Randomize treatment positions, record blinded image measurements where practical,
and use independent dishes/runs as replicate units, not individual seeds sharing
a dish. Use pilot variance to choose replication. Retain raw root lengths,
germination counts, control outcomes, precipitation, pH, vehicle, duration,
temperature and compound form. Do not turn failed germination or precipitation
into an unqualified compound potency measurement.

The selection algorithm combines model-score, disagreement and fingerprint-diversity
probes. Its value has not been validated prospectively; all model scores are
uncalibrated exploratory full fits with weak publication transfer. This design
does not claim OECD guideline compliance or establish a human-safety threshold.
''')
    shutil.copyfile(__file__, output / Path(__file__).name)
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Queue input changed')
    manifest = {'inputs': before, 'eligible_pool': len(pool), 'queue_compounds': len(queue),
        'selection_policy': 'Eight diverse higher-score, eight diverse disagreement, eight max-min '
                            'diversity candidates; source-asserted exact high-class toxicity, LOTUS '
                            'links, no existing plant labels, exclude original herbicide selection.',
        'limits': 'Catalog origin and occurrence links remain review-only; no laboratory work, '
                  'validated active-learning gain, calibrated uncertainty or safety claim.',
        'products': {str(p.relative_to(output)): sha256(p) for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return {'eligible_pool': len(pool), 'queue_compounds': len(queue)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['experiments', 'prior', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.experiments, args.prior, args.output), indent = 2))
