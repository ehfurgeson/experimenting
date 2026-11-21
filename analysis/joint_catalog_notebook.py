"""Interactive review of the joint plant-activity and toxicity screen."""

# Marimo uses trailing expressions for displayed cell outputs.
# ruff: noqa: B018, PLR1711

import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="full",
    app_title="Plant activity and toxicity | Catalog review",
)


@app.cell
def _():
    import json
    import os
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import polars as pl

    return Path, alt, json, mo, os, pl


@app.cell
def _(Path, json, mo, os, pl):
    root = Path(os.environ.get('AGROTOX_JOINT_ROOT', mo.notebook_location().parent / 'experiments/import-expansion'))
    joint = root / 'catalog-joint-screen-v2'
    diagnostics = root / 'catalog-joint-diagnostics-v2'
    mo.stop(not (joint / 'manifest.json').exists() or not (diagnostics / 'manifest.json').exists(),
            mo.md('**Analysis files are missing.** Set `AGROTOX_JOINT_ROOT` to the local run folder. '
                  'The reproduction commands are in `analysis/docs/joint-catalog-notebook.md`.'))
    counts = json.loads((joint / 'manifest.json').read_text())['counts']
    data = pl.scan_parquet(joint / 'joint_scores.parquet')
    measured = pl.read_csv(joint / 'measured_high_oral.csv', infer_schema_length=1000)
    endpoint_metrics = pl.read_csv(root / 'catalog-bulk-public-v1/endpoint_summary.csv')
    names = {'molecular_weight': 'Molecular weight', 'tpsa': 'Polar surface area', 'hbd': 'Hydrogen-bond donors',
             'hba': 'Hydrogen-bond acceptors', 'rotatable_bonds': 'Rotatable bonds', 'rings': 'Rings',
             'fraction_sp3': 'Fraction of tetrahedral carbon', 'morgan': 'Morgan fingerprint (all 2,048 bits)',
             'log10_dose': 'Dose (log scale)'}
    return (
        counts,
        data,
        diagnostics,
        endpoint_metrics,
        joint,
        measured,
        names,
        root,
    )


