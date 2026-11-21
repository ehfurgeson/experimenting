"""Join the frozen plant and toxicity catalog predictions by full InChIKey."""

import argparse
import json
from pathlib import Path

import polars as pl

from data_sprint import sha256
from sprint_report import verify_bundle

SCORE_CUTOFF = 0.5
ROOT_CUTOFF = 40
ORAL_HIGH_CUTOFF = 3400
RESOURCES = Path(__file__).with_name('resources') / 'joint-reproduction'


def screening_flags(endpoints):
    ice_high = (pl.col('ice_oral_bin') == 2) & pl.col('ice_reviewed_lower_bound_mg_kg').is_null()
    ice_missing = pl.col('ice_oral_bin').is_null()
    high_plant = pl.col('pooled_high_response_score') >= SCORE_CUTOFF
    oral_models = [pl.col(f'oral_{p}__high') >= SCORE_CUTOFF for p in ('A', 'B', 'augmented')]
    root_high = pl.any_horizontal(pl.col(f'{plant}_root_length_100um__inhibition_pct') >= ROOT_CUTOFF
                                  for plant in ('radish', 'cress'))
    binary = [r['endpoint'] for r in endpoints if r['task'] == 'binary']
    observed_positive = [(pl.col(f'{e}__observed') == 1).fill_null(False) for e in binary]
    predicted_positive = [pl.col(f'{e}__observed').is_null() & (pl.col(f'{e}__score') >= SCORE_CUTOFF)
                          for e in binary]
    return [
        ice_high.fill_null(False).alias('measured_oral_high'),
        high_plant.alias('pooled_plant_score_ge_half'),
        root_high.alias('root_inhibition_ge_40_at_100um'),
        (ice_missing & high_plant & pl.all_horizontal(oral_models[:2])).fill_null(False).alias('joint_model_ab'),
        (ice_missing & high_plant & pl.all_horizontal(oral_models)).fill_null(False).alias('joint_model_all_three'),
        (ice_missing & root_high & pl.all_horizontal(oral_models)).fill_null(False).alias('root_and_oral_models'),
        pl.sum_horizontal(observed_positive).alias('observed_positive_binary_endpoints'),
        pl.sum_horizontal(predicted_positive).alias('unmeasured_binary_model_flags'),
        pl.sum_horizontal(pl.col(f'{e}__observed').is_not_null() for e in binary).alias('measured_binary_endpoints'),
    ]


