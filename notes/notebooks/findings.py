"""Professor follow-up: halogen attribution, fingerprint classifiers and comparator review."""
# Serialized marimo cells use display expressions and explicit returns.
# ruff: noqa: B018, PLR1711

import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="full",
    app_title="Research findings · professor follow-up",
)


@app.cell
def _():
    import hashlib
    import json
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import polars as pl
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score

    root = Path(mo.notebook_location()).parents[1]
    diagnostic_dir = root / "analysis/outputs/professor-followup-2026-11-04-final"
    dietary_dir = root / "analysis/outputs/dietary-review-2026-11-04-final"
    return (
        alt,
        balanced_accuracy_score,
        diagnostic_dir,
        dietary_dir,
        hashlib,
        json,
        mo,
        pl,
        roc_auc_score,
        root,
    )


@app.cell
def _(diagnostic_dir, dietary_dir, hashlib, json, mo, pl):
    mo.stop(
        any(not (p / "manifest.json").exists() for p in (diagnostic_dir, dietary_dir)),
        mo.md("""The local bundles are missing. Follow `analysis/docs/diagnostics-review.md`
        and `analysis/docs/compound_sources.md` to obtain or build the inputs.
        This notebook never retrieves identities, fits models or writes research data."""),
    )
    frozen_bundle_integrity = []
    for _directory in (diagnostic_dir, dietary_dir):
        _manifest = json.loads((_directory / "manifest.json").read_text())
        for _path, _expected in _manifest["output_hashes"].items():
            _file = _directory / _path.split("/")[-1]
            _ok = _file.exists() and hashlib.sha256(_file.read_bytes()).hexdigest() == _expected
            if not _ok:
                raise ValueError(f"Frozen output hash mismatch: {_file}")
            frozen_bundle_integrity.append({"bundle": _directory.name, "product": _file.name, "hash": "verified"})
    reports = pl.read_csv(diagnostic_dir / "reports.csv")
    oof = pl.read_csv(diagnostic_dir / "oof.csv")
    cohort = pl.read_csv(diagnostic_dir / "cohort.csv")
    coefficients = pl.read_csv(diagnostic_dir / "coefficients.csv")
    permutations = pl.read_csv(diagnostic_dir / "permutations.csv")
    dietary_review = pl.read_csv(dietary_dir / "review.csv")
    overlaps = pl.read_csv(dietary_dir / "overlaps.csv")
    return (
        frozen_bundle_integrity,
        coefficients,
        cohort,
        dietary_review,
        oof,
        overlaps,
        permutations,
        reports,
    )


@app.cell
def _(balanced_accuracy_score, cohort, mo, oof, reports, roc_auc_score):
    # Recompute metrics and audit fold/scaffold integrity independently of model code.
    _folds_by_id = {}
    _folds_by_scaffold = {}
    for _row in oof.to_dicts():
        if _folds_by_id.setdefault(_row["compound_id"], _row["fold"]) != _row["fold"]:
            raise ValueError("Profiles do not share folds")
        if _folds_by_scaffold.setdefault(_row["scaffold"], _row["fold"]) != _row["fold"]:
            raise ValueError("Scaffold leakage")
    for _report in reports.to_dicts():
        _rows = oof.filter(oof["profile"] == _report["profile"])
        if _rows.height != cohort.height or _rows["compound_id"].n_unique() != cohort.height:
            raise ValueError("Incomplete held-out cohort")
        if set(_rows["compound_id"]) != set(cohort["compound_id"]):
            raise ValueError("Mismatched held-out cohort")
        _y, _p = _rows["label"].to_numpy(), _rows["probability"].to_numpy()
        if abs(roc_auc_score(_y, _p) - _report["roc_auc"]) > 1e-12:
            raise ValueError("AUROC mismatch")
        if abs(balanced_accuracy_score(_y, _p >= .5) - _report["balanced_accuracy"]) > 1e-12:
            raise ValueError("Balanced accuracy mismatch")
    model_metrics_verified = True
    return (model_metrics_verified,)


@app.cell
def _(hashlib, json, mo, pl, root):
    triage_dir = root / "analysis/outputs/dietary-triage-2026-11-04-final"
    mo.stop(
        not (triage_dir / "manifest.json").exists(),
        mo.md("Automated review bundle is missing; see `analysis/docs/dietary-triage.md`."),
    )
    triage_manifest = json.loads((triage_dir / "manifest.json").read_text())
    for _path, _hash in triage_manifest["output_hashes"].items():
        _product = triage_dir / _path.split("/")[-1]
        if hashlib.sha256(_product.read_bytes()).hexdigest() != _hash:
            raise ValueError(f"Triage product hash mismatch: {_product.name}")
    triage_rows = pl.read_csv(triage_dir / "triage.csv")
    triage_leads = pl.read_csv(triage_dir / "curated_leads.csv")
    triage_text_hits = pl.read_csv(triage_dir / "text_flags.csv", infer_schema_length = None)
    if triage_rows.height != triage_manifest["n"]:
        raise ValueError("Triage cohort count mismatch")
    if triage_rows.filter(
        (pl.col("plant_activity") != "unknown") | (pl.col("high_dose_safety") != "unknown")
    ).height:
        raise ValueError("Automated review must not create accepted biological labels")
    for _category, _n in triage_manifest["counts"].items():
        if triage_rows.filter(pl.col("triage") == _category).height != _n:
            raise ValueError("Triage category count mismatch")
    return triage_leads, triage_manifest, triage_rows, triage_text_hits


@app.cell
def _(hashlib, json, mo, pl, root):
    release_dir = root / "analysis/outputs/verification-release-audit-2026-11-05-final"
    mo.stop(
        not (release_dir / "manifest.json").exists(),
        mo.md("Verification-release audit is absent; see `analysis/docs/verification-release.md`."),
    )
    _manifest = json.loads((release_dir / "manifest.json").read_text())
    for _path, _expected in _manifest["output_hashes"].items():
        _product = release_dir / _path.split("/")[-1]
        if hashlib.sha256(_product.read_bytes()).hexdigest() != _expected:
            raise ValueError(f"Verification-release output hash mismatch: {_product.name}")
    release_audit = json.loads((release_dir / "audit.json").read_text())
    release_references = pl.read_csv(release_dir / "reference_checks.csv")
    release_priority = pl.read_csv(release_dir / "review_priority.csv")
    release_readiness = pl.read_csv(release_dir / "model_readiness.csv")
    release_leads = pl.read_csv(release_dir / "new_lead_identities.csv")
    release_case = json.loads((release_dir / "identity_case.json").read_text())
    release_svg = (release_dir / "identity_case.svg").read_text()
    return (
        release_audit,
        release_case,
        release_leads,
        release_priority,
        release_readiness,
        release_references,
        release_svg,
    )


