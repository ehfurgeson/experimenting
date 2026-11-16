"""Local professor review: structural models, scientific goals and readiness."""
# Explicit returns are part of marimo's serialized cell format.
# ruff: noqa: PLR1711
import marimo

__generated_with = "0.25.2"
app = marimo.App(width = "full", app_title = "Professor review · structure to activity")


@app.cell
def _():
    import sys
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import polars as pl

    notebook_dir = Path(mo.notebook_location())
    sys.path.insert(0, str(notebook_dir))
    from review_support import (
        FEATURES,
        PROFILES,
        cohort_features,
        comparison_rows,
        ecdf_rows,
        load_review,
        oof_metrics,
    )
    root = notebook_dir.parents[1]
    return (
        FEATURES, PROFILES, alt, cohort_features, comparison_rows, ecdf_rows,
        load_review, mo, oof_metrics, pl, root,
    )


@app.cell
def _(load_review, mo, root):
    mo.stop(
        not (root / "analysis/outputs/ablations-nested-2026-10-29-final/manifest.json").exists(),
        mo.md("""## Local research bundles are missing
        This notebook reads existing structural, stress, ablation and ChEMBL review
        bundles under `analysis/outputs/`. It does not acquire evidence or regenerate
        frozen results. Obtain the local bundle described in `docs/data.md` first.
        """),
    )
    frames, audit, label_source = load_review(root)
    return audit, frames, label_source


@app.cell
def _(cohort_features, comparison_rows, frames, pl):
    common_features = cohort_features(frames)
    comparisons = comparison_rows(frames)
    working_labels = frames["working_labels"]
    label_counts = {
        key: working_labels.filter(pl.col(key).is_in(values)).height
        for key, values in {
            "herbicidal_activity": ["active", "inactive"],
            "natural_origin": ["natural", "synthetic"],
        }.items()
    }
    return common_features, comparisons, label_counts, working_labels


@app.cell
def _(audit, common_features, label_counts, mo, working_labels):
    mo.vstack([
        mo.md("""
        # Structure is ready. Activity ground truth is the next gate.
        ### Professor review · 3 November 2026
        A local, read-only review of the existing **27–29 October** model runs,
        mapped to today's questions. New charts summarize saved outputs; no model
        has been retrained, no labels inferred, and no source evidence overwritten.

        **The honest conclusion:** the repository has a working structure-only
        selection classifier and most requested chemical features. It has not yet
        demonstrated a classifier for herbicidal activity in natural products.
        Strong selection accuracy does not close that scientific gap.
        """),
        mo.hstack([
            mo.stat(label = "Matched structural cohort", value = common_features.height),
            mo.stat(label = "Reviewed activity labels in working pack", value = label_counts["herbicidal_activity"]),
            mo.stat(label = "Working label rows", value = working_labels.height),
            mo.stat(label = "Provenance checks recorded", value = audit.height),
        ], justify = "start", gap = 3),
        mo.md("""
        Navigate: [Goal assessment](#1-goal-assessment) · [Formula/features](#2-formula-and-chemical-features)
        · [Fair model comparison](#3-fair-model-comparison) · [Held-out errors](#4-inspect-held-out-errors)
        · [Dimensionality/stress](#5-dimensionality-and-stress-tests) · [Labels](#6-the-label-bottleneck)
        · [Expansion sources](#7-expansion-sources-and-sequencing) · [Meeting decisions](#8-decisions-for-today)
        """),
    ])
    return


