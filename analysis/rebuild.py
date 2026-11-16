"""Rebuild professor-facing products from existing read-only source caches."""

import argparse
import hashlib
import json
import runpy
from datetime import UTC, datetime
from pathlib import Path

from endpoint_analysis import build_sources

HERE = Path(__file__).resolve().parent
DEFINITIONS = HERE.parent / "pipeline" / "examples" / "endpoints.yaml"


def rebuild(source: Path, output: Path, definitions: Path = DEFINITIONS):
    """Run retained analyses into a separate directory without copying raw data."""
    source, output = source.resolve(), output.resolve()
    if source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError("Output must be outside the source directory")
    rules, pubchem, epa = build_sources(source, definitions)
    if epa is None and (output / "epa_analysis").exists():
        raise ValueError("Use a clean output directory for a PubChem-only rebuild")
    output.mkdir(parents = True, exist_ok = True)
    steps = [
        ("build_traits.py", {
            "DATA_ROOT": source, "SELECTION": source / "compounds.csv",
            "CLASSES": source / "compound_classes.csv", "DEFINITIONS": definitions,
            "EXTRA": source / "raw" / "pubchem_computed",
            "TRAITS": output / "traits.parquet", "COMPOUNDS": output / "compound_traits.parquet",
            "COMPOUNDS_CSV": output / "compound_traits.csv",
        }),
        ("distributions.py", {"COMPOUNDS": output / "compound_traits.parquet",
                              "OUTPUT": output / "distributions.csv"}),
        ("compare.py", {"COMPOUNDS": output / "compound_traits.parquet",
                        "OUTPUT": output / "comparison.csv"}),
        ("classifiers.py", {"COMPOUNDS": output / "compound_traits.parquet",
                            "OUTPUT": output / "classifiers.csv"}),
    ]
    if epa is not None:
        steps.insert(1, ("endpoint_coverage.py", {
            "DATA": source, "DEFINITIONS": definitions, "OUTPUT": output / "epa_endpoint_coverage.csv",
        }))
    for name, settings in steps:
        namespace = runpy.run_path(str(HERE / name))
        namespace["main"].__globals__.update(settings)
        namespace["main"]()
    # Capture every consumed raw dependency, cached descriptor, and optional
    # coverage input, plus code. Generated products are separate hashes.
    dependencies = {Path(path) for path in pubchem.dependencies}
    if epa is not None:
        dependencies.update(Path(path) for path in epa.dependencies)
    dependencies.update({source / "compounds.csv", source / "compound_classes.csv", definitions})
    dependencies.update(source / "raw" / "pubchem_computed" / f"{cid}.json"
                        for cid in pubchem["compounds"]["pubchem_cid"].drop_nulls())
    dependencies.update(source / name for name in [
        "toxcast_coverage.parquet", "epa_property_coverage.parquet",
    ] if (source / name).exists())
    dependencies.update(HERE.glob("*.py"))
    dependencies.update((HERE.parent / "pipeline" / "src" / "agrotox").rglob("*.py"))
    def hashes(paths):
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(paths) if path.exists()}
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(), "source": str(source),
        "endpoint_policies": rules, "epa_available": epa is not None,
        "input_hashes": hashes(dependencies),
        "output_hashes": hashes([*output.glob("*.csv"), *output.glob("*.parquet"),
                                 *(output / "epa_analysis").glob("*.parquet")]),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent = 2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument("--source", type = Path, required = True,
                        help = "Existing selection, descriptor, PubChem, and EPA caches")
    parser.add_argument("--output", type = Path, default = HERE / "data")
    parser.add_argument("--definitions", type = Path, default = DEFINITIONS)
    args = parser.parse_args()
    manifest = rebuild(args.source, args.output, args.definitions)
    print(f"Rebuilt {len(manifest['output_hashes'])} products in {args.output}")


if __name__ == "__main__":
    main()