@app.cell
def _(hashlib, json, mo, pl, root):
    food200_dir = root / "analysis/outputs/food-comparator-200-audit-2026-11-05"
    mo.stop(
        not (food200_dir / "manifest.json").exists(),
        mo.md("The 200-compound audit is missing; see `analysis/docs/compound_sources.md`."),
    )
    _manifest = json.loads((food200_dir / "manifest.json").read_text())
    for _path, _expected in _manifest["output_hashes"].items():
        _product = food200_dir / _path.split("/")[-1]
        if hashlib.sha256(_product.read_bytes()).hexdigest() != _expected:
            raise ValueError(f"Food-comparator audit hash mismatch: {_product.name}")
    _source = root / "notes/plant_animal_food_compounds_200.tsv"
    _source_hashes = {v for k, v in _manifest["input_hashes"].items() if k.endswith(_source.name)}
    if hashlib.sha256(_source.read_bytes()).hexdigest() not in _source_hashes:
        raise ValueError("The 200-compound TSV changed; rebuild its audit in a fresh directory")
    food200_audit = json.loads((food200_dir / "audit.json").read_text())
    food200_identities = pl.read_csv(food200_dir / "identity_checks.csv")
    food200_overlaps = pl.read_csv(food200_dir / "overlaps.csv")
    return food200_audit, food200_identities, food200_overlaps


@app.cell
def _(mo):
    mo.md("""
    # Findings · 5 November 2026
    **Formula and fingerprint models distinguish the selected groups well.**
    Predicting actual plant activity still requires verified biological labels.

    All model comparisons below use **171 compounds (55 herbicides, 116 natural
    products)** and the same five test folds, keeping shared core structures together.
    """)
    return


@app.cell
def _(alt, cohort, mo):
    _rows = []
    for _label, _name in [(1, "Selected herbicides"), (0, "Selected natural products")]:
        _subset = cohort.filter(cohort["label"] == _label)
        _present = int(_subset["halogen_present"].sum())
        _rows.append({"group": _name, "present": _present, "total": _subset.height,
                      "fraction": _present / _subset.height,
                      "count_label": f"{_present}/{_subset.height}"})
    _base = alt.Chart(alt.Data(values = _rows)).encode(
        x = alt.X("fraction:Q", title = "Compounds containing F, Cl, Br or I",
                  scale = alt.Scale(domain = [0, 1]), axis = alt.Axis(format = "%")),
        y = alt.Y("group:N", title = None, sort = [r["group"] for r in _rows]),
        tooltip = ["group:N", "present:Q", "total:Q", alt.Tooltip("fraction:Q", format = ".1%")],
    )
    _chart = (_base.mark_bar(color = "#3575a5", size = 24) +
              _base.mark_text(align = "left", dx = 6, fontSize = 13).encode(text = "count_label:N")
              ).properties(width = 600, height = 90)
    mo.vstack([
        mo.md("""## 1. Halogens explain part of the separation
        Halogens are much more common in the selected herbicides.
        Other prominent formula associations involve nitrogen, element count,
        carbon and oxygen; these are associations within this collection.
        """),
        mo.ui.altair_chart(_chart, chart_selection = False, legend_selection = False),
    ])
    return


@app.cell
def _(alt, mo, model_metrics_verified, reports):
    assert model_metrics_verified
    _profiles = {
        "formula_pca": "Formula · original",
        "halogens_only": "Halogen features only",
        "composition_without_halogens": "Formula · recomputed without halogens",
        "morgan_logistic": "Morgan fingerprints · logistic",
        "morgan_forest": "Morgan fingerprints · random forest",
    }
    _rows = [{**r, "model": _profiles[r["profile"]]} for r in reports.to_dicts()
             if r["profile"] in _profiles]

    def _score_chart(metric, title, number_format):
        _base = alt.Chart(alt.Data(values = _rows)).encode(
            y = alt.Y("model:N", title = None, sort = list(_profiles.values())),
            x = alt.X(f"{metric}:Q", title = title, scale = alt.Scale(domain = [0, 1])),
            tooltip = ["model:N", alt.Tooltip("roc_auc:Q", format = ".4f"),
                       alt.Tooltip("balanced_accuracy:Q", format = ".2%")],
        )
        return (_base.mark_bar(color = "#3575a5", size = 22) +
                _base.mark_text(align = "right", dx = -6, color = "white", fontSize = 12).encode(
                    text = alt.Text(f"{metric}:Q", format = number_format))
                ).properties(width = 310, height = 180)

    _chart = alt.hconcat(
        _score_chart("roc_auc", "AUROC · ranking", ".3f"),
        _score_chart("balanced_accuracy", "Balanced accuracy · cutoff 0.5", ".1%"),
    ).resolve_scale(y = "shared")
    mo.vstack([
        mo.md("""## 2. Fingerprints work; removing halogens weakens the formula model
        Recomputing composition without halogens lowers AUROC **0.952 → 0.913**.
        RDKit Morgan logistic/forest models reach **0.947–0.949 AUROC**; neither
        improves balanced accuracy over the original formula model here.
        """),
        mo.ui.altair_chart(_chart, chart_selection = False, legend_selection = False),
        mo.md("""AUROC measures ranking; balanced accuracy averages performance on
        the two groups. These scores predict **selection membership**, not verified
        herbicidal activity, benignity or natural origin. Settings are exploratory;
        no independent biological validation is available.
        """),
    ])
    return