@app.cell
def _(frames, label_counts, mo, pl):
    _goals = [
        {"Professor's request": "Classifier using structure without toxicity", "Progress": "Implemented prototype",
         "Evidence": "Formula / RDKit descriptors / Morgan / combined models; predictors are allowlisted chemistry only",
         "Remaining": "Validate reviewed herbicidal activity, rather than curated selection membership"},
        {"Professor's request": "Number of different elements from formula", "Progress": "Implemented",
         "Evidence": "element_count plus atom counts/fractions and full-composition identity audit",
         "Remaining": "Its standalone predictive contribution has not been isolated by these frozen runs"},
        {"Professor's request": "Is formula indicative of herbicide or natural selection?", "Progress": "Supported in this selection",
         "Evidence": "Formula composition performs strongly in scaffold-held-out selection evaluation",
         "Remaining": "Curation/elemental composition bias and overlap; not proof of origin or activity"},
        {"Professor's request": "Dimension reduction for features ≫ compounds", "Progress": "Implemented, assessed",
         "Evidence": "Fold-local scaling/variance filtering/PCA at 95% training variance; nested regularization and ablations",
         "Remaining": "Many fingerprint components remain; independent validation still needed"},
        {"Professor's request": "Rules analogous to Tice / Lipinski", "Progress": "Proxies implemented; new rule unfinished",
         "Evidence": "Lipinski and explicit Tice-inspired violation counts; distributions can be inspected below",
         "Remaining": "No new independently validated agrochemical-vs-natural or activity rule set has been learned"},
        {"Professor's request": "Synthetic accessibility", "Progress": "Implemented heuristic",
         "Evidence": "RDKit bundled Ertl SA score from molecular structure",
         "Remaining": "Not a synthesis route, cost estimate, activity label or validation of practical manufacturability"},
        {"Professor's request": "Longer herbicide / natural-compound lists", "Progress": "Sources assessed; bounded assay acquisition done",
         "Evidence": "HRAC, COCONUT, LOTUS, KNApSAcK assessed; 14 ChEMBL assays / 157 measurements / 154 structures",
         "Remaining": "Versioned broader roster/import and reviewed actives + tested negatives; no full NP library imported"},
        {"Professor's request": "Natural actives / natural inactives classifier, then large screen", "Progress": "Scientific data gate unmet",
         "Evidence": f"{label_counts['herbicidal_activity']} known activity labels in the inspected working pack; scoring machinery exists",
         "Remaining": "Agree assay policy, curate sufficient diverse positives/negatives, reserve independent validation, then scale"},
    ]
    _toxicity_context = mo.md("Prepared toxicity context unavailable; see the original professor notebook.")
    if "presentation/traits" in frames:
        _traits = frames["presentation/traits"]
        _coverage = []
        for _source, _prefix in [("PubChem", "has_pubchem_"), ("EPA", "has_epa_"), ("Either source", "has_")]:
            for _policy in ["mammal_oral_ld50", "fish_lc50", "trout_lc50_96h", "daphnia_ec50_48h", "mammal_oral_noael_daily", "mammal_oral_loael_daily", "mammal_oral_bmd_daily", "mammal_oral_bmdl_daily"]:
                for _group in ["herbicide", "natural_product"]:
                    _subset = _traits.filter(pl.col("chemical_group") == _group)
                    _values = _subset[_prefix + _policy]
                    _coverage.append({"source": _source, "policy": _policy, "group": _group,
                                      "selected_n": _subset.height, "assessed_n": _values.count(),
                                      "eligible_n": int((_values == 1).sum())})
        _toxicity_context = mo.vstack([
            mo.md(f"**{_traits.height} prepared compounds** in the older evidence presentation. Counts below describe eligible saved evidence, not toxicity potency. Chronic example policies deliberately leave pooled potency medians null. This cohort differs from the 171-compound structural ablations; these source flags never enter structural predictors."),
            mo.ui.table(_coverage, selection = None, page_size = 8),
        ])
    mo.vstack([
        mo.md("""## 1 · Goal assessment
        Status is reported by deliverable and evidence. A completion percentage
        would conceal that implemented software and validated biological prediction
        are different milestones.
        """),
        mo.ui.table(_goals, selection = None, pagination = False, wrapped_columns = ["Professor's request", "Evidence", "Remaining"]),
        mo.accordion({"Overall repository goals — beyond the structural meeting requests": mo.md("""
        **Toxicity profiles and differentiating properties:** reusable acquisition,
        normalization, seven-endpoint structured EPA support, missingness-aware
        coverage, descriptive comparisons and presentation are implemented.
        Comparing matched potency across all endpoints and concluding relative safety
        remain unfinished: aquatic evidence is sparse and study context heterogeneous.

        **Known natural-product–protein binding:** reference target/protein/resistance
        tables and literature context exist. A source-reviewed interaction dataset
        and validated binding-characterization workflow remain open. Plant-growth
        inhibition and selection classification do not establish direct protein binding.

        **Safer bioherbicide discovery:** features and exploratory models support the
        path toward the goal. Accepted efficacy, independent validation, non-target
        hazard profiles and practical follow-up are still needed. No safer candidate
        or deployment-ready model has been established.
        """), "Toxicity-profile evidence from the prepared cohort": _toxicity_context}),
    ])
    return


