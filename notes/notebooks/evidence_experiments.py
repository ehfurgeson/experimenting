"""Local working notebook: toxicity models, literature activity and binding evidence."""

import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    app_title="Toxicity and plant-response experiments",
)


@app.cell(hide_code=True)
def _():
    import csv
    import hashlib
    import json
    from collections import Counter, defaultdict
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    from sklearn.metrics import f1_score

    return (
        Counter,
        Path,
        alt,
        csv,
        defaultdict,
        f1_score,
        hashlib,
        json,
        mo,
        np,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Toxicity & Plant-response Models

    **Track 1**, which compounds have lower or higher non-target toxicity?

    **Track 2**, what chemistry accompanies a measured plant response?

    Experiments are separeted into

        A. Experimental data

        B. Outside model estimated data

    I use **F1 first**. For three LD50 bins I use macro-F1, the unweighted mean
    of the three class F1 scores. For plant activity, positive means high response.
    F1 = 2TP/(2TP + FP + FN); it does not reward true negatives, so I keep the
    majority baseline and balanced accuracy nearby.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook contains **two distinct modeling experiments**, plus diagnostic checks.

    **1. Toxicity models: predicting an LD50 category**

    These models take seven structure-derived features—molecular weight, polarity, hydrogen-bonding sites, flexibility, rings, and fraction sp³—and predict **low, medium, or high LD50**.

    The same model types are fitted separately to two datasets:

    | Dataset | Total compounds | What the target represents | Training compounds per fold |
    |---|---:|---|---:|
    | **A** | **4,234** | Experimental rat oral LD50 | **3,104–3,510** |
    | **B** | **43,128** | Stored CATMoS LD50 estimates | **32,683–35,042** |

    Each evaluation uses **five folds**: train on four portions, test on the remaining portion, then repeat. Related structures stay together. Every compound receives a prediction from a model that did not train on its group.

    | Model | What it does, simply | A macro-F1 | B macro-F1 |
    |---|---|---:|---:|
    | **Majority baseline** | Always predicts the most common training-set category. Ignores molecular features. | **0.226** | **0.200** |
    | **Logistic regression** | Gives each feature a weight for each LD50 category, adds the contributions, and predicts the category with the highest probability. | **0.382** | **0.465** |
    | **Random forest** | Combines **200 decision trees**, which learn branching rules and interactions between features. Averages their category probabilities. | **0.430** | **0.616** |

    **A asks whether structure predicts measured toxicity. B asks whether seven simple descriptors can reproduce CATMoS.** Neither predicts natural origin or herbicidal activity.

    Macro-F1 gives each LD50 category equal importance. **0.430 does not mean 43% accuracy.**

    **2. Forest OOB diagnostics: understanding feature reliance**

    These are additional forests trained on **all 4,234 A compounds** or **all 43,128 B compounds**.

    Each tree trains on a bootstrap sample. Compounds omitted from that tree’s sample are its **out-of-bag (OOB)** cases.

    The notebook then:

    - Predicts each compound using trees that omitted it.
    - Shuffles one feature within those omitted cases.
    - Measures how much macro-F1 falls, repeating this ten times.

    A larger drop means the forest relies more on that feature. This is **feature importance, not a feature weight or significance test**.

    The OOB macro-F1 scores are **0.484 for A** and **0.729 for B**. Keep the scaffold-held-out scores above as the main performance results: the two evaluation methods test different things.

    **3. Literature activity models: predicting plant response**

    These models use a separate **73-compound exploratory dataset**:

    - **41 high-response compounds**
    - **32 low-response compounds**

    The labels come from different literature assay rules. These are **not 73 confirmed natural herbicides**, and low response under one assay does not establish universal inactivity.

    Again, five scaffold folds were used. Because chemical families have unequal sizes, each fitted model trained on **43–71 compounds**, with **2–30 held out**.

    | Model | What it sees and does | Held-out F1 |
    |---|---|---:|
    | **Majority baseline** | Predicts the most common training-set response—high response in these folds. | **0.719** |
    | **Formula logistic** | Uses elemental counts and proportions, such as oxygen count and chlorine fraction. Learns weighted associations with high response. | **0.513** |
    | **Fingerprint logistic** | Uses **2,048 encoded local structural patterns**, rather than just elemental composition. Learns a weight for each pattern. | **0.727** |
    | **Fingerprint forest** | Uses those structural patterns in **500 decision trees**, allowing combinations and branching rules. | **0.680** |

    Here, F1 concerns the **high-response class**, unlike the three-class macro-F1 used for toxicity.

    The formula model knows **what atoms are present**, but not how they connect. Fingerprints capture **local connectivity**, helping distinguish compounds with similar formulas but different structures.

    **4. New-paper transfer: testing whether the activity models travel**

    For the radish publication test, each activity model trained on **all 73 compounds** and predicted **20 compounds from the new paper**:

    - **2 high-response**
    - **18 low-response**

    All three models scored **F1 = 0** and missed both high-response compounds. This is the strongest warning that the pooled activity patterns do not yet generalize reliably.

    **5. The smaller supporting pieces**

    The notebook also mentions continuous LD50 models: a **median baseline**, **ridge regression**—a weighted linear prediction of log-LD50—and a **random forest regressor**. They use the same A/B cohorts and folds. Their errors are measured with MAE, because F1 applies to categories rather than continuous doses.

    The two protein-binding examples are **documented cases, not trained models**.

    For your professor, the central interpretation is: **the toxicity experiment finds modest structural predictive information; B explains an outside model; the literature activity experiment remains exploratory and fails its new-paper test.**
    """)
    return


@app.cell(hide_code=True)
def _(Path, csv, hashlib, json, mo):
    _location = Path(mo.notebook_location()).resolve()
    repo = next(p for p in [_location, *_location.parents] if (p / "analysis/pyproject.toml").exists())
    inputs_checked = []

    def load_result(bundle, filename):
        root = repo / "analysis/outputs" / bundle
        path = root / filename
        manifest = json.loads((root / "manifest.json").read_text())
        mapping = manifest.get("outputs", manifest.get("output_hashes", {}))
        expected = mapping.get(filename, mapping.get(str(path)))
        if expected is None or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Missing or changed frozen result: {path}")
        inputs_checked.append({"bundle": bundle, "file": filename, "hash": "verified"})
        with path.open(newline="") as stream:
            return list(csv.DictReader(stream))

    release_name = "separate-evidence-2026-11-12-v2"
    model_name = "separate-evidence-models-2026-11-12-v3"
    compare_name = "separate-evidence-comparison-2026-11-12-v3"
    oob_name = "separate-evidence-multiclass-oob-2026-11-12-v1"
    adoption_name = "human-review-adopted-2026-11-11-final"
    progress_name = "human-reviewed-progress-2026-11-11-complete"
    activity_name = "experimental-heterogeneous-diagnostics-2026-11-12"
    a_compounds = load_result(release_name, "A_compounds.csv")
    b_compounds = load_result(release_name, "B_compounds.csv")
    biological_membership = load_result(progress_name, "group_membership.csv")
    policy_models = load_result(adoption_name, "activity_models.csv")
    policy_names = {
        "K1998": "HUMAN-K1998-TWO-SPECIES-VERY-ACTIVE-1MM-v1",
        "Okamoto1991": "HUMAN-OKAMOTO-1991-UPLAND-10G-AI-PER-A-v0.1",
        "Li2006": "HUMAN-LI2006-AR-150G-POST-BOUNDS-v0.1",
        "He2011": "HUMAN-HE2011-AR-1500G-POST-BANDS-v0.1",
    }
    policy_labels = {name: load_result(adoption_name, policy + ".csv")
                     for name, policy in policy_names.items()}
    toxicity_scores = load_result(model_name, "pooled_metrics.csv")
    toxicity_weights = load_result(model_name, "weights.csv")
    toxicity_oob = load_result(oob_name, "importance.csv")
    bin_groups = load_result(compare_name, "descriptive_groups.csv")
    aquatic_coverage = load_result("ecotox-approved-comparison-2026-11-11-verified", "policy_coverage.csv")
    activity_scores = load_result(activity_name, "reports.csv")
    activity_oof = load_result(activity_name, "oof.csv")
    activity_weights = load_result(activity_name, "coefficients.csv")
    activity_oob = load_result(activity_name, "oob_importance.csv")
    transfer_scores = load_result("experimental-flavonoid-transfer-2026-11-12", "reports.csv")
    bindings = load_result("binding-structural-pilot-2026-11-12-final", "interactions.csv")
    return (
        a_compounds,
        activity_oob,
        activity_oof,
        activity_scores,
        activity_weights,
        aquatic_coverage,
        b_compounds,
        bin_groups,
        bindings,
        biological_membership,
        inputs_checked,
        policy_labels,
        policy_models,
        policy_names,
        toxicity_oob,
        toxicity_scores,
        toxicity_weights,
        transfer_scores,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. What compounds do I actually have?

    **Where B comes from:** stored CATMoS predictions in the model authors'
    [OPERA data archive](https://github.com/kmansouri/OPERA/blob/01b07c769dd86eadb71843e057783a64a364c885/OPERA_Data.zip),
    specifically `CATMoS_QR50k.sdf`, field `CATMoS_LD50_pred`. Structures, domain flags and training tags remain in the
    local B release. I did not generate these estimates by running OPERA locally.
    The **173-structure EPA TEST collection is separate** and is not the target
    behind the B classifier. A below uses measured experimental outcomes.

    Stored TEST coverage is now **173 full structures**; those stored estimates
    remain separate from experiments. My original prepared selection contains **60 selected herbicides and 116
    selected natural products**. Those are selection labels. For a stricter
    biological comparison, the reviewed set contains **19 natural-occurrence
    compounds: 5 active under K1998 and 14 activity-unknown**, with **0 reviewed
    natural low-response examples under that policy** and 58 distinct herbicide
    comparators. I cannot call unknown compounds non-herbicidal.

    Below I join that reviewed grouping to each new toxicity cohort by the full
    structure key. Counts are unique compounds, not dose rows or studies. A
    commercial comparator label does not automatically establish synthetic origin.
    """)
    return


