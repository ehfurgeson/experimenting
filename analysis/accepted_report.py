"""Render the accepted experimental outcomes, evidence intersections and candidate screen."""

import argparse
import html
import json
import shutil
from pathlib import Path

import altair as alt

from data_sprint import read_csv, sha256, write_csv
from sprint_report import verify_bundle

# Corrected release. plant-v1 / integrated-screen-v2 / the 120-structure count are retracted.
# Counts below are filled from the regenerated manifests and checked by require_corrected_release.
BUNDLES = ('toxicity-v1', 'toxicity-v2', 'toxicity-models-v2', 'plant-v5', 'plant-models-v5',
           'integrated-screen-v5', 'uncertainty-v2')
CORRECTED = {'plant_observations': 733, 'all_three_structures': 49}


def table(rows, fields):
    return '<table><thead><tr>' + ''.join(f'<th>{html.escape(k.replace("_", " "))}</th>' for k in fields) + (
        '</tr></thead><tbody>') + ''.join('<tr>' + ''.join(
            f'<td>{html.escape(str(r.get(k, "")))}</td>' for k in fields) + '</tr>' for r in rows) + (
                '</tbody></table>')


def class_count(counts, label):
    return int(counts.get(str(label), counts.get(label)))


def require_corrected_release(plant_observations, all_three_structures):
    """Reject the retracted 2,260-observation / 120-structure release."""
    if plant_observations == 2260 or all_three_structures == 120:
        raise ValueError('Retracted 120-structure plant release')
    if (CORRECTED['plant_observations'] is None or CORRECTED['all_three_structures'] is None or
            plant_observations != CORRECTED['plant_observations'] or
            all_three_structures != CORRECTED['all_three_structures']):
        raise ValueError('This report requires the corrected release counts')