@app.cell
def _(FEATURES, mo):
    _intro = mo.md("""## 2 · Formula and chemical features
    **Formula model ≠ element-count-only model.** The existing formula representation
    contains 27 composition predictors: distinct elements, total atoms, other atoms,
    and counts/fractions for 12 named elements. Isomers can share every formula feature.
    SMILES supplies connectivity/fingerprints; InChIKey is an identity audit key,
    never a numeric predictor. Toxicity is not required to derive these predictors.
    """)
    feature_choice = mo.ui.dropdown(FEATURES, value = "Distinct elements", label = "Feature", allow_select_none = False)
    cohort_choice = mo.ui.dropdown(
        {"Matched model cohort (171)": True, "All structurally valid rows (174)": False},
        value = "Matched model cohort (171)", label = "Feature population", allow_select_none = False,
    )
    mo.vstack([_intro, mo.hstack([feature_choice, cohort_choice], justify = "start")])
    return cohort_choice, feature_choice


@app.cell
def _(alt, cohort_choice, cohort_features, ecdf_rows, feature_choice, frames, mo, pl):
    _features = cohort_features(frames, cohort_choice.value)
    _key = feature_choice.value
    _rows = ecdf_rows(_features, _key)
    _chart = alt.Chart(alt.Data(values = _rows)).mark_line(interpolate = "step-after").encode(
        x = alt.X("value:Q", title = feature_choice.selected_key),
        y = alt.Y("fraction:Q", title = "Fraction at or below value", scale = alt.Scale(domain = [0, 1])),
        color = alt.Color("group:N", title = "Selection group", scale = alt.Scale(
            domain = ["herbicide", "natural_product"], range = ["#3465a4", "#14866d"],
        )), tooltip = ["group:N", "value:Q", alt.Tooltip("fraction:Q", format = ".1%"), "n:Q"],
    ).properties(height = 280, width = 660)
    _summary = _features.group_by("chemical_group").agg(
        pl.col(_key).count().alias("finite_n"), pl.col(_key).median().alias("median"),
        pl.col(_key).min().alias("min"), pl.col(_key).max().alias("max"),
    ).sort("chemical_group")
    mo.vstack([mo.ui.altair_chart(_chart, chart_selection = False, legend_selection = False),
               mo.ui.table(_summary, selection = None, pagination = False),
               mo.md("Features with unsupported formulas remain missing; denominator is shown per group. Curves describe selection, not biological activity.")])
    return


@app.cell
def _(common_features, mo, pl):
    _elements = []
    for _element in ("N", "Cl", "F", "S", "P"):
        for _group in ("herbicide", "natural_product"):
            _subset = common_features.filter(pl.col("chemical_group") == _group)
            _present = _subset.filter(pl.col(f"formula_{_element}_count") > 0).height
            _elements.append({"element": _element, "selection": _group, "present": _present,
                              "n": _subset.height, "fraction": round(_present / _subset.height, 3)})
    mo.accordion({
        "Elemental composition contrasts — curation signal, not causation": mo.ui.table(_elements, selection = None, pagination = False),
        "Screening-rule definitions and synthetic accessibility": mo.md("""
        **Implemented Lipinski violation count:** MW > 500, RDKit logP > 5,
        H-bond donors > 5, acceptors > 10. It is an oral-drug screening heuristic,
        not a herbicidal activity label.

        **Implemented Tice-inspired proxy:** MW outside 150–500, logP > 3.5,
        donors > 3, acceptors outside 2–12, rotatable bonds > 12. Definitions
        are explicitly RDKit-based; exact reproduction of Tice's original calculators
        has not been established. The current code does not create a new validated rule set.

        **Synthetic accessibility:** Ertl fragment/complexity heuristic through RDKit's
        bundled SA scorer; lower values suggest easier synthesis, higher harder.
        Natural extraction, supply, synthesis route, yield and cost require other evidence.
        [Primary SA method](https://link.springer.com/article/10.1186/1758-2946-1-8).

        **A reasonable next rule experiment:** predeclare a shallow model or small
        rule family, learn thresholds only inside training folds, and validate on
        independent chemistry/activity labels. Do not choose a cutoff from the
        complete distributions here and present its resubstitution score as validation.
        """),
    })
    return


