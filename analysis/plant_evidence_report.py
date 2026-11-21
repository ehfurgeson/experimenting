"""Independent arithmetic/source checks and figures for the plant evidence pilots."""

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import altair as alt
from sklearn.metrics import f1_score, mean_absolute_error

from accepted_plant_models import chemical_weights
from data_sprint import read_csv, sha256, write_csv
from sprint_report import verify_bundle


def verify_kava(sources, recovered):
    # Independently transcribed from visually checked Table 3, p.722; values are
    # germination/shoot/root inhibition, not percent control. '-' is untested.
    table = {
        'CHEMBL579224': ([[48.1, 71.1, 61.2], [55.6, 73.3, 53.1]],
                         [[50., 55., 75.4], [60., 56., 83.9]]),
        'CHEMBL569329': ([None, [25.9, 74.3, 15.6]],
                         [[46.7, 56.6, 53.1], [50., 61.2, 58.9]]),
        'CHEMBL254218': ([[48.1, 74.9, 50.3], [59.2, 82.4, 63.3]],
                         [[43.3, 31.7, 46.4], [60., 59.9, 51.3]]),
        'CHEMBL578607': ([[51.9, 75.9, 59.9], [59.2, 86.1, 62.6]],
                         [[46.7, None, 39.7], [46.7, 47.6, 46.9]]),
        'CHEMBL1098658': ([[44.4, 63.1, 36.1], [59.2, 78.6, 68.]],
                          [[56.7, 53.1, 42.9], [56.7, 58.2, 43.8]]),
        'CHEMBL576066': ([None, [89.9, 76.5, 74.8]],
                         [[50., 48.6, 32.1], [56.7, 55.6, 48.2]])}
    raw = json.loads((sources / 'CHEMBL3046625-activities-0.json').read_text())['activities']
    byid = {str(r['activity_id']): r for r in raw}
    checked = 0
    for r in recovered:
        if r['reference_id'] != '10.1021/jf0519461':
            continue
        native = byid[r['observation_id'].split(':')[1]]
        species = 0 if native['target_organism'] == 'Lactuca sativa' else 1
        dose = 0 if float(r['dose']) == 1 else 1
        endpoint = {'germination': 0, 'shoot_length': 1, 'root_length': 2}[r['endpoint']]
        expected = table[native['molecule_chembl_id']][species][dose][endpoint]
        assert expected is not None and abs(expected - float(r['signed_inhibition_percent'])) < 1e-10
        checked += 1
    assert checked == 65
    return checked