@app.cell(hide_code=True)
def _(counts, mo):
    mo.vstack([
        mo.md('''# Which compounds slow plant growth and have a higher rat oral LD50?

        High oral LD50 and plant inhibition sometimes occur together. The results identify compounds
        worth reviewing. Human safety and crop selectivity remain open questions.
        '''),
        mo.hstack([
            mo.stat(label='Structures compared', value=f"{counts['catalog_structures']:,}"),
            mo.stat(label='High measured oral LD50 + high plant score',
                    value=f"{counts['measured_high_oral_high_pooled_plant']:,}"),
            mo.stat(label='High scores on plant and all three oral models',
                    value=f"{counts['model_only_all_three_high_pooled_plant']:,}"),
        ], justify='start', gap=2, wrap=True),
        mo.md('**LD50** is the dose estimated to kill half the animals in a test. A higher value '
              'means more compound was needed in that test. This analysis uses rat oral LD50 and '
              'uses three project bins. **Low** is up to 1,080 mg/kg, **middle** is above 1,080 '
              'through 3,400, and **high** is above 3,400.')
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## How the screen worked

    1. **Build the catalog.** COCONUT contributed 724,233 valid structures. LOTUS added 36,374
       and NPASS added 7,832 after deduplication. RDKit checked each entry's structure against its
       full InChIKey, which retains distinctions such as stereochemistry. Catalog membership alone
       leaves origin unresolved.
    2. **Score each structure.** Three forests estimated the rat oral LD50 bin. Another 12 forests
       covered other toxicity outcomes. Five plant forests estimated one pooled response score and
       four species-and-endpoint responses at three doses each.
    3. **Join by exact structure.** Every catalog structure has a plant row and a toxicity row.
       Exact training matches use saved or reconstructed held-out predictions. Other rows use a
       fit to the full training cohort. The NPASS-augmented oral model leaves 568 training structures
       blank because those structures lacked held-out scores.
    4. **Compare measurements and scores.** ICE measured oral bins take priority. When an exact ICE
       aggregate is missing, the exploratory screen looks for a high-bin score of at least 0.50
       from each oral model. A pooled plant score of at least 0.50 represents high model activity.
       Seven binary toxicity endpoints have their own assay flags. Five quantitative toxicity endpoints
       retain their units and observed values. Each forest also has a simple training-range check.

    The supplied NICE files had no plant-growth measurements. The local NPASS plant records left
    critical details such as dose, duration or the meaning of a percentage unresolved. Neither source
    added plant-training labels. NPASS did contribute 568 labels under the project's trusted-source
    assumption to the augmented oral model. CATMoS targets are existing model estimates.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    plant_cutoff = mo.ui.slider(start=0.30, stop=0.90, step=0.05, value=0.50,
                                label='Minimum pooled plant score', show_value=True)
    plant_cutoff
    return (plant_cutoff,)


@app.cell(hide_code=True)
def _(alt, counts, data, measured, mo, pl, plant_cutoff):
    plant_high = pl.col('pooled_high_response_score') >= plant_cutoff.value
    screen = data.select(
        (plant_high & pl.col('measured_oral_high')).sum().alias('measured'),
        (plant_high & pl.col('ice_oral_bin').is_null() & pl.all_horizontal(
            pl.col(f'oral_{model}__high') >= 0.5 for model in ('A', 'B', 'augmented'))).sum().alias('model'),
    ).collect().row(0, named=True)
    chart_data = measured.select('name', 'full_key', 'ice_oral_ld50_mg_kg', 'pooled_high_response_score',
                                 'observed_positive_binary_endpoints')
    scatter = (alt.Chart(alt.Data(values=chart_data.to_dicts())).mark_circle(size=52, opacity=0.65)
               .encode(x=alt.X('ice_oral_ld50_mg_kg:Q', title='Measured rat oral LD50 (mg/kg)',
                               scale=alt.Scale(type='log', zero=False)),
                       y=alt.Y('pooled_high_response_score:Q', title='Pooled plant score',
                               scale=alt.Scale(domain=[0, 1])),
                       color=alt.condition('datum.observed_positive_binary_endpoints > 0',
                                           alt.value('#b94626'), alt.value('#137b78')),
                       tooltip=['name:N', 'full_key:N', 'ice_oral_ld50_mg_kg:Q',
                                'pooled_high_response_score:Q', 'observed_positive_binary_endpoints:Q']))
    cutoff_line = alt.Chart(alt.Data(values=[{'threshold': plant_cutoff.value}])).mark_rule(
        color='#343a40', strokeDash=[5, 4]).encode(y='threshold:Q')
    mo.vstack([
        mo.md(f'''## Compare candidate counts

        At the selected cutoff, **{screen['measured']:,}** structures have a high measured oral LD50
        and **{screen['model']:,}** have high scores from all three oral models with no exact ICE
        oral aggregate. The chart shows all {measured.height} measured high-LD50 structures. Orange marks a positive
        measured result on at least one of the seven other binary toxicity assays.
        '''),
        (scatter + cutoff_line).properties(height=280, width='container'),
        mo.md('The default cutoff is 0.50. At that cutoff, '
              f"**{counts['measured_oral_high_and_high_plant_score_with_observed_binary_flags']} of the "
              f"{counts['measured_high_oral_high_pooled_plant']}** had an observed positive binary result. "
              f"**{counts['measured_oral_high_and_high_plant_score_with_any_binary_flags']}** had an observed "
              'positive or a model flag on an unmeasured assay. The narrower '
              'radish and garden cress models produced **zero overlaps** at 40% root inhibition at '
              '100 µM with either high measured oral LD50 or high scores from all three oral models.'),
    ])
    return


@app.cell(hide_code=True)
def _(counts, mo):
    mo.md(f"""
    ## Three compounds that explain the result

    - **(R)-(+)-Limonene, 4,400 mg/kg.** A published study found strong wild oat germination
      inhibition. Its pooled plant score was just **0.30**. EPA records irritation and skin
      sensitization concerns. [Plant study](https://www.nature.com/articles/s41598-025-25935-z) ·
      [EPA assessment](https://downloads.regulations.gov/EPA-HQ-OPP-2010-0673-0004/content.pdf)
    - **7-Methylcoumarin, 3,800 mg/kg.** Its pooled score was **0.87**. The wheat study's table gives
      17 mm of root growth versus 68 mm in control at 10 ppm, or 75% inhibition. The test material
      was synthesized, natural occurrence is unresolved, and five other assays had model flags.
      [Study tables](https://medcraveonline.com/HIJ/HIJ-02-00021.pdf)
    - **Dibutyl phthalate, 7,499 mg/kg.** A study reported over 70% inhibition of Chinese sprangletop
      germination. EPA found robust developmental-toxicity evidence. [Plant study](https://doi.org/10.1071/CP13339) ·
      [EPA evaluation](https://www.epa.gov/assessing-and-managing-chemicals-under-tsca/risk-evaluation-dibutyl-phthalate-12-benzene)

    The original plant training table also flagged triforine. Its source measured **apple pollen**
    germination, a different biological outcome from weed seed germination. Of the
    {counts['measured_high_oral']} high ICE aggregates, **{counts['measured_high_oral_with_report_at_or_below_cutoff']}**
    include an eligible individual report at or below 3,400 mg/kg. Butyl stearate has a reviewed
    lower bound above 32,000 mg/kg, separate from the exact values. The table below preserves
    the report ranges. [Apple pollen study](https://doi.org/10.1080/00221589.1977.11514772)
    """)
    return


@app.cell(hide_code=True)
def _(counts, mo):
    compound_query = mo.ui.text(value='limonene', label=f"Name or InChIKey in {counts['measured_high_oral']} entries")
    compound_query
    return (compound_query,)


@app.cell(hide_code=True)
def _(compound_query, measured, mo, pl):
    query = compound_query.value.strip().lower()
    matching = measured.filter(pl.any_horizontal(pl.col(field).str.to_lowercase().str.contains(query, literal=True)
                                                for field in ('name', 'full_key')))
    mo.ui.table(matching.select(
        pl.col('name').alias('Compound'), pl.col('ice_oral_ld50_mg_kg').alias('ICE oral LD50 (mg/kg)'),
        pl.col('ice_exact_min_mg_kg').alias('Lowest ICE point'), pl.col('ice_exact_max_mg_kg').alias('Highest ICE point'),
        pl.col('pooled_high_response_score').round(3).alias('Plant score'),
        pl.col('measured_binary_endpoints').alias('Binary assays measured'),
        pl.col('observed_positive_binary_endpoints').alias('Observed positives'),
        pl.col('unmeasured_binary_model_flags').alias('Model flags'), 'full_key'), page_size=8,
        selection=None, show_download=False)
    return


@app.cell(hide_code=True)
def _(diagnostics, endpoint_metrics, mo, pl, root):
    oral = pl.read_csv(root / 'public-models-v2/pooled_metrics.csv').filter(
        (pl.col('task') == 'classification') & (pl.col('profile') == 'forest'))
    augmented = pl.read_csv(root / 'npass-label-trusted-v2/metrics.csv').filter(
        pl.col('profile') == 'trusted_npass_exact_and_bounds')
    oral_table = pl.concat([
        oral.select(pl.col('pathway').replace({'A': 'ICE', 'B': 'CATMoS'}).alias('Evaluation labels'),
                    pl.col('n').alias('Test structures'), 'macro_f1', 'class_2_f1'),
        augmented.select(pl.lit('ICE, after training with NPASS additions').alias('Evaluation labels'),
                         pl.col('structures').alias('Test structures'), 'macro_f1', 'class_2_f1'),
    ]).rename({'macro_f1': 'Macro-F1', 'class_2_f1': 'High-LD50 F1'}).with_columns(pl.selectors.float().round(3))
    plant_validation = pl.read_csv(diagnostics / 'pooled_plant_validation.csv').filter(
        pl.col('profile') == 'descriptor7_forest').select(pl.col('split').replace({
            'random_row': 'Random rows', 'publication': 'Held-out publications',
            'chemical_group': 'Held-out chemical groups'}).alias('Test split'),
            pl.col('macro_f1').round(3).alias('Macro-F1'), pl.col('high_response_f1').round(3).alias('High-response F1'))
    assays = pl.read_csv(diagnostics / 'plant_assay_validation.csv').with_columns(pl.selectors.float().round(3))
    controls = pl.read_csv(root / 'other-toxicity-endpoints-v2/metrics.csv').filter(
        pl.col('profile') == 'dummy').select('endpoint', pl.col('macro_f1').alias('baseline_f1'),
                                            pl.col('mae_log10').alias('median_mae_log10'))
    other_binary = endpoint_metrics.filter(pl.col('task') == 'binary').select(
        'endpoint', 'profile', 'structures', pl.col('macro_f1').round(3), pl.col('auroc').round(3)).join(
            controls.select('endpoint', pl.col('baseline_f1').round(3)), on='endpoint', validate='1:1')
    other_numeric = endpoint_metrics.filter(pl.col('task') != 'binary').select(
        'endpoint', 'profile', 'structures', 'output_unit', pl.col('mae_log10').round(3)).join(
            controls.select('endpoint', pl.col('median_mae_log10').round(3)), on='endpoint', validate='1:1')
    mo.vstack([
        mo.md('''## How well did the models work?

        A **random forest** combines hundreds of small decision trees. All 20 screening forests
        used 200 trees. The base inputs are seven molecular properties. Selected toxicity models
        add a Morgan fingerprint, a pattern of molecular fragments. The four plant regressions
        also take the tested dose.

        **F1** balances how often a positive call is correct and how many positives are found.
        **Macro-F1** averages the F1 scores for all classes equally. For numerical predictions,
        **MAE** is the average absolute distance between a prediction and its measured value.
        Chemical-group holdouts keep related structures together on one side of the test.
        '''),
        mo.ui.tabs({
            'Rat oral LD50': mo.vstack([mo.md('The models classify low, middle and high LD50. '
                'CATMoS F1 measures agreement with another model’s labels. The NPASS-augmented '
                'forest is evaluated on the same measured ICE labels as the ICE-only forest.'),
                mo.ui.table(oral_table, selection=None, show_download=False)]),
            'Pooled plant activity': mo.vstack([mo.md('The forest learns from 733 observations '
                'across 211 structures and 76 references. Quantitative results use ≥40% for high '
                'and ≤20% for low. The original categorical outcomes retain their own rules. '
                'Random row splits can share measurements of the same compound. Publication and '
                'chemical-group holdouts address different kinds of overlap.'),
                mo.ui.table(plant_validation, selection=None, show_download=False)]),
            'Radish and cress': mo.vstack([mo.md('Each numerical model uses 81 observations '
                'from 27 compounds in one study. The errors are in percentage points of inhibition. '
                'The secondary F1 compares the observed low and high bands at a 40% prediction '
                'cutoff. Blank F1 means the test data had no observed high responses.'),
                mo.ui.table(assays, selection=None, show_download=False)]),
            'Other toxicity': mo.vstack([mo.md('Seven classifiers predict binary assay outcomes. '
                'Five regressions predict doses or concentrations. Their errors are measured on the '
                'log10 scale, while their catalog outputs are in the displayed source units. '
                'AUROC summarizes how often positives rank above negatives. The forest profiles '
                'were selected using these grouped F1 or MAE results. The baseline uses the training '
                'class frequencies or median. The screen has no separate benchmark for that profile choice.'),
                mo.ui.table(other_binary, selection=None, show_download=False),
                mo.ui.table(other_numeric, selection=None, show_download=False)]),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(diagnostics, mo, names, pl, root):
    oral_weights = pl.read_csv(root / 'public-models-v2/weights.csv').select(
        (pl.col('pathway').replace({'A': 'ICE', 'B': 'CATMoS'}) + ' · ' + pl.col('class').replace_strict(
            {0: 'low LD50', 1: 'middle LD50', 2: 'high LD50'})).alias('comparison'),
        'fold', 'feature', pl.col('standardized_weight').alias('weight'))
    plant_weights = pl.read_csv(diagnostics / 'plant_logistic_weights.csv').filter(
        pl.col('protocol') == 'chemical_group').select(pl.lit('Pooled plant · high response').alias('comparison'),
                                                       'fold', 'feature', 'weight')
    weights = pl.concat([oral_weights, plant_weights]).with_columns(pl.col('feature').replace(names))
    oral_logistic = pl.read_csv(root / 'public-models-v2/pooled_metrics.csv').filter(
        (pl.col('task') == 'classification') & pl.col('profile').is_in(['majority', 'logistic', 'forest']))
    oral_comparison = (oral_logistic.select(pl.col('pathway').replace({'A': 'ICE oral', 'B': 'CATMoS oral'}),
                                           'profile', 'macro_f1')
                       .pivot(on='profile', index='pathway', values='macro_f1')
                       .rename({'pathway': 'Benchmark'}))
    pooled_comparison = (pl.read_csv(diagnostics / 'pooled_plant_validation.csv')
                         .filter(pl.col('split') == 'chemical_group')
                         .select(pl.lit('Pooled plant, held-out chemistry').alias('Benchmark'),
                                 pl.col('profile').str.strip_prefix('descriptor7_'), 'macro_f1')
                         .pivot(on='profile', index='Benchmark', values='macro_f1'))
    comparison = pl.concat([oral_comparison, pooled_comparison], how='diagonal').with_columns(
        pl.selectors.float().round(3))
    logistic_choice = mo.ui.dropdown(weights['comparison'].unique(maintain_order=True).to_list(),
                                     value='ICE · high LD50', label='Logistic comparison')
    mo.vstack([mo.md('''## Logistic weights from comparison models

    The screening runs used forests. Logistic regression was a simpler benchmark for ICE, CATMoS,
    and pooled plant activity. A positive standardized weight raises the model’s score for the
    selected class as the feature increases. A negative weight lowers it. These are average fold
    coefficients. Their variability across folds and correlations between features limit interpretation.
    The table compares their held-out macro-F1. The pooled plant logistic benchmark scored higher
    on held-out chemistry in this run. The completed catalog’s plant scores use the forest.
    '''), mo.ui.table(comparison, selection=None, show_download=False), logistic_choice])
    return logistic_choice, weights


@app.cell(hide_code=True)
def _(alt, logistic_choice, mo, pl, weights):
    grouped = weights.filter(pl.col('comparison') == logistic_choice.value).group_by('feature').agg(
        pl.col('weight').mean().alias('mean'), pl.col('weight').min().alias('min'), pl.col('weight').max().alias('max'))
    base = alt.Chart(alt.Data(values=grouped.to_dicts())).encode(
        y=alt.Y('feature:N', sort=alt.SortField('mean', order='descending'), title=None))
    mo.vstack([(base.mark_rule(color='#526878').encode(x='min:Q', x2='max:Q') +
                base.mark_point(filled=True, size=75, color='#137b78').encode(
                    x=alt.X('mean:Q', title='Standardized weight'), tooltip=['feature:N', 'mean:Q', 'min:Q', 'max:Q']))
               .properties(height=210, width='container'),
               mo.md('Dots show the mean weight. Lines span the lowest and highest weights across folds.')])
    return


@app.cell(hide_code=True)
def _(diagnostics, mo, names, pl):
    oob = pl.read_csv(diagnostics / 'oob_importance.csv').with_columns(pl.col('feature').replace(names))
    forest_choice = mo.ui.dropdown(oob['model'].unique(maintain_order=True).to_list(), value='Oral · ICE',
                                   label='Screening forest')
    mo.vstack([mo.md('''## Which inputs mattered to the forests?

    Each tree fits a resample of the training data. **Out of bag (OOB)** means looking at rows left
    out of that tree’s resample. The diagnostic shuffles one input among those rows and measures
    how much prediction quality drops. A larger drop means that shuffling disrupted the model more.
    The fingerprint is shuffled as a single block. These diagnostics measure how the model uses
    inputs. They leave causal effects and performance on new chemical families unresolved.
    For example, shuffling polar surface area reduced oral ICE OOB macro-F1 by about 0.032.
    Shuffling the hydrogen-bond acceptor count reduced pooled plant OOB macro-F1 by about 0.070.
    '''), forest_choice])
    return forest_choice, oob


@app.cell(hide_code=True)
def _(alt, forest_choice, mo, oob, pl):
    selected = oob.filter(pl.col('model') == forest_choice.value)
    detail = selected.row(0, named=True)
    metric = detail['metric']
    performance = 'Macro-F1' if metric == 'Macro-F1 drop' else 'MAE'
    units = (' (percentage points)' if forest_choice.value.startswith('Plant') else ' (log10 scale)'
             ) if performance == 'MAE' else ''
    chart = alt.Chart(alt.Data(values=selected.to_dicts())).mark_bar(color='#137b78').encode(
        x=alt.X('mean_performance_loss:Q', title=metric + units),
        y=alt.Y('feature:N', sort='-x', title=None),
        tooltip=['feature:N', 'mean_performance_loss:Q', 'shuffle_sd:Q'])
    mo.vstack([
        mo.md(f"{performance} before shuffling{units} was **{detail['baseline']:.3f}**. "
              f"**{detail['rows_with_oob_votes']:,} of {detail['training_rows']:,}** training rows "
              f"received an OOB prediction. Bars average {detail['repeats']} shuffles. "
              'A negative bar means that shuffling improved this diagnostic score.'),
        chart.properties(height=230, width='container'),
    ])
    return


@app.cell(hide_code=True)
def _(counts, joint, mo, pl):
    coverage = pl.read_csv(joint / 'endpoint_coverage.csv').filter(
        pl.col('group') == 'high_measured_oral_high_plant_model').drop('group')
    mo.vstack([mo.md(f'''## What would establish a stronger result?

    A strong follow-up has a confirmed tested structure, reproducible inhibition in an assay relevant
    to the target weed, evidence of crop selectivity, and route-specific toxicity measurements.
    This table shows how much additional toxicity evidence is available for the {counts['measured_high_oral_high_pooled_plant']}
    measured-oral overlaps. The model flags use a 0.50 cutoff on unmeasured binary outcomes.
    The numerical endpoints remain on separate scales.
    '''), mo.ui.table(coverage, selection=None, show_download=False),
        mo.md('**Data products.** The full one-row-per-structure join is `joint_scores.parquet`. '
              'The measured oral follow-up is `measured_high_oral.csv`. The purely score-based '
              'selection is `model_only_overlap.parquet`. All are under `catalog-joint-screen-v2`. '
              'Reproduction commands and model inputs are documented in `analysis/docs/joint-catalog-notebook.md`.')])
    return


if __name__ == "__main__":
    app.run()
