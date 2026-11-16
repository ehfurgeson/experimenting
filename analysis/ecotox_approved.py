"""Version explicit ECOTOX identity approval and compare context-admitted observations."""
import argparse
import json
import shutil
import tempfile
from datetime import date
from pathlib import Path

import polars as pl
from agrotox.ecotox_selected import identities
from rdkit import Chem

from review_adoption import read_csv
from screen import HERE, hashes, write_csv
from weekly_report import verify_manifest


def canonical_index(selection, packets):
    """Check canonical representations without treating model eligibility as identity."""
    result = {}
    for row in [*selection, *packets]:
        cid = row['compound_id']
        smiles = row.get('database_smiles') or row.get('input_smiles') or row.get('canonical_structure')
        mol = Chem.MolFromSmiles(smiles or '')
        expected = row.get('database_inchikey') or row.get('inchikey') or row.get('structure_inchikey')
        if mol is None or not mol.GetNumAtoms():
            # Retain unavailable rows; approval can only reference checked representations.
            continue
        key = Chem.MolToInchiKey(mol)
        if not expected or key != expected:
            raise ValueError('Canonical SMILES/key disagreement: '+cid)
        if cid in result and result[cid]['inchikey'] != key:
            raise ValueError('Conflicting canonical representations: '+cid)
        result[cid] = {'compound_id': cid, 'name': row.get('name') or row.get('query') or cid,
                       'canonical_smiles': Chem.MolToSmiles(mol), 'inchikey': key,
                       'structure_model_status': row.get('structure_status', 'not_assessed')}
    return result


def approve_pairs(candidates, selected, canonical, declaration, snapshot):
    required = ('approval_id', 'reviewer', 'review_date', 'statement', 'snapshot_sha256')
    if not all(declaration.get(k) for k in required) or declaration.get('scope') != 'all_selected_ecotox_identity_mappings':
        raise ValueError('Explicit snapshot-specific human identity approval required')
    date.fromisoformat(declaration['review_date'])
    if declaration['snapshot_sha256'] != snapshot:
        raise ValueError('Human approval snapshot does not match the frozen source')
    source_ids = [r['source_chemical_id'] for r in candidates]
    if len(source_ids) != len(set(source_ids)) or set(source_ids) != set(selected):
        raise ValueError('Approve exactly one mapping for every selected source chemical')
    decisions, ledger = [], []
    for row in candidates:
        targets = [v.strip() for v in row.get('candidate_compound_ids', '').split(';') if v.strip()]
        if len(targets) != 1:
            raise ValueError('Ambiguous or missing canonical candidate requires an explicit reviewed mapping')
        if row['status'] in {'rejected', 'conflict'}:
            raise ValueError('An explicit conflict cannot be resolved by blanket approval')
        cid = targets[0]
        if cid not in canonical:
            raise ValueError('Approved candidate lacks a checked canonical representation: '+cid)
        if row.get('compound_id') and row['compound_id'] != cid:
            raise ValueError('Existing canonical identity conflicts with the candidate')
        info = canonical[cid]
        reference = (f"Human identity review {declaration['approval_id']}; snapshot={snapshot}; "
                     f"source={row['source_chemical_id']}; canonical={cid}; InChIKey={info['inchikey']}")
        decision = {**row, 'compound_id': cid, 'status': 'approved', 'match_type': 'exact_structure',
                    'source_identity_reference': reference, 'reviewer': declaration['reviewer'],
                    'review_date': declaration['review_date']}
        decisions.append(decision)
        ledger.append({'source_chemical_id': row['source_chemical_id'], **info,
                       'previous_status': row['status'], 'previous_match_type': row['match_type'],
                       'adopted_status': 'approved', 'approval_id': declaration['approval_id'],
                       'reviewer': declaration['reviewer'], 'review_date': declaration['review_date'],
                       'evidence_basis': 'User assertion of completed human source-identity review; canonical representation consistency checked computationally.'})
    identities(decisions, set(selected))
    return decisions, ledger


def publish(stage, output, manifest, inputs_before):
    if hashes([Path(p) for p in inputs_before]) != inputs_before:
        raise ValueError('Source inputs changed during execution')
    manifest['input_hashes'] = inputs_before
    manifest['output_hashes'] = {str(output/Path(k).name): v for k,v in hashes(list(stage.iterdir())).items()}
    manifest['code_hashes'] = hashes([Path(__file__)])
    manifest['lock_hashes'] = hashes([HERE/'uv.lock', HERE/'pyproject.toml'])
    (stage/'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False)+'\n')
    if output.exists():
        raise ValueError('Output appeared before publication; refusing overwrite')
    stage.rename(output)
    return manifest


def adopt(cohort, selected_bundle, selection, review, approval, output):
    cohort, selected_bundle, selection, review, approval, output = [Path(p).resolve() for p in
        (cohort, selected_bundle, selection, review, approval, output)]
    if output.exists() or any(p.is_relative_to(output) or output.is_relative_to(p) for p in
                             (cohort, selected_bundle, selection, review, approval)):
        raise ValueError('Use a fresh output directory separate from inputs')
    for root in (cohort, selected_bundle, review):
        verify_manifest(root/'manifest.json')
    inputs = [cohort/'manifest.json', cohort/'chemical_ids.csv', cohort/'source_identity_decisions.csv',
              selected_bundle/'manifest.json', selection, review/'manifest.json', approval]
    before = hashes(inputs)
    coverage = pl.read_parquet(selected_bundle/'coverage.parquet')
    selected = [r['source_chemical_id'] for r in read_csv(cohort/'chemical_ids.csv')]
    if set(coverage['source_chemical_id'].to_list()) != set(selected) or len(set(selected)) != len(selected):
        raise ValueError('Cohort does not match the frozen selected results')
    snapshots = pl.read_parquet(selected_bundle/'native_observations.parquet')['snapshot_id'].unique().to_list()
    if len(snapshots) != 1:
        raise ValueError('A single frozen source snapshot is required')
    canonical = canonical_index(pl.read_parquet(selection).to_dicts(), read_csv(review/'compound_packets.csv'))
    declaration = json.loads(approval.read_text())
    decisions, ledger = approve_pairs(read_csv(cohort/'source_identity_decisions.csv'), selected,
                                       canonical, declaration, snapshots[0])
    output.parent.mkdir(parents = True, exist_ok = True)
    stage = Path(tempfile.mkdtemp(prefix = '.ecotox-approval-', dir = output.parent))
    try:
        write_csv(stage/'approved_crosswalk.csv', decisions, list(decisions[0]))
        write_csv(stage/'identity_approval_ledger.csv', ledger, list(ledger[0]))
        (stage/'approval_statement.json').write_bytes(approval.read_bytes())
        (stage/'chemical_ids.csv').write_bytes((cohort/'chemical_ids.csv').read_bytes())
        return publish(stage, output, {'approved_source_identities': len(decisions),
                       'snapshot_id': snapshots[0], 'approval': declaration,
                       'scope': 'Human-reviewed identity mappings only; endpoint eligibility, biological labels and study-duplicate decisions remain independent.'}, before)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    sub = parser.add_subparsers(dest = 'command', required = True)
    adoption = sub.add_parser('adopt')
    for key in ('cohort','selected-bundle','selection','review','approval','output'):
        adoption.add_argument('--'+key, type = Path, required = True)
    args = parser.parse_args()
    result = adopt(args.cohort,args.selected_bundle,args.selection,args.review,args.approval,args.output)
    print(json.dumps({'approved_source_identities': result['approved_source_identities'],
                      'snapshot_id': result['snapshot_id']}, indent = 2))
