"""Professor presentation: seven endpoints, chemical traits, and exploratory models."""

import marimo

__generated_with = "0.25.2"
app = marimo.App(width = "full", app_title = "Agrochemical traits and evidence")


@app.cell
def _():
    import os
    from pathlib import Path

    import marimo as mo
    import polars as pl

    from presentation import (
        ENDPOINTS,
        METRICS,
        classifier_chart,
        classifier_rows,
        distribution_chart,
        empirical_distributions,
        endpoint_chart,
        endpoint_distribution,
        load_results,
    )
    return (
        ENDPOINTS, METRICS, Path, classifier_chart, classifier_rows,
        distribution_chart, empirical_distributions, endpoint_chart,
        endpoint_distribution, load_results, mo, os, pl,
    )


@app.cell
def _(Path, load_results, mo, os):
    data_root = Path(os.environ.get("AGROTOX_ANALYSIS_DATA", str(mo.notebook_location() / "data")))
    mo.stop(
        not (data_root / "manifest.json").exists(),
        mo.md("""
        # Prepare the local analysis first
        From the repository root, run:
        ```bash
        uv run --project analysis python analysis/rebuild.py --source experiments/data
        ```
        Use any equivalent source-cache root. Generated data stays ignored.
        """),
    )
    tables, manifest = load_results(data_root)
    traits = tables["traits"]
    comparisons = tables["comparison"]
    models = tables["models"]
    return comparisons, data_root, manifest, models, tables, traits


@app.cell
def _(manifest, mo, pl, traits):
    herbicide_n = traits.filter(pl.col("chemical_group") == "herbicide").height
    natural_n = traits.filter(pl.col("chemical_group") == "natural_product").height
    mo.vstack([
        mo.md(f"""
        # Herbicides and natural compounds
        **Seven toxicity endpoints, molecular traits, and the evidence behind them**

        A descriptive comparison of the project’s curated selection. Prepared
        **{manifest['generated_at'][:10]}** from cached PubChem and EPA evidence.
        This selection is purposive; the plots describe these compounds.
        """),
        mo.hstack([
            mo.stat(label = "Selected compounds", value = traits.height),
            mo.stat(label = "Herbicides", value = herbicide_n),
            mo.stat(label = "Natural compounds", value = natural_n),
        ], justify = "start", gap = 4),
    ])
    return herbicide_n, natural_n


@app.cell
def _(mo):
    mo.md("""
    ## 1 · Toxicity evidence across seven endpoints
    These are **distributions of evidence availability**, rather than distributions
    of toxicity doses. Each bar retains every selected compound in that group.
    A missing record or unassessed source is never evidence that a chemical is safe.
    """)
    return


@app.cell
def _(mo):
    source = mo.ui.dropdown(
        {"Either source": "combined", "EPA hazard": "epa", "PubChem": "pubchem"},
        value = "Either source", label = "Evidence source", allow_select_none = False,
    )
    source
    return (source,)


@app.cell
def _(endpoint_chart, endpoint_distribution, mo, source, traits):
    endpoint_rows = endpoint_distribution(traits, source.value)
    mo.ui.altair_chart(endpoint_chart(endpoint_rows), chart_selection = False, legend_selection = False)
    return (endpoint_rows,)


@app.cell
def _(ENDPOINTS, endpoint_rows, mo, pl):
    _coverage = pl.DataFrame(endpoint_rows).filter(pl.col("state") == "Evidence found").select(
        "endpoint", "group", "count", "selected", "assessed", "fraction",
    )
    mo.vstack([
        mo.md("""
        **Reading the gaps:** NOAEL and LOAEL add substantial chronic evidence.
        BMD is absent in this cache and BMDL is sparse. EPA requires an explicit
        experimental source mark; BMD/BMDL are model-derived points of departure
        from those data. Stored TEST predictions remain separate.

        PubChem prose extraction is acute-only, so its chronic zeros describe an
        extraction limitation. Gray segments include unresolved identities and
        sources not assessed. The union is unknown when neither source is positive
        and one is unassessed. These flags do not establish absence of evidence
        outside the cached sources.
        """),
        mo.accordion({
            "Counts and denominators": mo.ui.table(_coverage, selection = None),
            "Endpoint contexts": mo.ui.table([
                {"Endpoint": e, "Policy": p, "Context": c} for e, p, c in ENDPOINTS
            ], selection = None),
        }),
    ])
    return


