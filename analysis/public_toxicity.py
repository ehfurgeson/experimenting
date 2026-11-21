"""Rebuild provisional ICE and pinned CATMoS cohorts from the two public inputs."""

import argparse
import json
from collections import Counter
from pathlib import Path

from data_sprint import sha256
from evidence_release import (
    catmos_compounds,
    catmos_prediction,
    ice_compounds,
    ice_observation,
    sdf_properties,
    structure,
    workbook_rows,
    write_csv,
)


def run(ice, opera, output):
    inputs = {str(path): sha256(path) for path in (ice, opera)}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    identities, by_key, memo = [], {}, {}

    def identify(cohort, native_id, smiles):
        if smiles not in memo:
            memo[smiles] = structure(smiles)
        identity = memo[smiles]
        if identity.get('full_key'):
            by_key[identity['full_key']] = identity
        identities.append({'source_cohort': cohort, 'native_id': native_id,
                           'source_smiles': smiles, **identity})
        return identity

    a = [ice_observation(row, loc, identify('ICE', row['Record_ID'], row.get('SMILES')))
         for loc, row in workbook_rows(ice, 'Data')]
    b = [catmos_prediction(row, loc, identify('CATMoS', row['ChemID'], row.get('Canonical_QSARr')))
         for loc, row in sdf_properties(opera)]
    ac, bc = ice_compounds(a, by_key), catmos_compounds(b, by_key)
    members = []
    for cohort, compounds in [('A', ac), ('B', bc)]:
        members.extend({'cohort': cohort, 'compound_id': row['full_key'],
                        'full_inchikey': row['full_key'], 'original_structure': row['smiles'],
                        'identity_status': 'valid', 'selection_group': '',
                        'target_log10_mg_kg': row['target_log10_mg_kg']} for row in compounds)
    coverage = {'A': dict(Counter(row['status'] for row in a)),
                'B': dict(Counter(row['status'] for row in b)),
                'A_compounds': len(ac), 'B_compounds': len(bc),
                'TEST_compounds': 0, 'TEST_records': 0, 'selection_rows': 0}
    for name, rows in [
        ('A_observations', a), ('B_predictions', b), ('A_compounds', ac), ('B_compounds', bc),
        ('chemical_identity', identities), ('cohort_membership', members),
    ]:
        write_csv(output / f'{name}.csv', rows)
    (output / 'coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    if inputs != {str(path): sha256(path) for path in (ice, opera)}:
        raise ValueError('Public inputs changed during reconstruction')
    products = {p.name: sha256(p) for p in output.iterdir()}
    manifest = {'inputs': inputs, 'outputs': products, 'products': products,
                'protocol_sha256': sha256(Path(__file__).with_name('docs') / 'modeled-evidence.md'),
                'code': {name: sha256(Path(__file__).with_name(name))
                         for name in ('public_toxicity.py', 'evidence_release.py')},
                'status': 'reconstructed_public_cohorts',
                'limits': 'Accepted selection, human review and TEST caches are unavailable here.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return coverage


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('ice', 'opera', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.ice, args.opera, args.output), indent=2))