@app.cell
def _(mo):
    _intro = mo.md("""## 3 · Fair model comparison
    These are the **same 171 compounds, 55 selected herbicides / 116 selected natural
    products, and the same five scaffold folds** for all nine profiles and both modes.
    Positive means membership in the selected-herbicide group. Every predictor is
    finite in this ablation cohort; zero input values were imputed.

    **Fixed:** C=1. **Nested:** C selected over 0.01, 0.1, 1, 10, 100 within three
    inner scaffold folds in each outer training set. All reported scores are outer
    held-out predictions. Choosing a profile after inspecting these scores is still
    exploratory. No confidence interval or external confirmation is supplied by these runs.
    """)
    metric_choice = mo.ui.dropdown(
        {"Balanced accuracy": "balanced_accuracy", "ROC-AUC": "roc_auc", "Average precision": "average_precision"},
        value = "Balanced accuracy", label = "Held-out metric", allow_select_none = False,
    )
    mo.vstack([_intro, metric_choice])
    return (metric_choice,)


@app.cell
def _(alt, comparisons, metric_choice, mo, pl):
    _metric = metric_choice.value
    _baseline = 55 / 171 if _metric == "average_precision" else 0.5
    _chart = alt.Chart(alt.Data(values = comparisons.to_dicts())).mark_bar().encode(
        y = alt.Y("profile_label:N", title = None, sort = list(comparisons["profile_label"].unique(maintain_order = True))),
        x = alt.X(f"{_metric}:Q", scale = alt.Scale(domain = [0, 1]), title = metric_choice.selected_key),
        yOffset = "mode:N", color = alt.Color("mode:N", scale = alt.Scale(
            domain = ["fixed", "nested"], range = ["#9aa9bc", "#3465a4"],
        )), tooltip = ["profile_label:N", "mode:N", alt.Tooltip(f"{_metric}:Q", format = ".4f"), "n:Q", "tp:Q", "fp:Q", "fn:Q", "tn:Q"],
    )
    _rule = alt.Chart(alt.Data(values = [{"baseline": _baseline}])).mark_rule(strokeDash = [4, 4], color = "#b25d39").encode(x = "baseline:Q")
    mo.vstack([
        mo.ui.altair_chart((_chart + _rule).properties(width = 680, height = 430), chart_selection = False, legend_selection = False),
        mo.md(f"Dashed reference = {_baseline:.3f}: {'positive prevalence as a no-skill AP reference' if _metric == 'average_precision' else '0.5 ranking/balanced-accuracy reference'}. Average precision depends on prevalence."),
        mo.accordion({"Exact saved outer-held-out metrics": mo.ui.table(comparisons.select(
            "profile_label", "mode", "n", "balanced_accuracy", "roc_auc", "average_precision", "tp", "fn", "fp", "tn",
        ), selection = None, page_size = 9)}),
        mo.md("""**Interpretation:** formula + descriptors at fixed C gains only one
        net selected-herbicide detection over formula alone. Preserving formula outside
        PCA does not by itself recover the gap. Nested C substantially improves the
        combined model, suggesting regularization/operating-point behavior matters.
        These comparisons do not identify a validated biological activity winner.
        """),
    ])
    return


@app.cell
def _(PROFILES, mo):
    _intro = mo.md("""## 4 · Inspect held-out errors
    Explore saved out-of-fold predictions. At the default **0.50** threshold the
    confusion counts reproduce the saved reports. Changing the slider explores
    sensitivity on these same outcomes; selecting a threshold here would need
    separate validation. Probabilities are uncalibrated selection scores.
    """)
    mode_choice = mo.ui.dropdown(["fixed", "nested"], value = "nested", label = "Regularization", allow_select_none = False)
    profile_choice = mo.ui.dropdown({v: k for k, v in PROFILES.items()}, value = "Formula · PCA", label = "Profile", allow_select_none = False)
    threshold = mo.ui.slider(start = 0.05, stop = 0.95, step = 0.05, value = 0.5, label = "Selection-score threshold", show_value = True)
    mo.vstack([_intro, mo.hstack([mode_choice, profile_choice, threshold], justify = "start")])
    return mode_choice, profile_choice, threshold