@app.cell
def _(food200_audit, mo, release_audit):
    _food = food200_audit
    _matches = release_audit["retrieved_reference_counts"]
    _leads = release_audit["new_lead_identity_status"]
    mo.md(f"""
    ## 3. Biological verification is the next step

    - **Dietary comparison expanded:** {_food['n']} user-verified benign compounds,
      including all 40 pilot identities (**160 additional**). All 200 SMILES/key
      pairs agree; fingerprints are available for all 200 and formula features for
      {_food['formula_eligible']}. This advances the dietary comparator group;
      **plant inactivity is not established** by dietary benignity.
    - **Assay review:** 154 compounds; {_matches['EXACT_FULL_STEREO_INCHIKEY']} full
      external identity matches and one connectivity-only match. **Li 7b /
      CHEMBL2253255 is on hold:** reported allyl and frozen cyclopropyl structures differ.
    - **New leads:** {_leads['name_lookup_candidate_requires_source_match']} additional
      fingerprinted identity candidates; {_leads['name_not_resolved']} names unresolved.
      **No activity model has been fitted from these additions.**

    **Next:** retain the benignity citations/dose limits, reconcile the 16 original
    selection overlaps, resolve 7b and agree the biological endpoint/group definitions.
    The herbicide–allelopath–benign comparison remains open.

    ---
    **Presentation ends here.** Verification instructions and supporting results follow.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    # Verification: exact next actions
    **Working instructions, separate from the presentation findings above.**

    An editable pack is ready at
    `analysis/outputs/manual-verification-2026-11-05/`.
    The full instructions are in `analysis/docs/verification-checklist.md`.
    Original source files remain unchanged; no human decisions have been filled in.

    **New priority:** resolve Li **7b / CHEMBL2253255** first. The latest release
    reports an allyl-versus-cyclopropyl discrepancy; keep activity unknown until
    original PDF/SI and chemistry review resolve it. Then check 7w and KIH-6127
    geometry. See `analysis/docs/verification-release.md` and the section 6c tables.

    **For the Li/He plant-assay compounds:**

    1. Start with `assays/li2006_source_mapping.csv` (24 rows), then review
       `he2011_source_mapping.csv` (58 rows) separately. Obtain each original PDF/SI.
    2. Compare the paper's structure with the matching computed SVG sheet in
       `assays/structure_drawings/`. Record the paper compound number, structure
       page and exact match/unresolved/conflict decision. Get chemistry help if unsure.
    3. Find that compound's exact result row and species/dose/application column.
       Save a cited excerpt and transcribe the original symbol, grade or inequality.
    4. Record species/stage, rate and units, application mode, duration, controls
       and replication from the methods. Record missing details and conflicts explicitly.
    5. Agree a source-specific decision rule with the research lead. Record human
       reviewer/date, the accepted policy and approval reference. Unresolved evidence
       remains unknown; a low response applies only to the declared assay conditions.
    6. Transfer only accepted decisions into separately versioned seven-column
       label files, one policy per file. Run `analysis/validate_activity_proposal.py`
       with the frozen latest audit (exact command in the release assessment).
       It checks the new hold as well as schema; passing does not verify scientific
       approval. Broaden scaffold support before activity modeling.

    **For the new 200-compound list:** retain the verification already performed
    as linked citations, dose/population/duration limits and reviewer decisions.
    Check CID correspondence and reconcile overlaps before a new model. Section 6.1
    shows the structural audit. The earlier 40-row worksheets below remain useful
    reference material; their frozen statuses do not describe the newer verification.

    **For the historical 40-compound pilot records:**

    1. Use `dietary/triage_reference.csv` to prioritize review; start with the 12
       provisional cases. Edit `dietary/review.csv`, not the frozen original.
    2. Define a specific population, oral amount/units, duration and endpoint.
       Match the exact compound/form and document occurrence in the claimed organism.
    3. Read the primary exposure evidence and each flag in context. Record the
       dose, route/time, restrictions, citation, reviewer and bounded decision.
       Food use and absence of warnings alone do not establish high-dose safety.
    4. Obtain separate suitable plant-assay evidence before calling any dietary
       candidate plant-inactive. The four natural-active occurrence leads likewise
       require their own identity, activity and ecological-role checks.

    ---
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    # Supporting analysis and source evidence
    The sections below document the methods, model comparisons, errors, dietary
    triage and deeper assay-review audit behind the presentation findings.

    Frozen model products passed their saved SHA-256 checks. All eight held-out
    AUROC/balanced-accuracy pairs were recomputed, shared compound/fold assignments
    checked and scaffold leakage rejected. The triage and deeper-review sections
    verify their own saved audit products. This notebook reads evidence; it does
    not retrieve compounds, fit models, assign labels or edit the working copies.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 1. Define exactly what the existing result measures

    The evaluation cohort is **55 selected herbicides and 116 selected natural
    products**, after the established identity/formula eligibility and deduplication
    policy. The prepared selection was larger (176); this diagnostic uses the same
    complete 171-compound cohort as the older ablations. Source membership=1 means
    selected herbicide; source membership=0 means selected natural product.

    Five fixed **scaffold-held-out** folds keep compounds with the same RDKit
    scaffold together. The same compounds/folds are used for every profile.
    Training-only preprocessing avoids exposing the held-out compounds to fitting.
    No seed/threshold/hyperparameter search was performed; the cutoff remains 0.5.
    All acyclic chemistry shares the ACYCLIC group under the existing policy.

    AUROC measures ranking; balanced accuracy averages sensitivity and specificity
    at the chosen cutoff. They answer different questions. High selection accuracy
    can reflect how the lists were assembled, rather than herbicidal efficacy.
    """)
    return


@app.cell
def _(cohort, mo):
    halogen_counts = cohort.group_by("label", "halogen_present").len().sort("label", "halogen_present")
    mo.vstack([
        mo.md("""## 2. Test the halogen hypothesis
        **37/55 selected herbicides have halogens, versus 1/116 natural products.**
        Presence alone reaches 83.21% balanced accuracy, so it is a strong clue.
        It does not recover all the original performance.

        Two ablations distinguish direct columns from indirect composition clues:
        (a) drop F/Cl/Br/I counts and fractions;
        (b) additionally recalculate element count, atom count and all remaining
        fractions without halogens. The stricter ablation still reaches
        **0.9130 AUROC / 82.15% balanced accuracy**. This supports additional signal.
        It does not establish causal elemental effects, or chemically simulate
        replacing halogens in real molecules.
        """),
        mo.ui.table(halogen_counts, selection = None),
    ])
    return


