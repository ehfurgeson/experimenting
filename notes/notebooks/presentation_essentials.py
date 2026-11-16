"""Local experimental notebook: saved model comparisons and feature diagnostics."""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Chemistry model experiments")


@app.cell(hide_code=True)
def _():
    import csv
    import hashlib
    import json
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    from sklearn.metrics import (
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )

    return (
        Path,
        alt,
        balanced_accuracy_score,
        confusion_matrix,
        csv,
        f1_score,
        hashlib,
        json,
        mo,
        np,
        precision_score,
        recall_score,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Chemistry model experiments
    Exploring which chemical features separate the compound groups, then
    checking whether that separation carries over to measured plant responses.
    """)
    return


@app.cell(hide_code=True)
def _(Path, csv, hashlib, json, mo):
    repo = Path(mo.notebook_location()).resolve().parents[1]
    experiment_specs = {
        "Selection · 171 compounds": (
            "weekly-models-2026-11-10", "Selected herbicide", "Selected natural product",
            "selection_target",
        ),
        "Reviewed cohorts · 30 compounds": (
            "reviewed-cohort-models-2026-11-11-final", "Commercial comparator",
            "Reviewed natural occurrence", "provenance_comparator_target",
        ),
        "Pooled activity · 73 compounds": (
            "experimental-heterogeneous-diagnostics-2026-11-12", "High response",
            "Low response", "activity_target",
        ),
    }
    verified_files = []

    def read_frozen(bundle, filename):
        path = repo / "analysis/outputs" / bundle / filename
        manifest = json.loads((path.parent / "manifest.json").read_text())
        expected = manifest["output_hashes"].get(str(path))
        if expected is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Missing or changed frozen result: {path}")
        verified_files.append({"Bundle": bundle, "File": filename, "SHA-256": "Matches"})
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))

    experiments = {
        name: {filename.removesuffix(".csv"): read_frozen(spec[0], filename)
               for filename in ("reports.csv", "oof.csv", "coefficients.csv", "oob_importance.csv")}
        for name, spec in experiment_specs.items()
    }
    transfer_bundle = "experimental-flavonoid-transfer-2026-11-12"
    transfer_reports = read_frozen(transfer_bundle, "reports.csv")
    transfer_predictions = read_frozen(transfer_bundle, "predictions.csv")
    model_names = {
        "formula_raw": "Formula · logistic",
        "formula_pca": "Formula + PCA · logistic",
        "morgan_logistic": "Morgan bits · logistic",
        "morgan_forest": "Morgan bits · random forest",
        "halogens_only": "Halogen counts/fractions · logistic",
        "halogen_presence": "Any halogen · logistic",
        "formula_drop_halogen_columns": "Formula, halogen columns removed",
        "composition_without_halogens": "Composition recomputed without halogens",
    }
    return (
        experiment_specs,
        experiments,
        model_names,
        transfer_predictions,
        transfer_reports,
        verified_files,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1: Model Overviews

    | Experiment | Positive / negative | Question |
    |---|---|---|
    | Selection, 171 structures | 55 selected herbicides / 116 selected natural products | Does chemistry distinguish my original selection? |
    | Reviewed cohorts, 30 structures | 11 commercial comparators / 19 natural-occurrence examples | Does the smaller, reviewed source contrast separate? |
    | Pooled activity, 73 structures | 41 high / 32 low responses | What happens if I relax assay compatibility? |

    The first two targets describe **cohort membership**. Natural origin is not
    inactivity. The third pools different plants, doses and endpoints under an
    experimental rule; it does not replace the separately reviewed assay labels.
    Scores across these experiments are not a model-improvement sequence.

    I used the same five scaffold folds for all profiles **within each experiment**.
    Scaling and PCA learn from training rows only. Logistic fits use L2, C=1 and
    balanced class weights. The forest uses 500 trees and minimum leaf size 2.
    """)
    return


@app.cell(hide_code=True)
def _(experiment_specs, mo):
    experiment = mo.ui.dropdown(
        options=list(experiment_specs), value="Selection · 171 compounds",
        label="Experiment: updates scores, weights and forest diagnostics below",
        allow_select_none=False,
    )
    experiment
    return (experiment,)