@app.cell
def _(Counter, a_compounds, b_compounds, biological_membership, mo):
    _reviewed = {r["structure_inchikey"]: r["group"] for r in biological_membership}
    track1_counts = []
    for _pathway, _rows in [("A: measured rat LD50", a_compounds), ("B: CATMoS estimates", b_compounds)]:
        _groups = Counter(_reviewed.get(r["full_key"], "other_or_unclassified") for r in _rows)
        track1_counts.append({
            "Track 1 cohort": _pathway,
            "Natural active (K1998)": _groups["natural_active_K1998"],
            "Natural low-response (K1998)": _groups["natural_tested_low_response_K1998"],
            "Natural activity unknown": _groups["natural_activity_unknown"],
            "Herbicide comparators": _groups["selected_herbicide_comparator"],
            "Other/unclassified": _groups["other_or_unclassified"], "Total": len(_rows),
        })
    mo.ui.table(track1_counts, selection=None, pagination=False)
    return


@app.cell
def _(mo, policy_labels, policy_models, policy_names):
    track2_counts = []
    for _name, _rows in policy_labels.items():
        _active = [r for r in _rows if r["herbicidal_activity"] == "active"]
        _low = [r for r in _rows if r["herbicidal_activity"] == "inactive"]
        _reports = [r for r in policy_models if r["policy"] == policy_names[_name]]
        track2_counts.append({
            "Track 2 assay policy": _name, "High response": len(_active),
            "Low response": len(_low), "Reviewed natural among high": sum(
                r["natural_origin"] == "natural" for r in _active),
            "Reviewed natural among low": sum(r["natural_origin"] == "natural" for r in _low),
            "Five-fold activity model": "; ".join(sorted({r["status"] for r in _reports})),
        })
    mo.ui.table(track2_counts, selection=None, pagination=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The activity policies above use different species, doses and response rules;
    I do not add their counts together. Li/He/Okamoto activity does not supply
    reviewed natural occurrence. The **73-compound pooled sensitivity** has 41
    high and 32 low responses, including provisional identities. It is a separate
    exploratory experiment, not 73 reviewed natural products.

    In the compatible 27-compound radish series at 100 µM, there are **2 high,
    18 low and 7 intermediate** root-growth responses. Intermediates stay unknown.
    Its class/scaffold support is insufficient for five-fold fitting.
    """)
    return


@app.cell
def _(aquatic_coverage, bin_groups, mo):
    _bins = [{"Cohort": r["pathway"], "Selection group": r["group"],
              "Low LD50": int(r["bin_0_n"]), "Medium LD50": int(r["bin_1_n"]),
              "High LD50": int(r["bin_2_n"]), "Total": int(r["compounds"])} for r in bin_groups]
    _aquatic = [{"Aquatic policy": r["policy"], "Compounds": int(r["distinct_compounds"]),
                 "Observations": int(r["approved_slots"])} for r in aquatic_coverage]
    mo.vstack([
        mo.ui.table(_bins, selection=None, pagination=False, label="Track 1: selection groups and LD50 bins"),
        mo.ui.table(_aquatic, selection=None, pagination=False, label="Separate measured aquatic coverage"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Exploring the toxicity classifiers

    I predict **LD50 bin**, not natural origin or herbicidal activity. Low LD50
    means greater acute hazard. The fixed 1,080/3,400 mg/kg cutoffs are historical
    cohort bins, not regulatory categories. Aquatic concentrations stay separate.

    I used five scaffold/connectivity-held-out folds. Scaling is fitted on each
    training fold. Logistic uses C=1 and balanced class weights; the forest uses
    200 trees, minimum leaf size 5 and balanced class weights. Seven predictors
    come from structures. I have not tuned these models against the test scores.
    """)
    return