@app.cell
def _(alt, mo, reports):
    comparison_chart = alt.Chart(alt.Data(values = reports.unpivot(
        on = ["roc_auc", "balanced_accuracy"], index = "profile", variable_name = "metric",
        value_name = "score").to_dicts())).mark_bar().encode(
            y = alt.Y("profile:N", title = None),
            x = alt.X("score:Q", scale = alt.Scale(domain = [0, 1]), title = "Held-out score"),
            color = "metric:N", row = "metric:N", tooltip = ["profile:N", "score:Q"],
        ).properties(width = 720, height = 230)
    mo.vstack([
        mo.md("""## 3. Compare formula and fingerprint classifiers
        Morgan fingerprints describe local atom environments up to radius 2 in
        **2048 binary bits**, with chirality included. They use the existing RDKit
        generator; the first linked paper proposes **MAP4**, a different fingerprint.
        MAP4 was not added or benchmarked here.

        Raw Morgan logistic uses class-balanced L2 logistic regression, C=1, without
        scaling or PCA. The forest uses 500 trees, minimum leaf size 2, square-root
        feature sampling and class-balanced weights. These are fixed exploratory
        baselines. Both reach **88.66% balanced accuracy**; their AUROCs are
        **0.9467** and **0.9487**. Neither improves on the original formula result at
        cutoff 0.5. This does not show fingerprints are generally inferior: cohort,
        settings, sample size and operating point all matter.
        """),
        comparison_chart,
        mo.ui.table(reports, selection = None),
    ])
    return


@app.cell
def _(coefficients, permutations, pl):
    coefficient_summary = coefficients.group_by("feature").agg(
        pl.col("coefficient").mean().alias("mean_coefficient"),
        pl.col("coefficient").min().alias("min_coefficient"),
        pl.col("coefficient").max().alias("max_coefficient"),
        pl.col("coefficient").abs().mean().alias("mean_absolute_coefficient"),
    ).sort("mean_absolute_coefficient", descending = True)
    permutation_summary = permutations.group_by("feature").agg(
        pl.col("auc_drop").mean().alias("mean_auc_drop"),
        pl.col("auc_drop").std().alias("descriptive_sd"),
    ).sort("mean_auc_drop", descending = True)
    return coefficient_summary, permutation_summary


@app.cell
def _(alt, coefficient_summary, mo, permutation_summary):
    mo.vstack([
        mo.md("""## 4. Identify which formula features contribute
        The raw standardized formula comparator has nearly the same AUROC as the
        original PCA model. Its strongest mean absolute coefficients are **N count,
        Cl count, element count, C count and O count**. Positive means association
        with selected herbicides; negative means association with natural products.
        Coefficients are per training-fold standard deviation, under L2 regularization.

        Held-out permutation checks shuffle each feature ten times per test fold.
        A joint halogen shuffle keeps relationships inside that block together.
        Mean AUC drops are approximately **0.0543 (joint halogens), 0.0493 (N count),
        0.0304 (Cl count)**. Negative drops can occur through noise.

        **These explain the raw formula comparator, not the original PCA model.**
        Counts/fractions are correlated: coefficients can be redistributed and
        individual permutation effects masked. Shuffling can create impossible
        formulas. Fold ranges and permutation SD are descriptive, not confidence
        intervals, p-values or causal attribution. Do not sum the drops as variance
        explained or interpret larger coefficients as biological mechanisms.
        """),
        alt.Chart(alt.Data(values = coefficient_summary.head(12).to_dicts())).mark_bar().encode(
            y = alt.Y("feature:N", sort = "-x", title = None),
            x = alt.X("mean_coefficient:Q", title = "Mean standardized coefficient (5 folds)"),
            tooltip = ["feature:N", "mean_coefficient:Q", "min_coefficient:Q", "max_coefficient:Q"],
        ).properties(width = 720, height = 280),
        mo.ui.table(coefficient_summary, selection = None),
        mo.ui.table(permutation_summary, selection = None),
    ])
    return


@app.cell
def _(mo, reports):
    profile_selector = mo.ui.dropdown(
        options = reports["profile"].to_list(), value = "morgan_forest", label = "Inspect held-out model",
    )
    profile_selector
    return (profile_selector,)


@app.cell
def _(cohort, mo, oof, pl, profile_selector):
    inspected_predictions = oof.filter(pl.col("profile") == profile_selector.value).join(
        cohort.select("compound_id", "query", "halogen_present"), on = "compound_id",
    ).with_columns((pl.col("probability") >= .5).cast(pl.Int64).alias("prediction"))
    mistakes = inspected_predictions.filter(pl.col("prediction") != pl.col("label"))
    mo.vstack([
        mo.md(f"""## 5. Inspect the held-out errors
        **{profile_selector.value}: {mistakes.height} incorrect classifications at 0.5.**
        Fingerprint logistic and forest each have 43 TP, 12 FN, 115 TN and 1 FP.
        Scores are selection probabilities under this experiment; they are not
        calibrated probabilities of toxicity. The errors below are useful review
        leads, not automatically wrong biological labels.
        """),
        mo.ui.table(mistakes, selection = None),
    ])
    return


@app.cell
def _(dietary_review, mo, overlaps):
    mo.vstack([
        mo.md("""## 6. Original 40-compound dietary pilot (historical)
        These are the frozen pilot results, before the subsequent 200-compound
        user verification summarized in section 6.1. The candidate list contains **40 names**: 20 amino acids, six sugars, five
        polyols, seven fatty acids and two organic acids. PubChem supplied the CID,
        isomeric SMILES and InChIKey; RDKit independently regenerated every InChIKey.
        All 40 agree, parse successfully and have fingerprints/descriptors.
        This verifies identity consistency, not correct stereoisomer choice or safety.

        **37 are pending human review; 3 are on hold; 0 have accepted high-dose or
        plant-negative labels.** Caprylic/capric acids occur in registered herbicide
        products even though they have edible-source food-use provisions. Lauric
        acid is held conservatively for biological-activity review. Xylitol has a
        dog-toxicity warning. Fructose/maltose source provisions concern mixtures;
        an isolated compound's exposure must be checked separately.

        The source overlap audit finds **L-proline already in the natural-product
        selection**. It cannot be assigned opposite roles or split across folds.
        **29/40 candidates share ACYCLIC**, so this pilot has substantial chemical
        family bias. More names alone will not create independent chemistry.
        Dose, population, route/duration and natural-occurrence references remain
        blank for human review. No candidate was inserted into model training.
        """),
        mo.ui.table(dietary_review.select(
            "name", "pubchem_cid", "family", "review_status", "review_caveat",
            "food_source_url", "caution_source_url", "existing_matches",
        ), selection = None),
        mo.ui.table(overlaps, selection = None),
    ])
    return