def run(root, training, output, review=RESOURCES / 'reviewed-plant-context.csv'):
    tox, plant, oral = (root / name for name in ('catalog-bulk-public-v1', 'catalog-plant-activity-v3',
                                                'public-cohorts-v2'))
    for folder in (tox, plant, oral):
        verify_bundle(folder)
    training_manifest = training.with_name('manifest.json')
    if sha256(training) != json.loads(training_manifest.read_text())['products'][training.name]:
        raise ValueError('Plant training data do not match the original release')
    toxicity = pl.read_parquet(tox / 'catalog_scores.parquet')
    plants = pl.read_parquet(plant / 'plant_scores.parquet').drop('name')
    joint = toxicity.join(plants, on='full_key', validate='1:1', maintain_order='left')
    if joint.height != toxicity.height or joint.height != plants.height:
        raise ValueError('The plant and toxicity catalog key sets differ')
    reports = pl.read_csv(oral / 'A_observations.csv', infer_schema_length=0).filter(pl.col('status') == 'exact')
    reports = reports.with_columns(pl.col('value_mg_kg').cast(pl.Float64))
    review_path = RESOURCES / 'oral-qualifier-review.csv'
    bounds = pl.read_csv(review_path)
    matched_bounds = reports.join(bounds, on=['full_key', 'source_record_id'], validate='m:1')
    if (matched_bounds.height != bounds.height
            or not matched_bounds.select((pl.col('value_mg_kg') == pl.col('ice_reviewed_lower_bound_mg_kg')).all()).item()
            or reports.join(bounds.select('full_key'), on='full_key').height != bounds.height):
        raise ValueError('The reviewed bound must match the sole frozen exact report for its structure')
    joint = joint.join(bounds.select('full_key', 'ice_reviewed_lower_bound_mg_kg'), on='full_key',
                       validate='1:1', how='left', maintain_order='left')
    endpoints = pl.read_csv(tox / 'endpoint_summary.csv').to_dicts()
    joint = joint.with_columns(screening_flags(endpoints))
    measured = joint.filter('measured_oral_high')
    measured_model = measured.filter('pooled_plant_score_ge_half')
    predicted = joint.filter('joint_model_all_three')
    keys = ['full_key', 'name', 'ice_oral_ld50_mg_kg', 'pooled_high_response_score']
    observed = (pl.read_csv(training).filter((pl.col('label_kind') == 'quantitative') & (pl.col('label') == 1))
                .join(measured.select(keys), on='full_key', validate='m:1'))
    reviewed = (pl.read_csv(review, infer_schema_length=0)
                .filter(pl.col('plant_evidence').is_not_null() | pl.col('doi').is_not_null())
                .join(measured.drop('name'), on='full_key', validate='m:1'))
    measured_ranges = (reports.group_by('full_key').agg(
        pl.col('value_mg_kg').min().alias('ice_exact_min_mg_kg'),
        pl.col('value_mg_kg').max().alias('ice_exact_max_mg_kg'), pl.len().alias('ice_exact_reports'),
        (pl.col('value_mg_kg') <= ORAL_HIGH_CUTOFF).sum().alias('ice_exact_reports_at_or_below_high_cutoff')))
    measured = measured.join(measured_ranges, on='full_key', validate='1:1')
    output.mkdir(parents=True, exist_ok=False)
    joint.write_parquet(output / 'joint_scores.parquet')
    measured.sort(['pooled_high_response_score', 'full_key'], descending=[True, False]).write_csv(
        output / 'measured_high_oral.csv')
    predicted.sort(['pooled_high_response_score', 'full_key'], descending=[True, False]).write_parquet(
        output / 'model_only_overlap.parquet')
    observed.write_csv(output / 'quantitative_plant_evidence.csv')
    reviewed.write_csv(output / 'reviewed_plant_evidence.csv')
    profile = []
    for group, entries in [('catalog', joint), ('high_measured_oral_high_plant_model', measured_model),
                           ('joint_model_only_all_three', predicted)]:
        for e in endpoints:
            prefix = e['endpoint']
            value = pl.col(prefix + '__observed')
            score = pl.col(prefix + '__score')
            binary = e['task'] == 'binary'
            profile.append({'group': group, 'endpoint': prefix, 'unit': e['output_unit'],
                            'entries': entries.height, 'scored': entries.height - entries[score.meta.output_name()].null_count(),
                            'observed': entries.select(value.is_not_null().sum()).item(),
                            'observed_positive': entries.select((value == 1).sum()).item() if binary else None,
                            'unmeasured_model_flags': entries.select(
                                (value.is_null() & (score >= SCORE_CUTOFF)).sum()).item() if binary else None,
                            'outside_descriptor_ranges': entries.select(
                                (pl.col(prefix + '__outside_descriptor_ranges') > 0).sum()).item()})
    pl.DataFrame(profile).write_csv(output / 'endpoint_coverage.csv')
    counts = {
        'catalog_structures': joint.height, 'measured_high_oral': measured.height,
        'reviewed_oral_lower_bounds': matched_bounds.height,
        'measured_high_oral_with_report_at_or_below_cutoff': measured.filter(
            pl.col('ice_exact_reports_at_or_below_high_cutoff') > 0).height,
        'measured_high_oral_high_pooled_plant': measured_model.height,
        'measured_high_oral_high_root_prediction': measured.filter('root_inhibition_ge_40_at_100um').height,
        'measured_high_oral_quantitative_plant_high_structures': observed['full_key'].n_unique(),
        'measured_high_oral_reviewed_plant_structures': reviewed['full_key'].n_unique(),
        'model_only_ab_high_pooled_plant': joint.filter('joint_model_ab').height,
        'model_only_all_three_high_pooled_plant': predicted.height,
        'model_only_all_three_high_root_prediction': joint.filter('root_and_oral_models').height,
        'additional_endpoints': len(endpoints),
        'measured_oral_high_and_high_plant_score_with_observed_binary_flags': measured_model.filter(
            pl.col('observed_positive_binary_endpoints') > 0).height,
        'measured_oral_high_and_high_plant_score_with_any_binary_flags': measured_model.filter(
            (pl.col('observed_positive_binary_endpoints') + pl.col('unmeasured_binary_model_flags')) > 0).height,
        'model_only_overlap_with_any_binary_flags': predicted.filter(
            (pl.col('observed_positive_binary_endpoints') + pl.col('unmeasured_binary_model_flags')) > 0).height,
    }
    products = {p.name: sha256(p) for p in output.iterdir()}
    inputs = [f / 'manifest.json' for f in (tox, plant, oral)] + [training, training_manifest, review, review_path]
    (output / 'manifest.json').write_text(json.dumps({'counts': counts, 'inputs': {str(p): sha256(p) for p in inputs},
                                                    'products': products}, indent=2) + '\n')
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('root', 'training', 'output'):
        parser.add_argument('--' + arg, type=Path, required=True)
    parser.add_argument('--review', type=Path, default=RESOURCES / 'reviewed-plant-context.csv')
    run(**vars(parser.parse_args()))
