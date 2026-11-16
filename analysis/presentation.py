"""Presentation views preserve denominators and distinguish evidence from potency."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import polars as pl

ENDPOINTS = [
    ("LD50", "mammal_oral_ld50", "Mammal oral · mg/kg"),
    ("LC50", "fish_lc50", "Fish · mg/L"),
    ("EC50", "daphnia_ec50_48h", "Daphnia, 48 h · mg/L"),
    ("NOAEL", "mammal_oral_noael_daily", "Mammal oral · mg/kg-day"),
    ("LOAEL", "mammal_oral_loael_daily", "Mammal oral · mg/kg-day"),
    ("BMD", "mammal_oral_bmd_daily", "Mammal oral · mg/kg-day"),
    ("BMDL", "mammal_oral_bmdl_daily", "Mammal oral · mg/kg-day"),
]


GROUPS = {"herbicide": "Herbicides", "natural_product": "Natural compounds"}
METRICS = {
    "molecular_weight": "Molecular weight (g/mol)", "xlogp": "XLogP",
    "tpsa": "Polar surface area (Å²)", "complexity": "Molecular complexity",
    "hbond_donor_count": "Hydrogen-bond donors", "hbond_acceptor_count": "Hydrogen-bond acceptors",
    "rotatable_bond_count": "Rotatable bonds", "heavy_atom_count": "Heavy atoms",
    "annotation_count": "PubChem annotations", "epa_hazard_records": "EPA hazard records",
    "epa_measured_properties": "EPA measured properties",
    "epa_calculated_properties": "EPA calculated properties",
    "toxcast_inactive_fraction": "ToxCast inactive fraction",
    "toxcast_assays": "ToxCast assays", "toxcast_hits": "ToxCast hits",
    "formal_charge": "Formal charge", "exact_mass": "Exact mass (Da)",
    "monoisotopic_mass": "Monoisotopic mass (Da)",
    "defined_atom_stereo_count": "Defined stereocenters", "covalent_unit_count": "Covalent units",
    "isotope_atom_count": "Isotope atoms",
}


def load_results(data: Path):
    """Read prepared products only after verifying their recorded hashes."""
    manifest_path = data / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("Prepare data first: python analysis/rebuild.py --source <cache-root>")
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest["output_hashes"].items():
        path = Path(name)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Prepared product changed; rebuild before presenting: {path.name}")
    tables = {
        "traits": pl.read_parquet(data / "compound_traits.parquet"),
        "comparison": pl.read_csv(data / "comparison.csv"),
        "models": pl.read_csv(data / "classifiers.csv"),
    }
    tables["measurements"] = (
        pl.read_parquet(data / "epa_analysis" / "measurements.parquet")
        if manifest["epa_available"] else pl.DataFrame()
    )
    return tables, manifest


def endpoint_distribution(traits, source = "combined"):
    """Return selected-compound distributions of found, absent, and unknown flags."""
    prefixes = {"combined": "has_", "epa": "has_epa_", "pubchem": "has_pubchem_"}
    if source not in prefixes:
        raise ValueError("Unknown endpoint source")
    rows = []
    for endpoint, policy, context in ENDPOINTS:
        for group, label in GROUPS.items():
            selected = [r for r in traits.to_dicts() if r["chemical_group"] == group]
            values = [r.get(prefixes[source] + policy) for r in selected]
            counts = Counter("Evidence found" if v == 1 else "No extracted match" if v == 0
                             else "Unassessed" for v in values)
            for order, state in enumerate(["Evidence found", "No extracted match", "Unassessed"]):
                rows.append({
                    "endpoint": endpoint, "context": context, "group": label,
                    "state": state, "order": order, "count": counts[state],
                    "selected": len(selected), "assessed": sum(v is not None for v in values),
                    "fraction": counts[state] / len(selected) if selected else 0.0,
                })
    return rows


def empirical_distributions(traits, names):
    """Construct exact, group-normalized CDFs; nulls and nonfinite values are excluded."""
    rows = []
    for name in names:
        if name not in traits.columns:
            continue
        for group, label in GROUPS.items():
            values = [r[name] for r in traits.to_dicts() if r["chemical_group"] == group
                      and isinstance(r[name], (int, float)) and not isinstance(r[name], bool)
                      and math.isfinite(r[name])]
            cumulative = 0
            for value, count in sorted(Counter(values).items()):
                cumulative += count
                rows.append({"trait": name, "metric": METRICS.get(name, name), "group": label,
                             "value": value, "cdf": cumulative / len(values), "n": len(values)})
    return rows


def endpoint_chart(rows):
    import altair as alt

    return alt.Chart(alt.Data(values = rows)).mark_bar(size = 24).encode(
        x = alt.X("fraction:Q", title = "Share of selected compounds",
                  scale = alt.Scale(domain = [0, 1]), axis = alt.Axis(format = "%", tickCount = 3)),
        y = alt.Y("group:N", title = None, sort = list(GROUPS.values())),
        color = alt.Color("state:N", title = None,
                          scale = alt.Scale(domain = ["Evidence found", "No extracted match", "Unassessed"],
                                            range = ["#277D79", "#E4ECEB", "#B7BFCA"]),
                          legend = alt.Legend(orient = "bottom")),
        order = "order:Q",
        tooltip = ["endpoint:N", "context:N", "group:N", "state:N", "count:Q", "selected:Q",
                   "assessed:Q", alt.Tooltip("fraction:Q", format = ".1%")],
    ).properties(width = 250, height = 85).facet(
        facet = alt.Facet("endpoint:N", sort = [r[0] for r in ENDPOINTS],
                          header = alt.Header(title = None, labelFontSize = 17)), columns = 3,
    ).configure_view(stroke = None).configure_axis(labelFontSize = 11, titleFontSize = 11)


def distribution_chart(rows, *, logarithmic = False):
    import altair as alt

    return alt.Chart(alt.Data(values = rows)).mark_line(interpolate = "step-after", strokeWidth = 2.5).encode(
        x = alt.X("value:Q", title = None,
                  scale = alt.Scale(type = "symlog") if logarithmic else alt.Scale(zero = False)),
        y = alt.Y("cdf:Q", title = "Share at or below value", scale = alt.Scale(domain = [0, 1]),
                  axis = alt.Axis(format = "%", tickCount = 4)),
        color = alt.Color("group:N", title = None,
                          scale = alt.Scale(domain = list(GROUPS.values()), range = ["#286E80", "#BF6847"]),
                          legend = alt.Legend(orient = "bottom")),
        tooltip = ["metric:N", "group:N", "value:Q", alt.Tooltip("cdf:Q", format = ".1%"), "n:Q"],
    ).properties(width = 370, height = 190).facet(
        facet = alt.Facet("metric:N", sort = list(dict.fromkeys(r["metric"] for r in rows)),
                          header = alt.Header(title = None, labelFontSize = 14)), columns = 2,
    ).resolve_scale(x = "independent").configure_view(stroke = None)


def classifier_rows(models):
    """Select presentation targets; retain unavailable targets in the accompanying table."""
    labels = {"group_from_structure": "Herbicide vs natural compound",
              "mammal_oral_ld50_availability": "Oral LD50 availability (union)",
              "epa_mammal_oral_noael_daily_availability": "NOAEL availability (EPA)",
              "epa_mammal_oral_loael_daily_availability": "LOAEL availability (EPA)",
              "any_complete_measurement": "Any PubChem measurement",
              "studied_at_all": "Any PubChem annotation"}
    rows = []
    for row in models.to_dicts():
        if row["model"] not in labels or row["accuracy"] is None:
            continue
        for metric, value in [("Held-out accuracy", row["accuracy"]), ("Majority baseline", row["baseline"])]:
            rows.append({"target": labels[row["model"]], "metric": metric, "value": value,
                         "n": row["n"], "positives": row["positives"]})
    return rows


def classifier_chart(rows):
    import altair as alt

    return alt.Chart(alt.Data(values = rows)).mark_point(filled = True, size = 110).encode(
        x = alt.X("value:Q", title = "Accuracy", scale = alt.Scale(domain = [0, 1]),
                  axis = alt.Axis(format = "%")),
        y = alt.Y("target:N", title = None, sort = None),
        color = alt.Color("metric:N", title = None,
                          scale = alt.Scale(domain = ["Held-out accuracy", "Majority baseline"],
                                            range = ["#286E80", "#B7BFCA"]),
                          legend = alt.Legend(orient = "bottom")),
        tooltip = ["target:N", "metric:N", alt.Tooltip("value:Q", format = ".1%"), "n:Q", "positives:Q"],
    ).properties(width = 640, height = 250).configure_view(stroke = None)