@app.cell(hide_code=True)
def _(experiment, experiment_specs, experiments, mo):
    selected = experiments[experiment.value]
    positive_class = experiment_specs[experiment.value][1]
    mo.hstack([
        mo.stat(positive_class, label="Positive class · 1"),
        mo.stat(experiment_specs[experiment.value][2], label="Negative class · 0"),
    ], justify="start", gap=3)
    return positive_class, selected


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2: Separation performance

    **F1 is the main comparison.** These are pooled scaffold-held-out predictions,
    not training scores or averages of fold F1. The majority rule is learned
    separately in each training fold; an always-positive reference helps expose
    an easy F1 score when positives are common.
    """)
    return


@app.cell(hide_code=True)
def _(
    balanced_accuracy_score,
    confusion_matrix,
    experiment,
    experiment_specs,
    f1_score,
    model_names,
    np,
    precision_score,
    recall_score,
    selected,
):
    score_rows = []
    reference = None
    scaffold_folds = {}
    for _report in selected["reports"]:
        assert _report["target"] == experiment_specs[experiment.value][3]
        assert _report["status"] == "evaluated"
        _rows = [r for r in selected["oof"] if r["profile"] == _report["profile"]]
        _membership = {r["compound_id"]: (r["fold"], r["label"]) for r in _rows}
        assert len(_membership) == len(_rows) == int(_report["n"])
        if reference is None:
            reference = _membership
        assert _membership == reference
        for _r in _rows:
            scaffold_folds.setdefault(_r["scaffold"], set()).add(_r["fold"])
        _y = np.array([int(r["label"]) for r in _rows])
        _pred = np.array([float(r["probability"]) >= 0.5 for r in _rows])
        _metrics = {
            "f1": f1_score(_y, _pred, zero_division=0),
            "precision": precision_score(_y, _pred, zero_division=0),
            "recall": recall_score(_y, _pred, zero_division=0),
            "balanced_accuracy": balanced_accuracy_score(_y, _pred),
        }
        for _metric, _value in _metrics.items():
            assert abs(_value - float(_report[_metric])) < 1e-12
        assert list(confusion_matrix(_y, _pred, labels=[0, 1]).ravel()) == [
            int(_report[k]) for k in ("tn", "fp", "fn", "tp")
        ]
        score_rows.append({
            "Model": model_names[_report["profile"]],
            "F1": _metrics["f1"], "Precision": _metrics["precision"],
            "Recall": _metrics["recall"], "Balanced accuracy": _metrics["balanced_accuracy"],
        })
    assert all(len(folds) == 1 for folds in scaffold_folds.values())
    assert len({fold for fold, _ in reference.values()}) == 5
    _ids = list(reference)
    _labels = np.array([int(reference[i][1]) for i in _ids])
    _majority = []
    for _id in _ids:
        _train = [int(label) for fold, label in reference.values() if fold != reference[_id][0]]
        _majority.append(int(sum(_train) > len(_train) / 2))
    baseline_rows = [
        {"Reference": name, "F1": float(f1_score(_labels, pred, zero_division=0))}
        for name, pred in (("Training-fold majority", _majority),
                           ("Always positive", np.ones(len(_labels))))
    ]
    return baseline_rows, score_rows


@app.cell(hide_code=True)
def _(alt, baseline_rows, mo, positive_class, score_rows):
    _main_names = {"Formula · logistic", "Formula + PCA · logistic",
                   "Morgan bits · logistic", "Morgan bits · random forest"}
    _main = [r for r in score_rows if r["Model"] in _main_names]
    _chart = alt.Chart(alt.Data(values=_main)).mark_bar(
        color="#377b81", cornerRadiusEnd=4, size=23,
    ).encode(
        y=alt.Y("Model:N", sort="-x", title=None),
        x=alt.X("F1:Q", scale=alt.Scale(domain=[0, 1]), title="Scaffold-held-out F1"),
        tooltip=[alt.Tooltip("Model:N"), alt.Tooltip("F1:Q", format=".3f")],
    ).properties(height=165, width="container").configure_view(stroke=None)
    mo.vstack([
        mo.ui.altair_chart(_chart, chart_selection=False, legend_selection=False),
        mo.ui.table(_main, selection=None, pagination=False, show_search=False, show_download=False,
                    format_mapping={k: "{:.3f}" for k in ("F1", "Precision", "Recall", "Balanced accuracy")},
                    label=f"Positive class: {positive_class}"),
        mo.ui.table(baseline_rows, selection=None, pagination=False, show_search=False, show_download=False, format_mapping={"F1": "{:.3f}"}),
        mo.accordion({"Feature-removal controls": mo.ui.table(
            [r for r in score_rows if r["Model"] not in _main_names], selection=None,
            pagination=False, format_mapping={k: "{:.3f}" for k in ("F1", "Precision", "Recall", "Balanced accuracy")},
        )}),
    ], gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observation.** In the 171-compound selection, formula logistic separates
    the groups strongly. In the 73-compound activity pool, Morgan logistic F1 is
    **0.727**, close to the always-positive reference (**0.719**). The apparent
    success depends on which question and baseline I use.

    ## 3 · Which logistic weights drive that separation?

    For formula logistic, **log-odds = intercept + Σ βⱼzⱼ**, where z is a feature
    standardized using its training fold. A positive β moves toward the selected
    positive class; a negative β moves away. Larger |β| means a larger conditional
    contribution per training standard deviation. For one fitted model, exp(β)
    is the corresponding odds multiplier.

    Below I inspect the original formula features, **without PCA**. PCA weights
    belong to mixtures of features. Morgan logistic uses unscaled binary bits;
    its bit weights are not exported in these bundles.
    """)
    return