def run(root, output):
    root, output = Path(root), Path(output)
    folders = ['experiments-v3', 'assay-regression-v1', 'validation-queue-v2']
    bundles = {folder: verify_bundle(root / folder) for folder in folders}
    paths = [root / folder / 'manifest.json' for folder in folders]
    paths += [root / 'sources-v1/coumarins2020.xml', root / 'extra-sources-v1/sources.json',
              Path('analysis/resources/cuscuta_primary_review_2026-11-17.csv')]
    before = {str(p): sha256(p) for p in paths}
    exp = root / 'experiments-v3'
    observations = read_csv(exp / 'combined_experimental_responses.csv')
    old_path = next(Path(p) for p in bundles['experiments-v3']['inputs'] if p.endswith('/plant_training_observations.csv'))
    old = [r for r in read_csv(old_path) if r['label_kind'] == 'quantitative']
    combined = {r['observation_id']: r for r in observations}
    assert all(all(combined[r['observation_id']][k] == v for k, v in r.items()) for r in old)
    assert len(combined) == len(observations)
    grouped = defaultdict(list)
    for r in read_csv(exp / 'context_predictions.csv'):
        grouped[r['protocol'], r['profile']].append(r)
    context_metrics = read_csv(exp / 'context_metrics.csv')
    for metric in context_metrics:
        rs = grouped[metric['protocol'], metric['profile']]
        assert len(rs) == len({r['observation_id'] for r in rs})
        assert len(rs) == bundles['experiments-v3']['combined_binary_observations']
        w = chemical_weights(rs)
        value = f1_score([int(r['observed']) for r in rs], [float(r['probability']) >= .5 for r in rs],
                         average = 'macro', labels = [0, 1], sample_weight = w)
        assert abs(value - float(metric['macro_f1'])) < 1e-12
        assignments = defaultdict(set)
        for r in rs:
            assignments[r['group']].add(r['fold'])
        assert all(len(folds) == 1 for folds in assignments.values())
    regression = root / 'assay-regression-v1'
    rgroups = defaultdict(list)
    for r in read_csv(regression / 'predictions.csv'):
        rgroups[r['species'], r['endpoint'], r['protocol'], r['profile']].append(r)
    regression_metrics = read_csv(regression / 'metrics.csv')
    for metric in regression_metrics:
        rs = rgroups[metric['species'], metric['endpoint'], metric['protocol'], metric['profile']]
        value = mean_absolute_error([float(r['observed']) for r in rs], [float(r['predicted']) for r in rs])
        assert abs(value - float(metric['mae_percentage_points'])) < 1e-12
    splits = defaultdict(lambda: defaultdict(set))
    for r in read_csv(regression / 'split_membership.csv'):
        splits[r['species'], r['endpoint'], r['protocol'], r['fold']][r['role']].add(r['group'])
    assert all(not (r['train'] & r['test']) for r in splits.values())
    coumarins = read_csv(exp / 'coumarin_primary_observations.csv')
    xml = ET.fromstring((root / 'sources-v1/coumarins2020.xml').read_bytes())
    native = {}
    for table in xml.findall('.//table-wrap'):
        for tr in table.findall('.//tbody/tr'):
            cells = [''.join(c.itertext()).strip() for c in tr]
            native[table.attrib['id'], cells[0]] = [float(re.search(r'\d+(?:\.\d+)?', c)[0]) for c in cells[1:]]
    for r in coumarins:
        table, code = r['source_locator'].split('; ')
        values = native[table, code]
        value = values[[0, 50, 100, 200, 400, 800].index(int(r['concentration']))]
        assert value == float(r['mean']) and values[0] == float(r['control_mean'])
        assert abs(float(r['derived_inhibition_percent']) - 100 * (1 - value / values[0])) < 1e-12
    kava = verify_kava(root / 'sources-v1', read_csv(exp / 'new_chembl_responses.csv'))
    queue = read_csv(root / 'validation-queue-v2/validation_queue.csv')
    assert len(queue) == len({r['full_key'] for r in queue}) == 24
    assert sorted(Counter(r['selection_reason'] for r in queue).values()) == [8, 8, 8]
    cuscuta = read_csv(paths[-1])
    assert len(cuscuta) == 5 and all(float(r['dose_mM']) == 1 for r in cuscuta)
    extras = json.loads((root / 'extra-sources-v1/sources.json').read_text())
    for r in extras:
        if r.get('sha256'):
            assert sha256(root / 'extra-sources-v1' / r['file']) == r['sha256']
    output.mkdir(parents = True, exist_ok = False)
    summary = {'canonical_old_quantitative_observations_preserved': len(old),
        'new_experimental_chembl_responses': bundles['experiments-v3']['new_chembl_observations'],
        'new_experimental_chembl_structures': bundles['experiments-v3']['new_chembl_structures'],
        'primary_kava_cells_checked': kava, 'primary_coumarin_cells_and_ratios_checked': len(coumarins),
        'additional_cuscuta_exact_text_observations': len(cuscuta),
        'recomputed_context_f1_scores': len(context_metrics), 'recomputed_assay_mae_scores': len(regression_metrics),
        'checked_assay_fold_partitions': len(splits), 'all_declared_groups_disjoint': True,
        'validated_hash_products': {name: len(m['products']) for name, m in bundles.items()},
        'queue_compounds': len(queue),
        'limits': 'Source/value and arithmetic checks do not independently establish sample identity, '
                  'natural biosynthesis, prospective model performance or safety.'}
    (output / 'verification.json').write_text(json.dumps(summary, indent = 2) + '\n')
    chart_rows = [{**r, 'macro_f1': float(r['macro_f1'])} for r in context_metrics]
    chart = alt.Chart(alt.Data(values = chart_rows)).mark_bar(color = '#346f7a').encode(
        x = alt.X('macro_f1:Q', scale = alt.Scale(domain = [0, 1]), title = 'Equal-structure macro-F1'),
        y = alt.Y('profile:N', title = None), row = alt.Row('protocol:N', title = None)
    ).properties(width = 520, height = 140, title = 'Context helps within familiar studies; new-study transfer remains weak')
    endpoint_names = {'fresh_biomass': 'Fresh biomass', 'germination_frequency': 'Germination',
                      'normal_seedling_count': 'Normal seedlings'}
    curves = [{**r, 'endpoint': endpoint_names[r['endpoint']],
               'dose': float(r['concentration']), 'inhibition': float(r['derived_inhibition_percent'])}
              for r in coumarins]
    curve_chart = alt.Chart(alt.Data(values = curves)).mark_line(point = True).encode(
        x = alt.X('dose:Q', scale = alt.Scale(type = 'log', domain = [50, 800]),
                  axis = alt.Axis(values = [50, 100, 200, 400, 800], format = 'g'),
                  title = 'Reported concentration (ug/mL)'),
        y = alt.Y('inhibition:Q', title = 'Mean inhibition (%)'),
        color = alt.Color('source_name:N', title = 'Source compound'),
        row = alt.Row('endpoint:N', title = None, header = alt.Header(labelAngle = 0, labelAlign = 'left'))
    ).properties(width = 520, height = 140, title = 'Complete primary tables preserve weak response and stimulation')
    import vl_convert as vlc
    for name, figure in [('context_validation', chart), ('coumarin_dose_responses', curve_chart)]:
        (output / f'{name}.svg').write_text(vlc.vegalite_to_svg(figure.to_dict()))
        (output / f'{name}.png').write_bytes(vlc.vegalite_to_png(figure.to_dict(), scale = 2))
    write_csv(output / 'cuscuta_primary_observations.csv', cuscuta, list(cuscuta[0]))
    shutil.copyfile(__file__, output / Path(__file__).name)
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Report inputs changed')
    manifest = {'inputs': before, 'products': {str(p.relative_to(output)): sha256(p)
                for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--root', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.output), indent = 2))
