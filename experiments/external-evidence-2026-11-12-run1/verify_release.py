"""Independent end-to-end checks for the canonical local evidence checkpoint."""
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from rdkit import Chem

sys.path.insert(0, str(Path('analysis').resolve()))
from evidence_release import workbook_rows

ROOT = Path('experiments/external-evidence-2026-11-12-run1')
RELEASE = Path('analysis/outputs/separate-evidence-2026-11-12-v2')
MODELS = Path('analysis/outputs/separate-evidence-models-2026-11-12-v3')
COMPARISON = Path('analysis/outputs/separate-evidence-comparison-2026-11-12-v3')
DIETARY = ROOT / 'dietary-test-v1'


def read(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


checks = {}
products = 0
for root in (RELEASE, MODELS, COMPARISON, DIETARY):
    manifest = json.loads((root / 'manifest.json').read_text())
    for name, expected in manifest['outputs'].items():
        assert sha(root / name) == expected, ('output hash', root, name)
        products += 1
    for path, expected in manifest.get('code', {}).items():
        candidates = [root / 'reproduction' / path.replace('/', '__'),
                      root / 'reproduction' / Path(path).name]
        assert any(p.is_file() and sha(p) == expected for p in candidates), ('code recovery', path)
checks['verified_product_hashes'] = products
reference = json.loads((ROOT / 'independent-openpyxl-ice.json').read_text())
parsed = list(workbook_rows(ROOT / 'sources/ice-acute-oral.xlsx', 'Data'))
assert len(reference) == len(parsed) == 16721
assert all(loc == n and raw == fields for (loc, raw), (n, fields) in zip(reference, parsed))
checks['independent_source_cell_comparison_rows'] = len(parsed)
# Read property samples through RDKit's SDF parser, not the release parser.
samples = {1, 2, 3, 101, 9999, 25000, 40000, 50660}
source_b = read(RELEASE / 'B_predictions.csv')
block, ordinal, compared = [], 0, 0
with zipfile.ZipFile(ROOT / 'sources/OPERA_Data.zip') as archive:
    with archive.open('CATMoS_QR50k.sdf') as stream:
        for line in io.TextIOWrapper(stream):
            block.append(line)
            if line.strip() == '$$$$':
                ordinal += 1
                if ordinal in samples:
                    supplier = Chem.SDMolSupplier()
                    supplier.SetData(''.join(block), sanitize = False, removeHs = False)
                    molecule = supplier[0]
                    assert molecule is not None
                    properties = molecule.GetPropsAsDict(autoConvertStrings = False)
                    raw = json.loads(source_b[ordinal - 1]['source_record_json'])
                    for key in ('ChemID', 'Canonical_QSARr', 'CATMoS_LD50_pred', 'AD_CATMoS'):
                        assert properties[key] == raw[key]
                    compared += 1
                block = []
assert ordinal == len(source_b) == 50660 and compared == len(samples)
checks['independent_RDKit_SDF_samples'] = compared
# Recalculate the prepared medians without the release's summarization function.
bykey = defaultdict(set)
for r in read(RELEASE / 'A_observations.csv'):
    if r['status'] == 'exact':
        bykey[r['full_key']].add((r['reference'], r['sex'], float(r['value_mg_kg'])))
a = read(RELEASE / 'A_compounds.csv')
b = read(RELEASE / 'B_compounds.csv')
assert len(a) == len(bykey) == 4234
for r in a:
    dose = median(v for _, _, v in bykey[r['full_key']])
    assert math.isclose(math.log10(dose), float(r['target_log10_mg_kg']), abs_tol = 1e-12)
conflicts = {r['full_key'] for r in read(RELEASE / 'B_duplicate_resolution.csv')
             if r['status'] == 'conflict_excluded'}
assert len(conflicts) == 2985
assert not conflicts & {r['full_key'] for r in b}
checks['A_medians_independently_recomputed'] = len(a)
checks['B_conflicting_structure_groups_excluded'] = len(conflicts)
# Audit each actual fold against original connectivity/scaffold, not only merged labels.
cohorts = {'A': {r['full_key']: r for r in a}, 'B': {r['full_key']: r for r in b}}
folds = defaultdict(lambda: defaultdict(set))
for r in read(MODELS / 'splits.csv'):
    folds[(r['pathway'], r['fold'])][r['role']].add(r['full_key'])
for (pathway, fold), roles in folds.items():
    assert not roles['train'] & roles['test']
    assert roles['train'] | roles['test'] == set(cohorts[pathway])
    for attribute in ('connectivity', 'scaffold'):
        train = {cohorts[pathway][k][attribute] for k in roles['train']}
        test = {cohorts[pathway][k][attribute] for k in roles['test']}
        assert not train & test, (pathway, fold, attribute)
checks['independently_verified_outer_folds'] = len(folds)
# Recompute pooled MAE/RMSE and macro-F1 from raw predictions with plain arithmetic.
strata = defaultdict(list)
for r in read(MODELS / 'predictions.csv'):
    strata[(r['pathway'], r['task'], r['profile'])].append(r)
for metric in read(MODELS / 'pooled_metrics.csv'):
    key = (metric['pathway'], metric['task'], metric['profile'])
    rs = strata[key]
    assert len({r['full_key'] for r in rs}) == len(rs) == len(cohorts[key[0]])
    if key[1] == 'regression':
        errors = [float(r['predicted']) - float(r['observed']) for r in rs]
        assert math.isclose(sum(abs(v) for v in errors) / len(errors),
                            float(metric['mae_log10']), abs_tol = 1e-10)
        assert math.isclose(math.sqrt(sum(v * v for v in errors) / len(errors)),
                            float(metric['rmse_log10']), abs_tol = 1e-10)
    else:
        confusion = Counter((int(r['observed']), int(r['predicted'])) for r in rs)
        f1 = []
        for c in range(3):
            tp = confusion[c, c]
            denom = sum(n for (y, p), n in confusion.items() if y == c)
            denom += sum(n for (y, p), n in confusion.items() if p == c)
            f1.append(2 * tp / denom if denom else 0)
        assert math.isclose(sum(f1) / 3, float(metric['macro_f1']), abs_tol = 1e-12)
checks['pooled_metric_profiles_independently_recomputed'] = len(strata)
summary = json.loads((COMPARISON / 'summary.json').read_text())
assert summary['unique_TEST_full_structures'] == 173
assert summary['additional_TEST_compounds'] == 37
assert summary['paired_known_teacher_training_compounds'] == 3359
assert summary['C'] == 'defer'
checks['coverage_lineage_C_checks'] = True
# Credential equality check emits no secret value or request headers.
key = None
for line in Path('.env').read_text().splitlines():
    name, sep, value = line.partition('=')
    if sep and name.strip() == 'COMPTOX_API_KEY':
        key = value.strip().strip('"').strip("'").encode()
if key:
    for root in (ROOT, RELEASE, MODELS, COMPARISON):
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in {'.json', '.csv', '.html', '.py', '.md'}:
                assert key not in path.read_bytes(), 'Credential found in output'
checks['credential_not_in_local_text_products'] = True
checks['verifier_sha256'] = sha(__file__)
(ROOT / 'verification.json').write_text(json.dumps(checks, indent = 2) + '\n')
print(json.dumps(checks, indent = 2))