@app.cell
def _(alt, frames, mo, mode_choice, oof_metrics, pl, profile_choice, threshold):
    _rows = frames[f"{mode_choice.value}/out_of_fold"].filter(pl.col("profile") == profile_choice.value)
    _metrics = oof_metrics(_rows, threshold.value)
    _confusion = [
        {"actual": "Selected natural", "predicted": "Selected natural", "count": _metrics["tn"]},
        {"actual": "Selected natural", "predicted": "Selected herbicide", "count": _metrics["fp"]},
        {"actual": "Selected herbicide", "predicted": "Selected natural", "count": _metrics["fn"]},
        {"actual": "Selected herbicide", "predicted": "Selected herbicide", "count": _metrics["tp"]},
    ]
    _base = alt.Chart(alt.Data(values = _confusion)).encode(x = alt.X("predicted:N", title = "Predicted selection"), y = alt.Y("actual:N", title = "Actual selection"))
    _heatmap = _base.mark_rect().encode(color = alt.Color("count:Q", scale = alt.Scale(range = ["#eff5fd", "#a8c5ee"])), tooltip = ["actual:N", "predicted:N", "count:Q"])
    _text = _base.mark_text(fontSize = 22, color = "#17253b").encode(text = "count:Q")
    _errors = _rows.with_columns((pl.col("probability") >= threshold.value).cast(pl.Int64).alias("predicted"))
    _errors = _errors.filter(pl.col("predicted") != pl.col("label")).join(
        frames["baseline/structural_features"].select("compound_id", "query", "derived_formula", "element_count", "sa_score", "canonical_structure"),
        on = "compound_id", how = "left",
    ).sort("probability", descending = True)
    mo.vstack([
        mo.hstack([mo.stat(label = "Balanced accuracy", value = f"{_metrics['balanced_accuracy']:.1%}"),
                   mo.stat(label = "ROC-AUC (threshold-independent)", value = f"{_metrics['roc_auc']:.3f}"),
                   mo.stat(label = "Selection errors", value = _errors.height)], justify = "start", gap = 3),
        mo.ui.altair_chart((_heatmap + _text).properties(width = 400, height = 200), chart_selection = False, legend_selection = False),
        mo.ui.table(_errors.select("query", "compound_id", "derived_formula", "element_count", "sa_score", "label", "predicted", "probability", "fold", "scaffold"), selection = None, page_size = 7),
        mo.md("A selected natural product called 'herbicide' is a selection error; it is not proof of either herbicidal activity or inactivity."),
    ])
    return


@app.cell
def _(alt, frames, mo, pl):
    _folds = []
    for _mode in ("fixed", "nested"):
        for _row in frames[f"{_mode}/folds"].to_dicts():
            _folds.append({**_row, "mode": _mode})
    _dims = pl.DataFrame(_folds)
    _summary = _dims.group_by("profile", "mode").agg(
        pl.col("model_features").max().alias("max_model_inputs"),
        pl.col("pca_components").max().alias("max_pca_components"),
        pl.col("preserved_features").max().alias("preserved_inputs"),
        pl.col("train_n").min().alias("smallest_outer_training_n"),
        pl.col("selected_c").unique().sort().alias("selected_C_values"),
    ).sort("profile", "mode")
    _stress = frames["stress/stress_models"]
    _actual = _stress.filter(pl.col("scenario") != "shuffled_labels")
    _shuffled = _stress.filter(pl.col("scenario") == "shuffled_labels").group_by("representation").agg(
        pl.col("balanced_accuracy").mean().alias("shuffled_mean"),
        pl.col("balanced_accuracy").min().alias("shuffled_min"),
        pl.col("balanced_accuracy").max().alias("shuffled_max"), pl.len().alias("controls"),
    )
    _chart = alt.Chart(alt.Data(values = _actual.to_dicts())).mark_point(filled = True, size = 80).encode(
        x = alt.X("balanced_accuracy:Q", title = "Held-out balanced accuracy", scale = alt.Scale(domain = [0, 1])),
        y = alt.Y("representation:N", title = None), color = "scenario:N", tooltip = ["scenario:N", "representation:N", "n:Q", "balanced_accuracy:Q"],
    ).properties(width = 660, height = 200)
    mo.vstack([
        mo.md("""## 5 · Dimensionality and stress tests
        Formula starts with 27 predictors, descriptors 11, Morgan fingerprints 2,048,
        and the original combined input 2,086. Variance filtering, scaling and PCA
        are learned within training folds. PCA retains 95% of training variance;
        it is unsupervised and may discard predictive low-variance directions.

        Fingerprint PCA can still leave about a hundred components for fewer than
        171 training compounds. Dimensionality is managed, not solved. All
        fingerprint-containing nested profiles hit the tested C-grid boundary of
        100 in every outer fold; this is not evidence of a global optimum.
        """),
        mo.accordion({"Fold-local dimensions and C choices": mo.ui.table(_summary, selection = None, page_size = 9),
                      "Every outer fold: training versus held-out performance": mo.ui.table(_dims, selection = None, page_size = 10)}),
        mo.ui.altair_chart(_chart, chart_selection = False, legend_selection = False),
        mo.ui.table(_shuffled, selection = None, pagination = False),
        mo.md("Twenty shuffled-label controls per representation hover around chance. Removing the largest scaffold changes the cohort (171 → 122), so that stress result is not a same-population model comparison. These checks expose fragility; they do not supply external activity validation."),
    ])
    return