@app.cell
def _(comparisons, mo, pl):
    _weight = comparisons.filter(pl.col("trait") == "molecular_weight").row(0, named = True)
    _logp = comparisons.filter(pl.col("trait") == "xlogp").row(0, named = True)
    mo.md(f"""
    ## 2 · The groups differ in chemistry as well as evidence
    The four views below show **whole distributions**, normalized within each
    group. At a given x-value, the curve gives the fraction at or below that value.
    Hover for the finite-value sample size; missing values are excluded.

    In this selection, median molecular weight is **{_weight['median_herbicide']:.1f}
    vs {_weight['median_natural']:.1f} g/mol**, and median XLogP is
    **{_logp['median_herbicide']:.1f} vs {_logp['median_natural']:.1f}**
    (herbicides, then natural compounds). The curves overlap; neither property
    alone is a toxicity or safety score.
    """)
    return


@app.cell
def _(distribution_chart, empirical_distributions, mo, traits):
    mo.ui.altair_chart(
        distribution_chart(empirical_distributions(
            traits, ["molecular_weight", "xlogp", "tpsa", "complexity"],
        )), chart_selection = False, legend_selection = False,
    )
    return


@app.cell
def _(comparisons, mo, pl):
    mo.accordion({
        "Group differences, sample sizes, and uncertainty": mo.vstack([
            mo.md("""
            Median difference = herbicides minus natural compounds. Intervals are
            95% percentile bootstrap intervals. Permutation p-values are unadjusted
            across many traits; these are exploratory descriptions. AUC is the
            probability a herbicide value exceeds a natural-compound value,
            with half-credit for ties. Polarity's interval can cross zero even
            though its point estimate differs.
            """),
            mo.ui.table(comparisons.filter(pl.col("trait").is_in([
                "molecular_weight", "xlogp", "tpsa", "complexity",
            ])), selection = None),
        ]),
    })
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3 · How much was measured is another distribution
    Annotation and hazard-record counts describe the available literature.
    Property counts distinguish measured from calculated records. Equal calculated
    coverage does not mean equal measured evidence—or equal toxicity.
    The horizontal axes below use a symmetric-log scale to retain zeros and long tails.
    """)
    return


@app.cell
def _(distribution_chart, empirical_distributions, mo, traits):
    _study_rows = empirical_distributions(traits, [
        "annotation_count", "epa_hazard_records", "epa_measured_properties", "epa_calculated_properties",
    ])
    mo.stop(not _study_rows, mo.md("Optional study-coverage traits are unavailable in this snapshot."))
    mo.ui.altair_chart(distribution_chart(_study_rows, logarithmic = True),
                       chart_selection = False, legend_selection = False)
    return


@app.cell
def _(classifier_chart, classifier_rows, models, mo, pl):
    _group_fit = models.filter(pl.col("model") == "group_from_structure").row(0, named = True)
    _unavailable = models.filter(pl.col("accuracy").is_null()).height
    mo.vstack([
        mo.md(f"""
        ## 4 · What can a simple classifier explain?
        Molecular descriptors predict **group membership or evidence availability**.
        They do not predict endpoint doses. The group model reaches
        **{_group_fit['accuracy']:.1%}** held-out accuracy versus a
        **{_group_fit['baseline']:.1%}** majority baseline in this snapshot.

        Compare each blue dot with its gray baseline. Some availability models
        add little or no accuracy over the baseline. **{_unavailable} of {models.height}
        targets cannot support five-fold validation**, including BMD and BMDL.
        """),
        mo.ui.altair_chart(classifier_chart(classifier_rows(models)),
                           chart_selection = False, legend_selection = False),
        mo.md("""
        **Method:** L2 logistic regression, stratified five-fold validation, fixed
        seed. Median imputation and scaling are learned on each training fold.
        Missing target labels are excluded; a target needs five examples of each
        class. Coefficients describe full-sample fits and are not causal importance
        scores; molecular descriptors are correlated. Validation is internal to
        this curated selection, not an external generalization test.
        """),
        mo.accordion({"All targets, baselines, and class balance": mo.ui.table(
            models, selection = None, page_size = 10,
        )}),
    ])
    return


@app.cell
def _(METRICS, mo, traits):
    _intro = mo.md("""
    ## 5 · Explore the remaining traits
    More descriptors and assay traits are available below. ToxCast fractions
    depend on which assays tested each compound; different panels can confound
    the comparison. They are not measures of whole-organism safety.
    """)
    extra_trait = mo.ui.dropdown(
        {label: key for key, label in METRICS.items() if key in traits.columns},
        value = "Hydrogen-bond donors", label = "Trait", allow_select_none = False,
    )
    mo.vstack([_intro, extra_trait])
    return (extra_trait,)


@app.cell
def _(distribution_chart, empirical_distributions, extra_trait, mo, traits):
    _extra = empirical_distributions(traits, [extra_trait.value])
    mo.stop(not _extra, mo.md("No finite values for this trait in the selected snapshot."))
    mo.ui.altair_chart(distribution_chart(_extra), chart_selection = False, legend_selection = False)
    return


@app.cell
def _(ENDPOINTS, mo):
    _intro = mo.md("""
    ## 6 · Inspect the actual toxicity observations
    Availability charts above do not replace study-level values. Inspect the
    normalized EPA observations here, keeping units, species, route, duration,
    effect, and benchmark context together. Unknown context stays unknown.
    Chronic example policies do not authorize pooled potency medians.
    """)
    observation_endpoint = mo.ui.dropdown(
        [e for e, _, _ in ENDPOINTS], value = "NOAEL", label = "Endpoint",
        allow_select_none = False,
    )
    mo.vstack([_intro, observation_endpoint])
    return (observation_endpoint,)


@app.cell
def _(mo, observation_endpoint, pl, tables):
    _measurements = tables["measurements"]
    mo.stop(_measurements.is_empty(), mo.md("EPA observations were not prepared for this snapshot."))
    _observations = _measurements.filter(
        (pl.col("endpoint") == observation_endpoint.value) & (pl.col("parse_status") == "complete"),
    )
    _columns = ["preferred_name", "chemical_group", "endpoint", "value_standardized",
                "unit_standardized", "qualifier", "species", "exposure_route", "duration_hours",
                "study_type", "effect", "evidence_basis", "benchmark_response", "parse_note"]
    mo.vstack([
        mo.md(f"**{_observations.height} complete normalized observations** for {observation_endpoint.value}. "
              "These are source records, not counts of independent studies or matched potency comparisons."),
        mo.ui.table(_observations.select(_columns), selection = None, page_size = 10),
        mo.accordion({"Records needing review": mo.ui.table(
            _measurements.filter((pl.col("endpoint") == observation_endpoint.value)
                                 & (pl.col("parse_status") != "complete")).select(_columns),
            selection = None, page_size = 5,
        )}),
    ])
    return


@app.cell
def _(data_root, manifest, mo):
    mo.md(f"""
    ## What to take forward
    The project now supports all seven endpoint types, but evidence is uneven.
    NOAEL/LOAEL expand chronic availability; BMD/BMDL still need more data and
    study context. Molecular distributions differ in this selection, while
    evidence-availability models often remain close to simple baselines.

    A next analysis should match study context for chronic potency and match
    ToxCast panels before interpreting activity differences. Neither missing
    data nor a classifier label establishes safety.

    **Reproducibility:** prepared products in `{data_root.name}/` are verified
    against `manifest.json` before display. The manifest records source and
    code hashes; source caches and generated products remain local. This
    snapshot used {len(manifest['endpoint_policies'])} comparison policies
    (seven types plus the trout-specific LC50 policy). See `analysis/README.md`
    for rebuild and export commands.
    """)
    return


if __name__ == "__main__":
    app.run()