def run(accepted, output):
    accepted, output = Path(accepted), Path(output)
    names = list(BUNDLES)
    manifests = {name: verify_bundle(accepted / name) for name in names}
    before = {str(accepted / name / 'manifest.json'): sha256(accepted / name / 'manifest.json')
              for name in names}
    toxicity = read_csv(accepted / 'toxicity-models-v2/metrics.csv')
    plant = read_csv(accepted / 'plant-models-v5/metrics.csv')
    intervals = read_csv(accepted / 'uncertainty-v2/paired_cluster_intervals.csv')
    screen = read_csv(accepted / 'integrated-screen-v5/candidate_screen.csv')
    profiles = read_csv(accepted / 'integrated-screen-v5/catalog_toxicity_summary.csv')
    trained, corrected, pm, sm = [manifests[name] for name in
                                  ['toxicity-v1', 'toxicity-v2', 'plant-v5', 'integrated-screen-v5']]
    frozen_n = manifests['toxicity-models-v2']['cohort_sizes']['frozen_A']
    require_corrected_release(pm['observations'], sm['all_three_structures'])
    output.mkdir(parents = True, exist_ok = False)
    figures = output / 'figures'
    figures.mkdir()
    training_names = {'frozen_A': 'Original A', 'source_asserted': 'Source asserted',
                      'all_accepted': 'All accepted'}
    tox_display = [{'training': training_names[r['scenario']], 'macro_f1': float(r['macro_f1'])}
                   for r in toxicity if r['evaluation_stratum'] == 'frozen_A' and
                   r['task'] == 'classification' and r['profile'] == 'forest']
    chart = alt.Chart(alt.Data(values = tox_display)).mark_bar(color = '#247d91').encode(
        x = alt.X('training:N', title = None, sort = list(training_names.values()),
                  axis = alt.Axis(labelAngle = 0)),
        y = alt.Y('macro_f1:Q', scale = alt.Scale(domain = [0, 1]), title = 'Held-out macro-F1')
    ).properties(width = 500, height = 240,
                 title = f'Same {frozen_n:,} A outcomes; matched chemical holdouts')
    chart.save(figures / 'matched_toxicity.png')
    chart.save(figures / 'matched_toxicity.svg')
    split_names = {'random_row': 'Random rows', 'publication': 'Publication holdout',
                   'chemical_group': 'Chemical holdout'}
    plant_display = [{'split': split_names[r['protocol']], 'profile': r['profile'].title(),
                      'macro_f1': float(r['macro_f1'])}
                     for r in plant if r['scenario'] == 'with_accepted_categories' and
                     r['source'] == 'all_sources' and r['weighting'] == 'equal_structure']
    chart = alt.Chart(alt.Data(values = plant_display)).mark_bar().encode(
        x = alt.X('split:N', title = None, sort = list(split_names.values()),
                  axis = alt.Axis(labelAngle = 0)),
        xOffset = 'profile:N', color = alt.Color('profile:N', title = None),
        y = alt.Y('macro_f1:Q', scale = alt.Scale(domain = [0, 1]), title = 'Equal-structure macro-F1')
    ).properties(width = 530, height = 240,
                 title = f"Pooled plant response: {pm['observations']:,} accepted observations")
    chart.save(figures / 'plant_holdouts.png')
    chart.save(figures / 'plant_holdouts.svg')
    plot_rows = []
    for i, r in enumerate(screen):
        # Deterministic plot thinning affects only the picture, never the table or front.
        if i % 3 == 0 or r['exploratory_prediction_pareto_front'] == 'True' or r['selection_ids']:
            plot_rows.append({'name': r['compound_name'], 'predicted_log10_ld50': float(r['predicted_log10_ld50']),
                              'plant_probability': float(r['predicted_high_plant_response_probability']),
                              'front': 'Prediction front' if r['exploratory_prediction_pareto_front'] == 'True'
                                       else 'Other candidates',
                              'measured_toxicity': bool(r.get('measured_log10_ld50'))})
    chart = alt.Chart(alt.Data(values = plot_rows)).mark_circle(size = 28, opacity = .55).encode(
        x = alt.X('predicted_log10_ld50:Q', title = 'Full-fit predicted log10(LD50, mg/kg)'),
        y = alt.Y('plant_probability:Q', title = 'Full-fit high plant-response probability',
                  scale = alt.Scale(domain = [0, 1])),
        color = alt.Color('front:N', title = 'Prediction Pareto front'),
        tooltip = ['name:N', 'predicted_log10_ld50:Q', 'plant_probability:Q', 'measured_toxicity:N']
    ).properties(width = 530, height = 300, title = 'Experimental screen; includes in-sample compounds')
    chart.save(figures / 'experimental_screen.png')
    chart.save(figures / 'experimental_screen.svg')
    write_csv(output / 'toxicity_comparison.csv', [r for r in toxicity if r['evaluation_stratum'] == 'frozen_A'],
              list(toxicity[0]))
    write_csv(output / 'plant_comparison.csv', [r for r in plant if r['source'] == 'all_sources'], list(plant[0]))
    score_fields = ['compound_name', 'measured_log10_ld50', 'measured_ld50_scope',
                    'measured_ld50_qualifier', 'measured_ld50_support', 'predicted_log10_ld50',
                    'predicted_high_plant_response_probability', 'exact_catalog_hit',
                    'selected_herbicide', 'selected_natural_product']
    original = [r for r in screen if r['selection_ids']]
    original.sort(key = lambda r: -float(r['predicted_high_plant_response_probability']))
    write_csv(output / 'original_selection_screen.csv', original, list(screen[0]))
    front_rows = [r for r in screen if r['exploratory_prediction_pareto_front'] == 'True']
    write_csv(output / 'prediction_front.csv', front_rows, list(screen[0]))

    def forest_metric(rows, scenario, task, field):
        match = [r for r in rows if r['scenario'] == scenario and r['evaluation_stratum'] == 'frozen_A'
                 and r['task'] == task and r['profile'] == 'forest']
        return float(match[0][field])

    def plant_metric(scenario, protocol, source = 'all_sources', field = 'macro_f1'):
        match = [r for r in plant if r['scenario'] == scenario and r['protocol'] == protocol and
                 r['profile'] == 'forest' and r['source'] == source and r['weighting'] == 'equal_structure']
        return float(match[0][field])

    f1 = [forest_metric(toxicity, name, 'classification', 'macro_f1')
          for name in ('frozen_A', 'source_asserted', 'all_accepted')]
    mae = [forest_metric(toxicity, name, 'regression', 'mae_log10')
           for name in ('frozen_A', 'source_asserted', 'all_accepted')]
    macro_interval = next(r for r in intervals if r['scenario'] == 'all_accepted' and r['metric'] == 'macro_f1')
    mae_interval = next(r for r in intervals if r['scenario'] == 'all_accepted' and r['metric'] == 'mae_log10')

    def covers_zero(row):
        return float(row['conditional_bootstrap_lower95']) <= 0 <= float(row['conditional_bootstrap_upper95'])

    macro_zero = 'includes zero' if covers_zero(macro_interval) else 'excludes zero'
    mae_zero = 'includes zero' if covers_zero(mae_interval) else 'excludes zero'
    source_exact = corrected['scenarios']['source_asserted']['exact_structures']
    trained_broad = trained['scenarios']['all_accepted']
    broad = corrected['scenarios']['all_accepted']
    high, low = class_count(pm['class_counts'], 1), class_count(pm['class_counts'], 0)
    flav_high_f1 = plant_metric('quantitative_only', 'chemical_group', 'Flavonoids2012', 'high_response_f1')
    flav_random_f1 = plant_metric('quantitative_only', 'random_row', 'Flavonoids2012', 'high_response_f1')
    chemical_f1 = plant_metric('with_accepted_categories', 'chemical_group')
    text = f'''# Accepted-data experimental results — 17 November 2026

The earlier plant-v1 / integrated-screen-v2 / results-v2 run reported 2,260 plant
observations and 120 three-axis structures. That count treated percent of control
as percent inhibition and is retracted. plant-v3 corrected the scale. plant-v4
then scored every direction-INC value at or below 100% of control as stimulation
unless the comment recorded a decrease, which mislabeled bare percent-of-control
rows. Here, stimulation is used only when the comment documents an increase or
stimulation. A comment that only names percent of control keeps inhibition =
100 − response. An unresolved contradiction stays unlabeled. Frozen A labels
are unchanged.

## Data expansion and integration

Frozen A has {frozen_n:,} exact structures, and those labels are unchanged.
The forests below were refit on `toxicity-v2`: source-asserted **{source_exact:,}**
exact structures and all-accepted **{broad['exact_structures']:,}**
(+{broad['new_exact_structures']:,}). Those additions are not
{broad['new_exact_structures']:,} newly verified oral LD50s.
**{broad['new_exact_with_context_assumption']:,}** of the
**{broad['new_exact_structures']:,}** new exact structures still carry an
experimental-status, route, or acute-context assumption.
Classification also uses unambiguous censored intervals. Censored doses never
become regression targets. The 1,080 and 3,400 mg/kg bins are this project's
tertiles, not EPA or GHS categories.

`toxicity-v1` is the pre-median cohort: all-accepted **{trained_broad['exact_structures']:,}**
exact structures (+{trained_broad['new_exact_structures']:,}). It is not the
training set for these forests. `toxicity-v2` rebuilds new targets as the median
on the log10 scale. It withholds **{broad['wide_exact_dose_spans']}** new structures
whose distinct exact doses span more than 100-fold and
**{broad['single_implausible_assumed_doses']}** lone assumed doses below 0.05 mg/kg.
**{broad['log_median_bin_disagreements']}** retained new structures change tertile
relative to the arithmetic mean of mg/kg. Frozen A is not relabeled.
`toxicity-models-v2` and `uncertainty-v2` were fit on these targets.

The plant pool contains **{pm['observations']:,} observations / {pm['full_structures']}
structures / {pm['references']} references**, with {high:,} high and {low:,} low
responses. Low inhibition includes stimulation; it does not imply universal inactivity.
There are {pm['mixed_response_structures']} structures with different responses in
different assay contexts. **{sm['all_three_structures']} structures** have an exact
catalog hit, an exact LD50, and a plant-response label. Of those,
**{sm['all_three_selected_herbicides']}** are selected herbicides and
**{sm['all_three_selected_natural_products']}** are selected natural products.
An exact catalog hit is a valid COCONUT or NPASS full key. Provider-key conflicts
are not hits. Selected herbicides are removed from `exact_catalog_hit`. That flag
is not an origin claim. The plant-protein table has {sm['plant_protein_records']}
records, including {sm['affinity_endpoint_records']} Kd/Ki records.

## What the fixed models show

On the unchanged {frozen_n:,} A outcomes, forest macro-F1 moves from
**{f1[0]:.4f}** to **{f1[1]:.4f}** to **{f1[2]:.4f}**. Log10-dose MAE moves from
**{mae[0]:.4f}** to **{mae[1]:.4f}** to **{mae[2]:.4f}**. The all-accepted macro-F1
difference is {float(macro_interval['difference_expanded_minus_baseline']):+.4f};
its conditional 95% interval is {float(macro_interval['conditional_bootstrap_lower95']):+.4f}
to {float(macro_interval['conditional_bootstrap_upper95']):+.4f} and {macro_zero}.
The MAE difference is {float(mae_interval['difference_expanded_minus_baseline']):+.4f},
interval {float(mae_interval['conditional_bootstrap_lower95']):+.4f} to
{float(mae_interval['conditional_bootstrap_upper95']):+.4f}, and {mae_zero}.
These intervals condition on the fixed held-out predictions in `uncertainty-v2`,
which was computed from the `toxicity-models-v2` refit. The bootstrap does not
refit the forests, adjust for source-study dependence, or support a safety or
screening claim. Fold membership follows the corrected `toxicity-v2` cohort, so
these scores replace the pre-median `toxicity-models-v1` / `uncertainty-v1` table.

Pooled plant chemical-holdout macro-F1 is **{chemical_f1:.4f}**. That is weak
transfer. On the flavonoid root/germination series, forest high-response F1 is
**{flav_random_f1:.4f}** under random-row holdout and **{flav_high_f1:.4f}** under
chemical-group holdout. These scores do not validate the plant model and do not
support a screening claim beyond what the holdout shows. Random-row scores reuse
chemicals and papers.

## Experimental candidate screen

The screen contains **{sm['candidate_structures']:,} structures**. The
**{sm['pareto_prediction_front']}-member set is a mathematical prediction front**
on predicted LD50 and predicted high-response probability. It is not a
safer-herbicide list and not a natural-product shortlist. Displayed model numbers
are predictions. A measured LD50 is shown when one exists on the same full key or
the same connectivity key; stereoisomers can share a prediction because the seven
descriptors are stereo-blind. Butyl stearate's stored 32,000 mg/kg is one ICE/HSDB
record (`acute_oral_1852`, qualifier stored as `=`) repeated in later ToxVal and
NPASS rows. Those copies are not additional studies. The shortlist shows qualifier
`>` and does not replace 32,000 with the shrunken prediction. Project bins remain
the 1,080 and 3,400 mg/kg tertiles.

Catalog-hit versus other median LD50 values are not an origin effect and are not
used as one. {sm['unscorable_selection_rows']} structurally unscorable selection
rows remain in an audit file. Full-data predictions include training compounds.
Descriptor distances are coverage diagnostics, not calibrated similarity.

## Reproduction

Canonical local bundles are `toxicity-v2` (corrected aggregation and the cohort
these forests were fit on), `toxicity-models-v2`, `uncertainty-v2`, `plant-v5`,
`plant-models-v5`, and `integrated-screen-v5`. `toxicity-v1`, `toxicity-models-v1`,
and `uncertainty-v1` predate the log10-median refit and are not the current metrics.
`plant-v1`, `plant-models-v2`, `integrated-screen-v2`, and `results-v2` are the
retracted 120-structure run. `plant-v4` is the prior INC-as-stimulation release
and is superseded by `plant-v5`. `results-v4` quoted the pre-refit forests.
The maintained workflow is `analysis/docs/accepted-sprint.md`.
No teacher-derived B values entered the experimental outcome targets.
'''
    (output / 'RESULTS.md').write_text(text)
    rendered = ''.join((figures / f'{name}.svg').read_text() for name in
                       ['matched_toxicity', 'plant_holdouts', 'experimental_screen'])

    def present(rows):
        shown = []
        for r in rows:
            shown.append({**r,
                          'predicted_high_plant_response_probability': round(float(
                              r['predicted_high_plant_response_probability']), 3),
                          'predicted_log10_ld50': round(float(r['predicted_log10_ld50']), 3)})
        return shown

    selected_table = table(present(original[:15]), score_fields)
    front_table = table(present(front_rows), score_fields)
    banner = (f"{broad['exact_structures']:,} exact structures in the refit forest cohort, "
              f"most of the additions assumed rather than newly verified · "
              f"{pm['observations']:,} plant observations · "
              f"{sm['all_three_structures']} structures with a catalog hit, an exact LD50, and a plant label")
    page = f'''<!doctype html><html><meta charset="utf-8"><title>Accepted-data experiments</title>
<style>body{{max-width:1100px;margin:40px auto;padding:0 22px;font:17px system-ui;color:#243e46}}
h1,h2{{color:#174f61}}svg{{max-width:100%;height:auto}}table{{border-collapse:collapse;font-size:13px}}
td,th{{padding:9px;border-bottom:1px solid #ccd4d7;text-align:left;max-width:260px;overflow-wrap:anywhere}}
section{{background:#edf5f5;padding:20px;margin:24px 0}}pre{{white-space:pre-wrap;font:15px system-ui;line-height:1.5}}</style>
<h1>Accepted-data experimental results</h1><p>17 November 2026 · corrected release</p>
<section><strong>{html.escape(banner)}</strong>
<p>Predicted log10 LD50 is a model number. Measured log10 LD50 is a stored dose on the same
full key or the same connectivity key. The 120-structure plant-v1 run is retracted.</p></section>
{rendered}<h2>Original selection: measured LD50 and model prediction</h2>{selected_table}
<h2>Mathematical prediction front, not a natural-product shortlist</h2>{front_table}
<h2>Methods, findings and interpretation</h2><pre>{html.escape(text)}</pre></html>'''
    (output / 'walkthrough.html').write_text(page)
    write_csv(output / 'paired_cluster_intervals.csv', intervals, list(intervals[0]))
    write_csv(output / 'natural_toxicity_summary.csv', profiles, list(profiles[0]))
    if before != {p: sha256(p) for p in before}:
        raise ValueError('Results inputs changed')
    rep = output / 'reproduction'
    rep.mkdir()
    shutil.copyfile(__file__, rep / Path(__file__).name)
    result = {'inputs': before, 'canonical_bundles': names,
              'products': {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return {'report': str(output / 'RESULTS.md'), 'walkthrough': str(output / 'walkthrough.html')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--accepted', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.accepted, args.output), indent = 2))