@app.cell
def _(frames, label_counts, label_source, mo, pl, working_labels):
    _measurements = frames["review/activity_review"]
    _structure_states = frames["baseline/structural_features"].group_by("structure_status", "formula_status").len()
    _review_states = frames["review_screen/structure_models"].select("target", "representation", "n", "status", "balanced_accuracy")
    _axis = working_labels.group_by("natural_origin", "herbicidal_activity").len()
    _assays = _measurements.group_by("assay_chembl_id", "assay_organism", "standard_type", "standard_units").len()
    mo.vstack([
        mo.md(f"""## 6 · The label bottleneck
        The frozen review export has **{_measurements.height} measurements** from
        **{_measurements['assay_chembl_id'].n_unique()} assays / {_measurements['document_chembl_id'].n_unique()} publications**.
        The working worksheet has **{working_labels.height} compound rows**;
        **{label_counts['herbicidal_activity']}** have known activity and
        **{label_counts['natural_origin']}** known origin in the inspected copy.
        These are source-specific counts, not a census of all research labels.

        **The requested categories overlap.** A natural product can be herbicidal.
        Use separate axes: natural occurrence/provenance and plant activity under
        an agreed assay policy. A useful future model can predict activity for a
        known natural product without pretending 'natural' is its opposite class.
        """),
        mo.ui.table([
            {"Origin": "Natural", "Activity": "Active", "Need": "Cited natural occurrence + comparable positive plant assay"},
            {"Origin": "Natural", "Activity": "Tested inactive", "Need": "Cited occurrence + adequate exposure/controls under the same policy"},
            {"Origin": "Synthetic / other reviewed provenance", "Activity": "Active or tested inactive", "Need": "Explicit provenance and activity evidence; marketed use does not alone define assay response"},
            {"Origin": "Unknown", "Activity": "Unknown", "Need": "Keep unknown until reviewed; database membership/absence is not a negative assay"},
        ], selection = None, pagination = False),
        mo.accordion({
            "Working label coverage": mo.ui.table(_axis, selection = None),
            "Why activity/origin model reports are unavailable": mo.ui.table(_review_states, selection = None, page_size = 8),
            "Assay contexts: why raw response bands need review": mo.ui.table(_assays, selection = None, page_size = 7),
            "Identity/feature exclusions in the original cohort": mo.ui.table(_structure_states, selection = None),
        }),
        mo.md(f"Working labels read from `{label_source}`. The notebook never modifies them. Use the tracked `analysis/docs/label_review_guide.md` to adjudicate publication methods, dose/time/species, inequalities, conflicts and occurrence separately. Unknown or untested is not inactive."),
    ])
    return