@app.cell
def _(mo):
    pathway = mo.ui.dropdown(
        options={"A · experimental LD50 outcomes": "A", "B · CATMoS estimates": "B"},
        value="A · experimental LD50 outcomes", allow_select_none=False, label="Toxicity experiment",
    )
    pathway
    return (pathway,)


@app.cell
def _(mo, pathway, toxicity_scores):
    _rows = [r for r in toxicity_scores if r["pathway"] == pathway.value and r["task"] == "classification"]
    toxicity_f1_table = [{
        "Model": r["profile"], "Macro-F1 (held out)": round(float(r["macro_f1"]), 3),
        "Low-bin F1": round(float(r["class_0_f1"]), 3),
        "Medium-bin F1": round(float(r["class_1_f1"]), 3),
        "High-bin F1": round(float(r["class_2_f1"]), 3),
        "Balanced accuracy": round(float(r["balanced_accuracy"]), 3), "Compounds": int(r["n"]),
    } for r in _rows]
    mo.ui.table(toxicity_f1_table, selection=None, pagination=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    My A forest reaches **macro-F1 0.430**, compared with majority **0.226**;
    logistic is **0.382**. B reaches **0.616**, compared with majority **0.200**;
    logistic is **0.465**. B's higher F1 describes teacher reproduction and does
    not make it a better experimental predictor.

    I also checked continuous dose error: A forest MAE is 0.636 log10 units
    versus baseline 0.650, a small improvement. The bin result is not a reliable
    general dose predictor. Nearly all paired A/B compounds overlap teacher
    training (3,359/3,361), so I leave combined modeling deferred.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. What did logistic learn?

    Each coefficient multiplies a **one-training-fold-SD** feature change in a
    class's linear score. Positive raises that class's score; negative lowers it.
    For multiclass relative log-odds I need the **difference between two classes'
    coefficients**. These are associations among correlated features, not causes.

    I show fold means and sample SDs across five folds, not a newly fitted averaged model. Changing the
    class below changes which score I inspect. Fold SD is variability, not a p-value.
    """)
    return


@app.cell
def _(mo):
    ld50_class = mo.ui.dropdown(
        options={"Low LD50 · greater acute hazard": 0, "Medium LD50": 1, "High LD50": 2},
        value="Low LD50 · greater acute hazard", allow_select_none=False, label="Logistic class score",
    )
    ld50_class
    return (ld50_class,)


@app.cell(hide_code=True)
def _(alt, defaultdict, ld50_class, mo, np, pathway, toxicity_weights):
    _values = defaultdict(list)
    for _r in toxicity_weights:
        if _r["pathway"] == pathway.value and int(_r["class"]) == ld50_class.value:
            _values[_r["feature"]].append(float(_r["standardized_weight"]))
    logistic_summary = [{"Feature": k, "Mean coefficient": float(np.mean(v)),
                         "Fold SD": float(np.std(v, ddof=1)), "Folds": len(v)} for k, v in _values.items()]
    _chart = alt.Chart(alt.Data(values=logistic_summary)).mark_bar().encode(
        x=alt.X("Mean coefficient:Q", title="Standardized logistic coefficient"),
        y=alt.Y("Feature:N", sort="-x"),
        color=alt.condition("datum['Mean coefficient'] >= 0", alt.value("#35766b"), alt.value("#b36a43")),
        tooltip=[alt.Tooltip("Feature:N"), alt.Tooltip("Mean coefficient:Q", format=".3f"),
                 alt.Tooltip("Fold SD:Q", format=".3f")],
    ).properties(width=560, height=210)
    mo.vstack([mo.ui.altair_chart(_chart), mo.ui.table(
        [{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}
         for r in logistic_summary], selection=None, pagination=False)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What the structural features mean**

    | Feature | Simple meaning |
    |---|---|
    | **Molecular weight** | How heavy one molecule is; a rough measure of molecular size. |
    | **TPSA** | The calculated surface area associated with polar atoms, mainly oxygen and nitrogen. |
    | **HBA** | Number of sites that can **accept** a hydrogen bond. |
    | **HBD** | Number of groups that can **donate** a hydrogen bond, often OH or NH groups. |
    | **Rotatable bonds** | A rough measure of molecular flexibility. |
    | **Rings** | Number of closed atom loops in the structure. |
    | **Fraction sp³** | Fraction of carbon atoms with tetrahedral bonding; a rough indicator of saturated, potentially three-dimensional character. |

    **Strongest and weakest logistic features**

    These are the **largest and smallest absolute mean standardized coefficients**, not significance rankings. Each coefficient concerns the selected class’s score; a positive value raises that score. Relative odds between two classes depend on the difference between their coefficients.

    | Model / LD50 class | Strongest coefficients | Smallest coefficient |
    |---|---|---|
    | **A: low LD50** | HBA **+0.390**; TPSA **−0.388**; flexibility **−0.336** | HBD **−0.006** |
    | **A: medium LD50** | HBA **−0.132**; fraction sp³ **−0.093** | TPSA **−0.003** |
    | **A: high LD50** | TPSA **+0.391**; flexibility **+0.277** | HBD **−0.020** |
    | **B: low LD50** | TPSA **−1.070**; flexibility **−0.790** | HBD **+0.093** |
    | **B: medium LD50** | Molecular weight **−0.227**; fraction sp³ **−0.192** | Rings **+0.038** |
    | **B: high LD50** | TPSA **+1.229**; HBA **−0.628** | Molecular weight **−0.086** |

    The clearest shared pattern is that **greater polar surface area raises the high-LD50 score and lowers the low-LD50 score**. This is conditional on the other features. TPSA and HBA overlap chemically, so their opposite coefficients should not be interpreted as independent chemical mechanisms.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. What does the forest rely on?

    The forest has no single logistic-style weight vector. I measure importance
    as the **drop in OOB macro-F1 when a feature is shuffled**. For each tree I
    shuffle only its unsampled compounds, then aggregate class-probability votes.
    Here the target is the same three LD50 bins as above; the older binary
    low-LD50-versus-rest diagnostic is deliberately not substituted.

    Positive drop means the forest relies on the feature. Near-zero or negative
    drop means little measured reliance or a possible improvement after shuffling.
    Ten-repeat SD describes **stability**, not statistical significance or a
    confidence interval. Correlated features can share importance. OOB permits
    familiar scaffolds in training and is not the held-out accuracy headline.
    """)
    return