@app.cell(hide_code=True)
def _(alt, mo, np, positive_class, selected):
    _groups = {}
    for _row in selected["coefficients"]:
        _groups.setdefault(_row["feature"], []).append(float(_row["coefficient"]))
    assert len(_groups) == 27 and all(len(v) == 5 for v in _groups.values())
    weight_rows = sorted([
        {"Feature": {"element_count": "Distinct elements", "atom_count": "Total atoms",
                     "other_atom_count": "Other atoms"}.get(
                         feature, feature.removeprefix("formula_").replace("_", " ")),
         "β": float(np.mean(values)), "Fold SD": float(np.std(values)),
         "Positive folds / 5": sum(v > 0 for v in values),
         "Low": float(np.mean(values) - np.std(values)),
         "High": float(np.mean(values) + np.std(values))}
        for feature, values in _groups.items()
    ], key=lambda r: abs(r["β"]), reverse=True)
    _top = weight_rows[:10]
    _base = alt.Chart(alt.Data(values=_top)).encode(
        y=alt.Y("Feature:N", sort=alt.SortField(field="β", order="descending"), title=None),
    )
    _bars = _base.mark_bar(size=15).encode(
        x=alt.X("β:Q", title="Mean standardized weight · whisker = ±1 fold SD"),
        color=alt.condition("datum['β'] > 0", alt.value("#377b81"), alt.value("#bd7651")),
        tooltip=["Feature:N", alt.Tooltip("β:Q", format=".3f"),
                 alt.Tooltip("Fold SD:Q", format=".3f"), "Positive folds / 5:Q"],
    )
    _plot = (_bars + _base.mark_rule(color="#34454b").encode(x="Low:Q", x2="High:Q"))
    mo.vstack([
        mo.ui.altair_chart(_plot.properties(height=260, width="container").configure_view(stroke=None),
                          chart_selection=False, legend_selection=False),
        mo.accordion({"All 27 feature weights": mo.ui.table(
            [{k: v for k, v in r.items() if k not in ("Low", "High")} for r in weight_rows],
            selection=None, pagination=False, show_search=False, show_download=False, format_mapping={"β": "{:.3f}", "Fold SD": "{:.3f}"},
            label=f"Raw-formula logistic · positive class: {positive_class}",
        )}),
    ], gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Weight notes.** In the original selection, nitrogen count averages **+1.293**,
    chlorine **+0.938**, and oxygen **−0.548**. Their signs agree in all five folds.
    Change the experiment above to see whether that pattern survives a new target.

    Counts, fractions and total atoms are correlated: these weights describe the
    fitted model, not the effect of adding an atom. Fold SD is descriptive, not a
    confidence interval or significance test. I would use ablations to investigate
    feature dependence before proposing a chemical explanation.

    ## 4 · Random forest: out-of-bag feature evidence

    I use **OOB permutation F1 loss**, rather than impurity importance, to examine
    feature relevance. Each tree predicts rows absent from its bootstrap sample.
    For each bit, I shuffle that bit within each tree's OOB rows and recombine
    the votes: **ΔF1 = original OOB F1 − shuffled OOB F1**.

    A larger positive drop means the fitted forest relies more on that bit.
    Zero means no observed loss; a negative drop means shuffling helped.
    """)
    return


@app.cell(hide_code=True)
def _(mo, selected):
    _oob = selected["oob_importance"]
    assert len(_oob) == 2048 and len({r["feature"] for r in _oob}) == 2048
    assert len({r["baseline_oob_f1"] for r in _oob}) == 1
    _top = sorted(_oob, key=lambda r: float(r["mean_f1_drop"]), reverse=True)[:10]
    mo.vstack([
        mo.hstack([
            mo.stat(f"{float(next(r['f1'] for r in selected['reports'] if r['profile'] == 'morgan_forest')):.3f}",
                    label="Scaffold-held-out forest F1", bordered=True),
            mo.stat(f"{float(_oob[0]['baseline_oob_f1']):.3f}", label="OOB F1 · diagnostic fit",
                    caption=f"{_oob[0]['repeats']} shuffles/bit · at least {_oob[0]['min_oob_votes']} OOB votes/row",
                    bordered=True),
        ], widths="equal"),
        mo.ui.table([{
            "Morgan bit": r["feature"].removeprefix("morgan_bit_"),
            "Mean ΔF1": float(r["mean_f1_drop"]), "Shuffle SD": float(r["std_f1_drop"]),
        } for r in _top], selection=None, pagination=False, show_search=False, show_download=False,
            format_mapping={"Mean ΔF1": "{:.4f}", "Shuffle SD": "{:.4f}"},
            label="Ten largest OOB F1 losses · all 2,048 bits retained in the source"),
    ], gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Significance check.** These saved OOB results measure importance; they do
    **not provide formal significance or p-values**. The ten-shuffle SD measures
    permutation variability, not uncertainty across independent datasets. I cannot
    label a bit statistically significant from this table. Testing that would
    require a specified null procedure and correction for testing 2,048 bits.

    OOB omits individual rows, not whole scaffolds, so its F1 answers a weaker
    generalization question. I use scaffold-held-out F1 for model performance.
    A hashed Morgan bit can represent several environments; I need to map those
    environments before assigning a chemical meaning.

    ## 5 · Does the activity model survive a new paper?

    I kept the three profiles fixed and tested the recovered radish root-growth
    series at **100 µM, 120 h**: 20 labeled compounds, only **2 high responses**.
    Seven intermediate responses remain unknown. The original 73 compounds form
    training; the shared-scaffold sensitivity removes 21 training compounds.
    """)
    return


