"""Independently check the follow-up pilot and render compact scientific products."""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import altair as alt
import numpy as np
from sklearn.metrics import f1_score

from accepted_plant_models import chemical_weights
from data_sprint import read_csv, sha256, write_csv
from research_followup import catalog_exact_hit
from sprint_report import verify_bundle


def run(pilot, accepted, output):
    pilot, accepted, output = map(Path, [pilot, accepted, output])
    manifest = verify_bundle(pilot)
    inputs = [pilot / 'manifest.json', *[pilot / f'{n}.csv' for n in [
        'metrics', 'predictions', 'split_membership', 'selection_screen', 'natural_toxicity',
        'analogues', 'lotus_occurrence_links', 'paired_intervals', 'coefficients']],
        accepted / 'plant-models-v5/metrics.csv', accepted / 'toxicity-models-v2/metrics.csv',
        accepted / 'integrated-screen-v5/candidate_screen.csv',
        accepted / 'toxicity-v2/all_accepted_exact_compounds.csv',
        accepted / 'toxicity-v2/frozen_A_compounds.csv']
    before = {str(p): sha256(p) for p in inputs}
    metrics, predictions, splits, selection, natural, analogues, lotus, _intervals, coefficients = [
        read_csv(pilot / f'{n}.csv') for n in ['metrics', 'predictions', 'split_membership',
            'selection_screen', 'natural_toxicity', 'analogues', 'lotus_occurrence_links',
            'paired_intervals', 'coefficients']]
    frozen = {r['full_key'] for r in read_csv(accepted / 'toxicity-v2/frozen_A_compounds.csv')}
    grouped = defaultdict(list)
    for r in predictions:
        grouped[r['task'], r['protocol'], r['profile']].append(r)
    for r in metrics:
        rs = grouped[r['task'], r['protocol'], r['profile']]
        rs = [p for p in rs if p['full_key'] in frozen] if r['task'] == 'toxicity' else rs
        assert len({p['row_id'] for p in rs}) == len(rs)
        weight = chemical_weights(rs) if r['task'] == 'plant' else None
        value = f1_score([int(p['observed']) for p in rs], [int(p['predicted']) for p in rs],
                         labels = list(range(2 if r['task'] == 'plant' else 3)),
                         average = 'macro', sample_weight = weight, zero_division = 0)
        assert abs(value - float(r['macro_f1'])) < 1e-12
    assignments = {}
    for r in splits:
        group = r['task'], r['protocol'], r['group']
        assert group not in assignments or assignments[group] == r['fold']
        assignments[group] = r['fold']
    historical_plant = read_csv(accepted / 'plant-models-v5/metrics.csv')
    historical_tox = read_csv(accepted / 'toxicity-models-v2/metrics.csv')
    for r in metrics:
        if not r['profile'].startswith('descriptor7_'):
            continue
        profile = r['profile'].split('_')[1]
        if r['task'] == 'plant':
            baseline = [p for p in historical_plant if p['scenario'] == 'quantitative_only'
                and p['protocol'] == r['protocol'] and p['profile'] == profile
                and p['source'] == 'all_sources' and p['weighting'] == 'equal_structure']
        else:
            baseline = [p for p in historical_tox if p['scenario'] == 'all_accepted'
                and p['evaluation_stratum'] == 'frozen_A' and p['profile'] == profile
                and p['task'] == 'classification']
        assert len(baseline) == 1
        assert abs(float(baseline[0]['macro_f1']) - float(r['macro_f1'])) < 1e-12
    classes = Counter(r['ld50_bin'] for r in natural)
    exact = {r['full_key']: r for r in read_csv(accepted / 'toxicity-v2/all_accepted_exact_compounds.csv')}
    screen = read_csv(accepted / 'integrated-screen-v5/candidate_screen.csv')
    expected = {r['full_key'] for r in screen if catalog_exact_hit(r) and r['full_key'] in exact}
    assert {r['full_key'] for r in natural} == expected
    assert classes == Counter(exact[key]['ld50_bin'] for key in expected)
    selection_bykey = {r['full_key']: r for r in selection if r.get('full_key')}
    natural_bykey = {r['full_key']: r for r in natural}
    annotated = []
    for r in analogues:
        query, analogue = selection_bykey[r['query_full_key']], natural_bykey[r['analogue_full_key']]
        assert query['full_key'][:14] != analogue['full_key'][:14]
        assert float(analogue['target_log10_mg_kg']) >= np.log10(3400)
        annotated.append({**r, 'query_name': query['compound_name'], 'analogue_name': analogue['compound_name'],
            'query_smiles': query['original_structure'], 'analogue_smiles': analogue['smiles'],
            'source_cohort': analogue['source_cohort'], 'toxicity_context_assumptions': analogue['assumptions'],
            'plant_evidence_band': analogue['plant_evidence_band'],
            'similarity_interpretation': 'finite_radius_binary_fingerprint; score_1_is_not_structure_identity'})
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'annotated_analogues.csv', annotated, list(annotated[0]))
    summarized = defaultdict(list)
    for r in coefficients:
        summarized[r['task'], r['protocol'], r['profile'], r['class'], r['feature']].append(
            float(r['standardized_weight']))
    coef_summary = [{'task': key[0], 'protocol': key[1], 'profile': key[2], 'class': key[3],
        'feature': key[4], 'mean_standardized_weight': float(np.mean(values)),
        'fold_sd': float(np.std(values)), 'folds': len(values)} for key, values in summarized.items()]
    write_csv(output / 'logistic_weight_summary.csv', coef_summary, list(coef_summary[0]))
    labels = {'descriptor7_logistic': '7 descriptors · logistic', 'descriptor7_forest': '7 descriptors · forest',
              'chemistry_logistic': '13 descriptors · logistic', 'chemistry_forest': '13 descriptors · forest',
              'morgan_logistic': 'Morgan 2048 · logistic'}
    chart_rows = [{**r, 'macro_f1': float(r['macro_f1']), 'model': labels[r['profile']],
                   'panel': 'Toxicity · same frozen A' if r['task'] == 'toxicity' else 'Plant · ' + r['protocol']}
                  for r in metrics]
    chart = alt.Chart(alt.Data(values = chart_rows)).mark_bar().encode(
        x = alt.X('macro_f1:Q', scale = alt.Scale(domain = [0, 1]), title = 'Protected macro-F1'),
        y = alt.Y('model:N', sort = list(labels.values()), title = None),
        color = alt.Color('model:N', legend = None), row = alt.Row('panel:N', title = None)
    ).properties(width = 570, height = 145, title = 'Fixed representation pilots · no hyperparameter search')
    hazard_rows = [{'LD50 class': name, 'structures': classes[str(i)]} for i, name in enumerate([
        'Low ≤1080 mg/kg', 'Medium >1080 to 3400 mg/kg', 'High >3400 mg/kg'])]
    hazard = alt.Chart(alt.Data(values = hazard_rows)).mark_bar(color = '#366c78').encode(
        x = alt.X('structures:Q', title = 'Catalog-matched structures with accepted exact toxicity'),
        y = alt.Y('LD50 class:N', sort = [r['LD50 class'] for r in hazard_rows], title = None)
    ).properties(width = 570, height = 140, title = 'Catalog membership is provisional origin evidence')
    import vl_convert as vlc
    for name, figure in [('protected_models', chart), ('natural_catalog_toxicity', hazard)]:
        (output / f'{name}.svg').write_text(vlc.vegalite_to_svg(figure.to_dict()))
        (output / f'{name}.png').write_bytes(vlc.vegalite_to_png(figure.to_dict(), scale = 2))
    verification = {'pilot_product_hashes_verified': len(manifest['products']),
        'independently_recomputed_metrics': len(metrics), 'reproduced_historical_baselines': 6,
        'all_groups_confined_to_one_test_fold': True, 'selection_rows': len(selection),
        'scored_selection_rows': sum(r['screen_coverage'] == 'scored' for r in selection),
        'natural_class_counts': dict(classes), 'plant_bands': dict(Counter(r['plant_evidence_band'] for r in natural)),
        'lotus_rows': len(lotus), 'lotus_full_keys': len({r['structure_inchikey'] for r in lotus}),
        'lotus_provider_manual_validation_Y_rows': sum(r['manual_validation'] == 'Y' for r in lotus),
        'analogue_pairs': len(analogues), 'analogue_pairs_tanimoto_ge_0_6': sum(float(r['morgan_tanimoto']) >= .6 for r in analogues),
        'canonical_bin_edges': 'low <=1080; medium >1080 and <=3400; high >3400 mg/kg',
        'metadata_note': 'Computed classes follow upstream ld50_bin: low <=1080, medium >1080 and '
                         '<=3400, high >3400 mg/kg. Analogue threshold >=3400 is a queue criterion, '
                         'not exactly the >3400 high-class boundary.',
        'limits': 'Verifies computation under accepted-source assumptions, not biological truth.'}
    (output / 'verification.json').write_text(json.dumps(verification, indent = 2) + '\n')
    shutil.copyfile(__file__, output / Path(__file__).name)
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Inputs changed')
    result = {'inputs': before, 'products': {str(p.relative_to(output)): sha256(p)
              for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return verification


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['pilot', 'accepted', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.pilot, args.accepted, args.output), indent = 2))