@app.cell
def _(mo):
    mo.vstack([
        mo.md("""## 7 · Expansion sources and sequencing
        Source pages rechecked **3 November 2026**. No bulk collection has been
        imported by this notebook. A large unlabeled library increases candidate
        coverage; it does not manufacture reviewed activity ground truth.
        """),
        mo.md("""
        | Source | Suitable next use | Current repository gap |
        | --- | --- | --- |
        | [HRAC 2026 master list](https://hracglobal.com/tools/2026-hrac-global-herbicide-moa-classification) | Extend recognized herbicide identities/MoA; XLSX with/without structures | Freeze roster and review salts/esters/stereo; not a standardized active/inactive assay dataset |
        | [COCONUT downloads](https://coconut.naturalproducts.net/download) | Versioned natural-product structure library; page now offers **November 2026** CSV/SDF and CC0 release | No full import/batch scorer yet; database 'active/inactive' terminology is not herbicidal ground truth |
        | [LOTUS primary description](https://elifesciences.org/articles/70780), [portal](https://lotus.naturalproducts.net/) | Referenced structure–organism relationships for occurrence and literature leads | Freeze export/query and review provenance; occurrence does not imply activity; portal content was not text-readable in this check |
        | [KNApSAcK Core](https://www.knapsackfamily.com/knapsack_core/top.php) | Targeted metabolite/species/structure searches and references | Broader acquisition remains unimplemented; source page restricts redistribution/commercial use without contact; establish an appropriate access/reuse route |
        | Frozen ChEMBL plant assays / PubChem BioAssay literature leads | Reviewed comparable actives and tested negatives before broad screening | 14 assays acquired; original-paper context and label adjudication still needed |

        **Sequence:** agree activity policy → curate diverse actives/tested negatives
        and natural-occurrence evidence → reserve independent chemical/publication
        holdouts → evaluate structure models and calibration → freeze a natural-product
        release → implement bounded batch scoring with identity/provenance/domain checks.

        HRAC and natural-source enrichment can be prepared now. Claims that a model
        'performs well' should use an agreed, independent activity validation criterion,
        not the selection scores above. The existing candidate command loads the
        list in memory and uses pairwise similarity; a full-library batch interface
        is a separate engineering step. See `analysis/docs/compound_sources.md`
        for the original dated source assessment and specific assay leads.
        """),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 8 · Decisions for today
    **Suggested meeting summary:** “We have the structure-only feature/model pipeline,
    including formula composition, PCA, rule proxies and SA. Formula discriminates
    our curated groups well, but that is not yet an activity classifier. We have
    additional measured plant-assay evidence ready for review; the immediate next
    milestone is a defensible activity/origin training set and independent validation.”

    1. **Define the task:** prioritize predicting plant activity in natural candidates;
       maintain natural occurrence as a separate cited label. Is a broad selection
       diagnostic also useful as a secondary research question?
    2. **Agree biological policy:** species/weed, pre/post emergence, endpoint,
       exposure/duration, controls, positive/negative bands, qualifiers and conflicts.
       What would constitute a useful tested negative?
    3. **Choose validation before more model search:** reserve publications/chemotypes,
       agree precision–recall and sensitivity tradeoffs, calibration/domain checks,
       and what evidence would justify broad candidate screening. Scaffold support
       matters more than simply reaching a large row count.
    4. **Decide the next deliverable:** a versioned reviewed-label pilot and its
       audit, then a held-out activity benchmark. For a rule set, predeclare a small
       interpretable candidate family and validate it without whole-dataset threshold picking.
    5. **Keep the broader goals visible:** separate non-target hazard comparison,
       known binding-interaction curation and practical accessibility from efficacy.
       None is completed merely by making the candidate library larger.

    **Readiness:** feature extraction **ready**; internal selection modeling
    **demonstrated, exploratory**; new discriminating rule set **not validated**;
    biological activity training data **requires review**; broad natural-product
    screen **waits on validation and batch engineering**. This gives concrete
    finish criteria without inventing a completion percentage or a safety claim.
    """)
    return


@app.cell
def _(audit, mo):
    _summary = audit.group_by("bundle", "kind", "status").len().sort("bundle", "kind")
    mo.accordion({"Provenance and what was verified for this notebook": mo.vstack([
        mo.md("""The loader checks frozen output hashes before reading CSVs, verifies
        fixed/nested cohort identity and exact outer-fold assignments across profiles,
        rejects scaffold leakage, and recomputes saved metrics from OOF probabilities.
        Input/code/lock matches or drift are displayed below, separately from product
        integrity. Working labels are a live local copy and may legitimately differ
        from their original template. No acquisition, fitting or scientific output
        writes occur during notebook execution. New UI state/cache/export files stay local.
        """),
        mo.ui.table(_summary, selection = None, page_size = 12),
        mo.ui.table(audit, selection = None, page_size = 8),
    ])})
    return


if __name__ == "__main__":
    app.run()