@app.cell(hide_code=True)
def _(
    confusion_matrix,
    f1_score,
    mo,
    model_names,
    transfer_predictions,
    transfer_reports,
):
    transfer_rows = []
    for _report in transfer_reports:
        if _report["publication"] != "Flavonoids2012":
            continue
        _rows = [r for r in transfer_predictions if all(
            r[k] == _report[k] for k in ("publication", "scenario", "profile"))]
        _y = [int(r["label"]) for r in _rows]
        _pred = [float(r["probability"]) >= 0.5 for r in _rows]
        assert len(_rows) == int(_report["test_n"])
        assert abs(f1_score(_y, _pred, zero_division=0) - float(_report["f1"])) < 1e-12
        assert list(confusion_matrix(_y, _pred, labels=[0, 1]).ravel()) == [
            int(_report[k]) for k in ("tn", "fp", "fn", "tp")]
        assert abs(f1_score(_y, [int(r["baseline_prediction"]) for r in _rows])
                   - float(_report["baseline_f1"])) < 1e-12
        transfer_rows.append({
            "Test": "New paper" if _report["scenario"] == "publication_only" else "+ shared scaffolds removed",
            "Model": model_names[_report["profile"]], "F1": float(_report["f1"]),
            "Majority F1": float(_report["baseline_f1"]),
            "TP / FP / FN / TN": " / ".join(_report[k] for k in ("tp", "fp", "fn", "tn")),
        })
    mo.ui.table(transfer_rows, selection=None, pagination=False, show_search=False, show_download=False,
                format_mapping={"F1": "{:.3f}", "Majority F1": "{:.3f}"},
                label="Publication-held-out activity test · fixed cutoff 0.50")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observation.** All three models have **F1 = 0** on the primary new-paper
    test: each misses both high responses. Purging shared scaffolds changes the
    predictions sharply but does not establish reliable transfer. Assay mismatch,
    source chemistry and class balance remain entangled.

    ## 6 · What I would try next

    - Expand both response classes under one compatible assay policy, with new
      scaffold groups and an untouched study for testing.
    - Inspect formula ablations and map the strongest OOB bits to actual molecular
      environments. Keep feature importance separate from statistical significance.
    - Keep measured toxicity and outside-model toxicity estimates separate;
      selection-model scores cannot establish efficacy, safety or binding.

    ### Sources and execution notes

    Repository references:
    `analysis/professor_followup.py` (profiles), `analysis/oob.py` (OOB calculation),
    `analysis/structure.py` (features), `analysis/docs/human-review.md` (cohorts),
    `analysis/docs/experimental-expansion-2026-11-12.md` (activity and transfer),
    `analysis/docs/modeled-evidence.md` (toxicity), and
    `analysis/docs/binding-evidence.md` (binding).

    This notebook reads frozen local results and checks their hashes, common
    cohorts/folds, scaffold separation and displayed F1 scores. It fits no new
    models. The file inventory below identifies the exact bundles; these ignored
    research assets are required in this checkout.

    Open from the repository root:
    `uv run --project analysis --locked marimo edit notes/notebooks/presentation_essentials.py`
    """)
    return


@app.cell(hide_code=True)
def _(mo, verified_files):
    mo.accordion({"Frozen input inventory": mo.ui.table(
        verified_files, selection=None, pagination=False, show_search=False, show_download=False,
    )})
    return


if __name__ == "__main__":
    app.run()