@app.cell
def _(alt, food200_audit, food200_identities, food200_overlaps, mo):
    _food = food200_audit
    _overlap = _food["overlaps"]
    _rows = [
        {"structure_group": "Acyclic", "compounds": _food["acyclic"]},
        {"structure_group": "Contains rings", "compounds": _food["n"] - _food["acyclic"]},
    ]
    _base = alt.Chart(alt.Data(values = _rows)).encode(
        x = alt.X("compounds:Q", title = "Compounds", scale = alt.Scale(domain = [0, 200])),
        y = alt.Y("structure_group:N", title = None), tooltip = ["structure_group:N", "compounds:Q"],
    )
    _chart = (_base.mark_bar(color = "#238672", size = 24) +
              _base.mark_text(align = "left", dx = 6).encode(text = "compounds:Q")
              ).properties(width = 540, height = 90)
    mo.vstack([
        mo.md(f"""## 6.1. Expanded dietary comparison · 5 November 2026

        The new `notes/plant_animal_food_compounds_200.tsv` contains **{_food['n']}
        unique names, CIDs and supplied keys**. The user reports these compounds
        were verified benign. This audit checks the supplied chemical records;
        the four-column TSV does not include the supporting exposure/reviewer records.

        **Identity and features:** all {_food['parseable_structures']} SMILES parse;
        all computed InChIKeys match; all have Morgan fingerprints. The current
        formula workflow supports {_food['formula_eligible']}; eight charged records
        are unsupported. CID-to-structure correspondence has not been independently
        re-fetched. Name/key consistency and benignity evidence are separate checks.

        **What is new:** all 40 earlier pilot identities are present, so there are
        **160 additional full-key identities**, not 200 additional controls. The
        older pilot's automated-review statuses above/below describe its frozen
        evidence, not a reassessment of the user's subsequent verification.

        **Chemical diversity:** {_food['scaffold_groups']} scaffold groups;
        {_food['acyclic']}/{_food['n']} compounds share ACYCLIC. Counts of compounds
        do not equal counts of independent chemical families.
        """),
        mo.ui.altair_chart(_chart, chart_selection = False, legend_selection = False),
        mo.md(f"""**Overlap:** {_overlap['original_selection']['full_key_candidates']}
        exact original-selection matches; {_overlap['original_selection']['connectivity_candidates_including_full']}
        when including connectivity-only matches. Keep shared identities/families
        together across splits. No full or connectivity matches occur with the
        154 assay candidates.

        **What this enables:** a larger herbicide-versus-dietary-comparator
        experiment, with the benignity claim's population, dose and duration
        documented. It does not establish plant-inactive controls or a numerical
        herbicide–allelopath–benign ordering. Preserve the original four columns;
        retain verification sources, dose limits, reviewer/date and decision in a
        linked record. Reconcile overlaps and check CIDs before model evaluation.
        No biological targets were assigned and no new classifier was fitted by
        this structural audit. All saved target columns remain null.
        """),
        mo.accordion({
            "Inspect all 200 identity checks": mo.ui.table(food200_identities, selection = None, page_size = 8),
            "Inspect overlaps with previous datasets": mo.ui.table(food200_overlaps, selection = None, page_size = 8),
        }),
    ])
    return


@app.cell
def _(mo, triage_manifest, triage_rows):
    _shortlist = triage_rows.filter(
        triage_rows["triage"] == "provisional_dietary_shortlist",
    )["name"].to_list()
    mo.vstack([
        mo.md(f"""## 6a. Automated review of the original 40-compound pilot (historical)

        **12 provisional dietary candidates · 26 priority review · 2 exclusions
        from a presumed plant-inactive group.** This is a review queue, not a new
        biological label file. All high-dose and plant-activity labels remain unknown.

        **Provisional list:** {', '.join(_shortlist)}.

        The process saved 95 requests: 40 PubChem hazard sections, 40 toxicity
        sections and 15 food-use documents. Ninety-four returned HTTP 200;
        xylitol's hazard section returned 404. Food checks used **2025 annual CFR
        XML** or FDA GRAS pages. Thirty-eight names have conditional food-use leads;
        fructose/HFCS and maltose/malt syrup remain mixture-scoped. Verify current
        conditions, exact compound form and exposure before accepting a comparator.

        The rules separate GHS handling warnings from systemic codes, known
        population/dose cautions, prior holds, identity overlaps and family-specific
        exposure questions. They also scan selected human-toxicity/interaction
        passages. This promotes **tryptophan, methionine, lysine and glutamine** out
        of the simpler 16-candidate pilot shortlist. Eleven candidates have text
        review hits in the final run.

        **A text hit is not a harmful-effect finding.** Matches can describe null
        results, contamination, co-exposures, historical evidence or other species.
        GHS reports can vary across suppliers and conditions. Absence of a trigger
        does not clear the compound; the provisional group merely has fewer
        flags under this bounded policy. This is not an exhaustive literature
        review or a validated automated safety classifier.

        **Missingness stays visible:** five rows have gaps, even though the standalone
        evidence-gap category has zero entries (priority flags take precedence).
        These include unavailable/missing xylitol, lactose and L-malic-acid sections
        or extracted text, plus the two mixture-scoped food references.
        """),
        mo.ui.table([
            {"category": k, "count": v} for k, v in triage_manifest["counts"].items()
        ], selection = None),
    ])
    return