@app.cell(hide_code=True)
def _(alt, mo, pathway, toxicity_oob):
    forest_summary = [{"Feature": r["feature"], "OOB macro-F1 drop": float(r["mean_macro_f1_drop"]),
                       "Repeat SD": float(r["sd_macro_f1_drop"]),
                       "Lower": float(r["mean_macro_f1_drop"]) - float(r["sd_macro_f1_drop"]),
                       "Upper": float(r["mean_macro_f1_drop"]) + float(r["sd_macro_f1_drop"]),
                       "Baseline OOB macro-F1": float(r["baseline_oob_macro_f1"]),
                       "Repeats": int(r["repeats"])} for r in toxicity_oob if r["pathway"] == pathway.value]
    _base = alt.Chart(alt.Data(values=forest_summary)).encode(y=alt.Y("Feature:N", sort="-x"))
    _bars = _base.mark_bar(color="#526f9a").encode(x=alt.X("OOB macro-F1 drop:Q"))
    _ranges = _base.mark_rule(color="#263238").encode(x="Lower:Q", x2="Upper:Q")
    mo.vstack([
        mo.ui.altair_chart((_bars + _ranges).properties(width=560, height=210)),
        mo.ui.table([{k: round(v, 4) if isinstance(v, float) else v
                      for k, v in r.items() if k not in {"Lower", "Upper"}}
                     for r in forest_summary], selection=None, pagination=False),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Strongest and weakest forest features**

    Importance here is the **absolute drop in OOB macro-F1 after shuffling a feature**, averaged over ten repeats.

    | Forest | Greatest reliance | Least measured reliance |
    |---|---|---|
    | **A: experimental toxicity** | TPSA **0.031**; fraction sp³ **0.026**; rotatable bonds **0.018** | HBA **0.005**; rings **0.007** |
    | **B: CATMoS reproduction** | TPSA **0.160**; rotatable bonds **0.111**; molecular weight **0.080** | HBD and rings, both about **0.032** |

    These importances have **no direction**: a large TPSA importance does not itself say whether increasing TPSA increases or decreases toxicity. Correlated features can also substitute for one another.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5. Trying the literature activity question

    The reviewed individual policies cannot yet support five-fold activity
    modeling. I can still inspect my earlier **73-compound pooled sensitivity**:
    positive = high plant response, negative = low response under source-specific
    rules. Plants, doses and endpoints differ. This is exploratory pooling.

    I compare formula logistic with fingerprint logistic/forest, keeping their
    feature representations explicit. A high F1 needs a baseline and a new-paper
    test: F1 alone can look good when high responses dominate.
    """)
    return


@app.cell
def _(activity_oof, activity_scores, f1_score, mo, np, transfer_scores):
    _reference = [r for r in activity_oof if r["profile"] == "formula_raw"]
    _truth = np.array([int(r["label"]) for r in _reference])
    _majority = np.array([int(sum(int(s["label"]) for s in _reference if s["fold"] != r["fold"])
                                 >= sum(s["fold"] != r["fold"] for s in _reference) / 2)
                          for r in _reference])
    activity_f1_table = [{"Model": "Training-fold majority", "F1 (high response)":
                         float(f1_score(_truth, _majority)), "Balanced accuracy": 0.5,
                         "Compounds": len(_truth)}]
    activity_f1_table.extend({"Model": r["profile"], "F1 (high response)": float(r["f1"]),
                             "Balanced accuracy": float(r["balanced_accuracy"]), "Compounds": int(r["n"])}
                            for r in activity_scores if r["profile"] in
                            {"formula_raw", "morgan_logistic", "morgan_forest"})
    _new_paper = [{"New radish test": r["profile"], "F1 (high response)": float(r["f1"]),
                   "Test compounds": int(r["test_n"]), "High responses": int(r["test_active"]),
                   "Missed high responses": int(r["fn"])} for r in transfer_scores
                  if r["publication"] == "Flavonoids2012" and r["scenario"] == "publication_only"]
    mo.vstack([
        mo.ui.table([{k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}
                     for r in activity_f1_table], selection=None, pagination=False),
        mo.ui.table(_new_paper, selection=None, pagination=False),
    ])
    return


@app.cell
def _(activity_oob, activity_weights, defaultdict, mo, np):
    _by_feature = defaultdict(list)
    for _r in activity_weights:
        _by_feature[_r["feature"]].append(float(_r["coefficient"]))
    activity_weight_summary = sorted([
        {"Formula logistic feature": k, "Mean coefficient": float(np.mean(v)),
         "Fold SD": float(np.std(v, ddof=1))} for k, v in _by_feature.items()
    ], key=lambda r: abs(r["Mean coefficient"]), reverse=True)
    activity_forest_summary = sorted([
        {"Fingerprint forest feature": r["feature"], "OOB F1 drop": float(r["mean_f1_drop"]),
         "Repeat SD": float(r["std_f1_drop"]), "Baseline OOB F1": float(r["baseline_oob_f1"])}
        for r in activity_oob
    ], key=lambda r: r["OOB F1 drop"], reverse=True)
    mo.vstack([
        mo.ui.table([{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}
                     for r in activity_weight_summary], selection=None, page_size=8,
                    label="Formula logistic: positive means high source-specific response"),
        mo.ui.table([{k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}
                     for r in activity_forest_summary[:10]], selection=None, pagination=False,
                    label="Fingerprint forest: top 10 OOB F1 permutation drops"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What I take from this:** pooled fingerprint logistic F1 is 0.727 against
    majority 0.719; forest is 0.680. All three fixed profiles have **F1 = 0 on
    the new 20-compound radish test** and miss both high responses. The appealing
    within-pool score does not transfer. Coefficients/importance describe this
    pooled experiment, not a general signature of natural herbicidal activity.
    Fingerprint bits can encode multiple motifs; I cannot name a unique chemical
    mechanism from a bit number. OOB SD is not a significance test.

    ## 6. Binding evidence stays a separate experiment

    I have two structural cases, tentoxin and cornexistin's bound diacid, rather
    than a binding classifier. I can describe their exact forms, protein partners
    and contacts; there is no measured Kd/Ki training target or binding-model F1.
    """)
    return


@app.cell
def _(bindings, mo):
    mo.ui.table([{
        "Parent": r["parent_name"], "PDB": r["pdb_id"], "Bound ligand": r["ligand_name"],
        "Form relationship": r["parent_bound_relationship"], "Resolution (Å)": r["resolution_angstrom"],
        "Affinity label": r["affinity_endpoint"] or "unavailable",
    } for r in bindings], selection=None, pagination=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### My next experiment

    I want more compatible active/low-response literature series and reviewed
    natural-occurrence annotations on the measured toxicity cohort. I will keep
    source, species, dose and chemical form visible, and test new-paper transfer
    before interpreting a feature as useful for screening. I am leaving A/B
    combined modeling deferred. Changing the controls here explores saved results;
    it does not silently refit or overwrite any frozen experiment.
    """)
    return


@app.cell(hide_code=True)
def _(inputs_checked, mo):
    mo.ui.table(inputs_checked, selection=None, page_size=8, label="Frozen inputs verified on load")
    return


if __name__ == "__main__":
    app.run()