@app.cell
def _(mo, triage_rows):
    triage_filter = mo.ui.dropdown(
        options = ["All", *sorted(triage_rows["triage"].unique().to_list())],
        value = "All", label = "Candidate review group",
    )
    triage_candidate = mo.ui.dropdown(
        options = sorted(triage_rows["name"].to_list()), value = "L-Tryptophan",
        label = "Inspect evidence for one candidate",
    )
    mo.hstack([triage_filter, triage_candidate])
    return triage_candidate, triage_filter


@app.cell
def _(mo, pl, triage_filter, triage_rows):
    _queue = triage_rows if triage_filter.value == "All" else triage_rows.filter(
        pl.col("triage") == triage_filter.value,
    )
    mo.vstack([
        mo.md("""### Preliminary review queue
        `priority_review` includes logistics/identity and exposure questions as
        well as hazard leads. It does not mean every flagged compound is dangerous.
        Review the reason, gaps and original source context before making a decision.
        """),
        mo.ui.table(_queue.select(
            "name", "triage", "flags", "preliminary_reason", "evidence_gaps",
            "ghs_systemic_codes", "ghs_handling_codes", "ghs_aquatic_codes",
            "food_support", "next_review_action",
        ), selection = None),
    ])
    return


@app.cell
def _(mo, pl, triage_candidate, triage_leads, triage_rows, triage_text_hits):
    _chosen = triage_rows.filter(pl.col("name") == triage_candidate.value)
    _leads = triage_leads.filter(pl.col("name") == triage_candidate.value)
    _hits = triage_text_hits.filter(pl.col("name") == triage_candidate.value)
    mo.vstack([
        mo.md(f"""### Evidence drill-down: {triage_candidate.value}
        The first table is the automated summary. Agency-source leads below are
        separately curated rules with checked dates; text matches are automatically
        found passages with no inferred polarity. Inspect the linked primary source.

        Quantities have **different meanings**: sorbitol/mannitol values are labeling
        triggers, erythritol's is an ADI, and arginine's is a supplement warning
        context. None is a proposed dose or a plant-inactivity threshold.
        """),
        mo.ui.table(_chosen, selection = None),
        mo.ui.table(_leads, selection = None),
        mo.ui.table(_hits.select(
            "signal", "interpretation", "section", "text", "source_name", "source_url",
            "snapshot_url", "retrieved_at",
        ), selection = None),
        mo.md("""Full records and all extracted source text are retained under
        `analysis/outputs/dietary-triage-sources-2026-11-04/` and
        `analysis/outputs/dietary-triage-2026-11-04-final/`.
        Reproduce with the commands in `analysis/docs/dietary-triage.md`.
        Review a new versioned decision copy; do not alter the frozen outputs or
        automatically feed this queue into model training.
        """),
    ])
    return


@app.cell
def _(hashlib, json, mo, pl, root):
    deeper_audit_dir = root / "analysis/outputs/deeper-review-connection-2026-11-05"
    mo.stop(
        not (deeper_audit_dir / "manifest.json").exists(),
        mo.md("Deeper source-review integration audit is absent; see `analysis/docs/deeper-assay-review.md`."),
    )
    _manifest = json.loads((deeper_audit_dir / "manifest.json").read_text())
    for _path, _expected in _manifest["output_hashes"].items():
        _product = deeper_audit_dir / _path.split("/")[-1]
        if hashlib.sha256(_product.read_bytes()).hexdigest() != _expected:
            raise ValueError(f"Deeper audit hash mismatch: {_product.name}")
    deeper_audit = json.loads((deeper_audit_dir / "audit.json").read_text())
    deeper_files = pl.read_csv(deeper_audit_dir / "file_inventory.csv")
    deeper_support = pl.read_csv(deeper_audit_dir / "hypothetical_support_NOT_APPROVED.csv")
    deeper_overlaps = pl.read_csv(deeper_audit_dir / "identity_overlaps.csv")
    deeper_studies = pl.read_csv(deeper_audit_dir / "study_inventory.csv")
    return (
        deeper_audit,
        deeper_files,
        deeper_overlaps,
        deeper_studies,
        deeper_support,
    )


@app.cell
def _(
    deeper_audit,
    deeper_files,
    deeper_overlaps,
    deeper_studies,
    deeper_support,
    mo,
):
    mo.vstack([
        mo.md(f"""## 6b. Connecting the deeper compound review · 5 November 2026

        `notes/compound_review_deeper_2026-10-29/` is useful source-review work on
        the **same 154 ChEMBL compounds, 157 observations and 14 publications**
        already in the frozen assay bundle. It does not add another independent
        dataset or replace the dietary comparator review.

        The audit checked all **{deeper_audit['source_files']} files**, verified all
        15 listed release hashes and all 154 packet structures/observation IDs,
        and confirmed that the original 16 source columns were preserved across
        all 157 log rows. Both the index and compound packets are byte-identical
        to the earlier handoff. All working activity/origin labels remain unknown.

        **Historical package:** the newer section 6c supersedes one of these
        conditional actives with an unresolved identity hold; these counts preserve
        what the older package said.

        **What is useful:** 47 conditional active and 31 conditional low-response
        scenarios, 8 gray-zone rows and 68 not assessed. The low-response cases
        (10 Li 2006, 21 He 2011) are leads for an actual plant-activity dataset,
        whereas the new dietary list addresses a different exposure question.
        Four separate ophiobolin occurrence proposals are natural-active review
        leads; they do not establish safe compounds or an ordinal middle group.

        **What blocks training:** exact source structure/table matching and
        policy/quality approval are still missing. Li and He have different doses,
        thresholds and assay contexts. Under the current scaffold policy, Li's
        proposed negatives span only two scaffolds; He's 50 proposed known
        outcomes span only two total scaffolds. Both fail three-/five-fold support.
        No classifier was fitted during this audit.

        **Important importer limit:** the provisional seven-column CSVs parse
        successfully. `NOT_FOR_TRAINING` filenames and proposed policy names are
        not a scientific-approval gate in the importer. Do not give those CSVs to
        `screen.py --labels` as accepted labels or pool the separate policies.

        There are **five exact original-selection overlaps** and **no exact or
        additional connectivity-key overlaps with the 40 dietary candidates**.
        The measured plant and dietary evidence complement each other; neither
        supplies the other task's missing negative labels.

        **Next:** obtain original Li/He PDF/SI, map the 82 in-study compounds to
        exact frozen structures and table columns, agree source-specific quality/
        label rules, then add independent negative-bearing chemical families.
        The source package also flags ordinal/binned responses, g/kg unit issues,
        detached-leaf mm endpoints, missing outcomes and repeated-study conflicts.
        Some copied links/access summaries are stale; use the maintained label
        guide and observation-level log. Preserve the original directory unchanged.

        Full file-by-file assessment, source checks and reproduction commands:
        `analysis/docs/deeper-assay-review.md`. The tables below are an integrity
        and hypothetical support audit, not newly approved biological evidence.
        """),
        mo.ui.table(deeper_support, selection = None),
        mo.ui.table(deeper_overlaps, selection = None),
        mo.ui.table(deeper_files, selection = None),
        mo.ui.table(deeper_studies, selection = None),
    ])
    return


@app.cell
def _(
    mo,
    release_audit,
    release_case,
    release_leads,
    release_priority,
    release_readiness,
    release_references,
    release_svg,
):
    mo.vstack([
        mo.md(f"""## 6c. New verification release · 5 November 2026

        **Highest priority: Li 7b / CHEMBL2253255 has an unresolved source-identity
        conflict.** The release reports N-allyl in the source; the frozen SMILES
        encode N-cyclopropyl. Keep activity unknown. Obtain original PDF/SI, expand
        the R-group table, check the exact result row and seek a chemistry review.
        This audit did not independently visually adjudicate the original figure.

        The illustrated alternative below was constructed only to explain the
        problem. Both structures have formula **{release_case['formula']}**, but
        different full InChIKeys and **{release_case['different_morgan_bits']} different
        Morgan bits** (Tanimoto {release_case['morgan_tanimoto']:.3f}). This shows a
        limitation of formula representation; it does not validate the alternative
        structure or prove fingerprints predict activity.
        """),
        mo.Html(release_svg),
        mo.md(f"""**Integrity and progress:** all 16 release files were inventoried,
        all 15 listed hashes agreed and all {release_audit['n']} unique RDKit keys
        reproduced. Original source fields for all {release_audit['observations']}
        observations were unchanged. Independent public-reference retrievals confirm
        15 full-key matches and one connectivity-only comparison. Full keys establish
        database representation agreement, not paper-isolate or activity mapping.
        Manufacturing provenance is not proof that natural occurrence is impossible.

        Li's 24-row crosswalk has 21 substituent-consistency leads, the 7b hold,
        unresolved 7w and comparator geometry. Matching all 24 response bands alone
        cannot resolve these structure questions. The release does not include the
        original source PDFs/SI; three claimed context files remain only in the
        earlier package. All working activity/origin labels remain unknown.

        The old conditional file still has 47 active scenarios. This audit's
        `effective_conditional_screen.csv` takes precedence: **46 active, 31 low
        response, 8 gray, 68 unassessed and one identity hold**, all unapproved.
        `identity_holds.csv` and the hold-aware proposal checker guard against
        inadvertently importing the historical active assignment. The generic
        importer and old worksheet validator do not automatically enforce this hold.

        **Training decision:** no classifier fitted. The readiness table below
        checks hypothetical support only. Excluding the held structure or restricting
        to the 21 consistency leads still leaves just two negative-bearing scaffolds.
        The 15 provenance proposals also lack the required class/scaffold support.
        """),
        mo.ui.table(release_readiness, selection = None),
        mo.md("""### External identities and source-review priorities
        Read the comparison/status columns before interpreting a match. Resolve
        7b first, then the remaining Li uncertainties and He source mappings.
        """),
        mo.ui.table(release_references, selection = None),
        mo.ui.table(release_priority, selection = None),
        mo.md("""### Additional natural-product leads
        Five of the 11 names resolved to single PubChem identity candidates with
        internally consistent SMILES/keys; their fingerprints are in the separate
        `new_lead_features.parquet`. Six 404 name searches remain unresolved, not
        discarded. Every target remains null. Match original paper/SI structures
        before accepting identities; assess occurrence and plant response separately.

        The [2021 primary leaf study](https://www.jstage.jst.go.jp/article/mycosci/62/1/62_MYC515/_html/-char/en)
        reports lesion diameters on punctured/intact detached green-foxtail leaves.
        Ophiobolin I has weak punctured-leaf response at the highest concentration
        and no intact-leaf lesions in Table 1; two other congeners have no lesions
        under the tested conditions. Record dose, leaf treatment and duration before
        considering bounded low-response labels. Keep mixture synergy and anticancer
        endpoints separate from individual herbicidal activity.

        Full file-by-file assessment, sources, reproduction command and hold-aware
        label-check command: `analysis/docs/verification-release.md`. These findings
        supplement the dietary review; they establish neither benign high-dose
        controls nor the proposed herbicide–allelopath–benign ordering.
        """),
        mo.ui.table(release_leads, selection = None),
    ])
    return


@app.cell
def _(
    alt,
    cohort,
    diagnostic_dir,
    dietary_dir,
    dietary_review,
    hashlib,
    json,
    mo,
    pl,
    root,
):
    _manifest = json.loads((diagnostic_dir / "manifest.json").read_text())
    _source = root / "analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet"
    _expected = next(iter(_manifest["input_hashes"].values()))
    if hashlib.sha256(_source.read_bytes()).hexdigest() != _expected:
        raise ValueError("Structural input hash mismatch")
    _original = pl.read_parquet(
        root / "analysis/outputs/structure-2026-10-28-stress-baseline/structural_features.parquet",
    ).join(cohort.select("compound_id"), on = "compound_id").with_columns(
        pl.when(pl.col("selection_target") == 1).then(pl.lit("Selected herbicides"))
        .otherwise(pl.lit("Allelopathy-source natural selection")).alias("source_group"),
    )
    _dietary = pl.read_parquet(dietary_dir / "features.parquet").join(
        dietary_review.select("compound_id", "review_status", "existing_matches"), on = "compound_id",
    ).filter(pl.col("existing_matches").is_null() | (pl.col("existing_matches") == "")).with_columns(
        pl.when(pl.col("review_status") == "hold").then(pl.lit("Dietary candidates · HOLD"))
        .otherwise(pl.lit("Dietary candidates · unreviewed")).alias("source_group"),
    )
    _columns = ["compound_id", "query", "mw", "logp", "source_group"]
    chemical_space = pl.concat([_original.select(_columns), _dietary.select(_columns)])
    mo.vstack([
        mo.md("""## 7. What would “allelopaths in the middle” mean?
        The professor's proposal is a testable hypothesis, not an ordering built
        into these labels. An allelopath may be a potent herbicide; a human food
        compound may injure plants. The natural selection also contains response
        markers, so it is not a fully reviewed set of allelopaths.

        This descriptive molecular-weight/logP view displays the source selections
        and new review candidates. The shared proline identity is omitted from the
        dietary points. This historical projection uses the original 40-compound
        pilot, not the expanded 200-compound list in section 6.1.
        **It is not an activity axis or a statistical test of a
        midpoint.** Pan/zoom and hover to inspect family/size differences that a
        future model could exploit. A validated middle-group claim requires
        independent reviewed labels and a declared score/endpoint/contrast.
        """),
        alt.Chart(alt.Data(values = chemical_space.to_dicts())).mark_circle(size = 65, opacity = .75).encode(
            x = alt.X("mw:Q", title = "Molecular weight (g/mol)"),
            y = alt.Y("logp:Q", title = "RDKit calculated logP"),
            color = alt.Color("source_group:N", title = "Source/review role"),
            tooltip = ["query:N", "compound_id:N", "mw:Q", "logp:Q", "source_group:N"],
        ).properties(width = 820, height = 410).interactive(),
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 8. What you must do before calling this an activity/safety model

    1. **Agree the target with your professor.** A source-group classifier, a
       human dietary-safety classifier and a plant-inhibition classifier are three
       different questions. For plant activity, predeclare species, endpoint,
       concentration, duration, controls and active/inactive thresholds. Record
       natural occurrence and non-target hazard separately.
    2. **Retain the verification behind the 200 dietary compounds.** Link the
       supplied TSV to primary references, dose/unit, population, route/duration,
       reviewer/date and exceptions. Confirm CID correspondence and reconcile the
       16 exact original-selection overlaps plus the additional connectivity match.
       The older 40-row worksheet retains useful flags; its frozen statuses are
       historical. Keep dietary benignity separate from tested plant inactivity.
       Preserve original inputs and save decisions in a versioned linked record.
    3. **Review actual plant assays.** Existing frozen ChEMBL material has 157
       measurements from 14 assays/publications but no accepted activity labels.
       Start with `analysis/docs/label_review_guide.md`; review the original paper
       and assay methods. Low response in one assay is not universal inactivity.
       Keep unknown/conflicting outcomes explicit.
    4. **Then compare the three groups.** Obtain diverse reviewed herbicides,
       allelopaths and suitable comparators, reserve independent chemistry and
       publications, deduplicate overlaps, and evaluate formula and fingerprint
       logistic/forest models using matching holdouts. A three-class classifier
       has no inherent ordinal “middle”; alternatively train a declared binary
       contrast and assess an independent allelopath score distribution.
    5. **Validate before screening.** Report AUROC, balanced accuracy, confusion,
       precision–recall, calibration and similarity/domain limits. Keep an
       independent test set out of profile/threshold choices. Confirm efficacy
       and non-target hazard separately before proposing safer bioherbicides.

    **What you can tell your professor now:** “The halogen hypothesis is supported
    (37/55 versus 1/116), but non-halogen composition also separates the selection.
    I reproduced the formula result and tested raw Morgan logistic and forest
    models on the same scaffold folds. The dietary comparison now has 200 compounds
    reported verified benign; all supplied SMILES/key pairs agree, with 160 identities
    beyond the pilot. Dietary benignity does not establish plant inactivity. Actual activity prediction
    and the three-group ordering still depend on reviewed biological labels.”
    """)
    return


@app.cell
def _(frozen_bundle_integrity, mo):
    mo.vstack([
        mo.md("""## Reproduce and inspect the evidence

        From the repository root:

        ```bash
        UV_CACHE_DIR=analysis/.uv-cache uv run --project analysis marimo run notes/notebooks/findings.py
        ```

        Use `edit` instead of `run` to change the notebook. A static export is at
        `notes/notebooks/findings.html`; selectors need the live notebook.
        Implementation/reproduction commands and input/output contracts are in
        `analysis/docs/diagnostics-review.md` (professor follow-up) and
        `analysis/docs/compound_sources.md` (dietary pilot). Dated scientific results
        are in `analysis/FINDINGS.md`. Research outputs/raw snapshots remain local
        and ignored; the requested notebook is selectively committed under notes.
        Output hashes verify integrity, not scientific validity. Historical
        manifests are preserved and current code may evolve separately.

        **Professor's reading list and primary source checks (4 November 2026):**

        - [MAP4 paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7291580/): proposes a
          different fingerprint combining circular environments with atom-pair
          distances. It is an alternative to benchmark later, not a prerequisite
          for the RDKit Morgan baseline.
        - [Fingerprint review / PubMed](https://pubmed.ncbi.nlm.nih.gov/36113834/)
          ([publisher](https://www.sciencedirect.com/science/article/pii/S135964462200349X)):
          overview of fingerprint concepts/applications. Publisher access was
          restricted; no claim of a full-text implementation from that paper.
        - [RDKit fingerprint generator tutorial](https://greglandrum.github.io/rdkit-blog/posts/2023-01-18-fingerprint-generator-tutorial.html):
          generator configuration and bit-environment explanations.
        - [Amino-acid food-use conditions](https://www.ecfr.gov/current/title-21/section-172.320),
          [edible-source fatty-acid conditions](https://www.ecfr.gov/current/title-21/section-172.860),
          [EPA herbicide-active table](https://downloads.regulations.gov/EPA-HQ-OPP-2021-0336-0002/content.pdf),
          [FDA xylitol warning](https://www.fda.gov/animal-veterinary/animal-health-literacy/paws-xylitol-toxic-dogs).
          Food-use provisions do not establish plant inactivity.
        """),
        mo.ui.table(frozen_bundle_integrity, selection = None),
    ])
    return


if __name__ == "__main__":
    app.run()
