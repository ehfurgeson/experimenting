"""Experimental complexes must not become wrong-ligand, wrong-form or affinity labels."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from binding_catalog import audit_record, hydrolysis_connectivity, run
from structure import structure_features
from weekly_report import verify_manifest


def fixtures(smiles = 'CCO'):
    key = structure_features(smiles)['structure_inchikey']
    record = {'interaction_id': 'fixture', 'pdb_id': '1ABC', 'ligand_component_id': 'LIG',
              'parent_name': 'synthetic fixture', 'parent_bound_relationship': 'exact_parent',
              'primary_doi': '10.1234/fixture', 'target_entity_ids': ['1'],
              'natural_product_context': 'fixture only; no natural-origin claim',
              'source_locator': 'fixture structure', 'limits': 'synthetic test evidence',
              'parent_snapshot': 'parent.json', 'primary_source_file': 'paper.html'}
    entry = {'rcsb_id': '1ABC', 'rcsb_accession_info': {'status_code': 'REL'},
             'exptl': [{'method': 'X-RAY DIFFRACTION'}],
             'rcsb_primary_citation': {'pdbx_database_id_DOI': '10.1234/fixture'},
             'rcsb_entry_container_identifiers': {'polymer_entity_ids': ['1'], 'non_polymer_entity_ids': ['2']},
             'rcsb_entry_info': {'resolution_combined': [2.]}}
    component = {'chem_comp': {'id': 'LIG', 'name': 'fixture ligand'},
                 'rcsb_chem_comp_descriptor': {'SMILES_stereo': smiles, 'InChIKey': key}}
    nonpolymer = {'pdbx_entity_nonpoly': {'comp_id': 'LIG'},
                  'rcsb_nonpolymer_entity_container_identifiers': {'entry_id': '1ABC'}}
    proteins = {'1': {'rcsb_polymer_entity_container_identifiers': {
        'entry_id': '1ABC', 'entity_id': '1', 'asym_ids': ['A'], 'auth_asym_ids': ['B'],
        'reference_sequence_identifiers': [{'database_name': 'UniProt', 'database_accession': 'FIXTURE'}]},
        'entity_poly': {'rcsb_entity_polymer_type': 'Protein', 'pdbx_seq_one_letter_code_can': 'ACD\nEFGHIK'},
        'rcsb_entity_source_organism': [{'scientific_name': 'Plant fixture'}],
        'rcsb_entity_host_organism': [{'scientific_name': 'Bacterial expression fixture'}]}}
    parent = {'PropertyTable': {'Properties': [{'CID': 1, 'SMILES': smiles, 'InChIKey': key}]}}
    return record, entry, component, [nonpolymer], proteins, parent


def test_exact_structural_evidence_keeps_protein_construct_host_and_affinity_separate():
    interaction, proteins, fasta = audit_record(*fixtures())
    assert interaction['parent_inchikey'] == interaction['bound_inchikey']
    assert interaction['affinity_value'] is None and interaction['natural_origin_label'] == 'unknown'
    assert interaction['evidence_class'] == 'experimental_complex_structure'
    assert proteins[0]['target_organism'] == 'Plant fixture'
    assert proteins[0]['expression_host'] == 'Bacterial expression fixture'
    assert proteins[0]['uniprot_sequence_version'] is None
    assert fasta == [('1ABC_entity_1', 'ACDEFGHIK')]


def test_anhydride_opening_does_not_erase_the_exact_bound_form():
    parent = 'O=C1CCC(=O)O1'
    acid = 'O=C(O)CCC(=O)O'
    assert hydrolysis_connectivity(parent, acid)
    assert not hydrolysis_connectivity(parent, 'CCO')
    args = list(fixtures(acid))
    p = fixtures(parent)[-1]
    args[-1] = p
    with pytest.raises(ValueError, match = 'not the same exact'):
        audit_record(*args)
    args[0]['parent_bound_relationship'] = 'source_reported_anhydride_hydrolysis'
    args[0]['relationship_locator'] = 'fixture source depicts hydrolysis'
    row, _, _ = audit_record(*args)
    assert row['parent_formula'] != row['bound_formula']
    assert row['parent_inchikey'] != row['bound_inchikey']
    assert 'stereo_requires_source_review' in row['relationship_check']


@pytest.mark.parametrize('case', ['cofactor', 'wrong_key', 'parent_ambiguity', 'orphan_target',
                                  'other_entry', 'doi', 'nonexperimental', 'resolution', 'missing_reference'])
def test_wrong_component_identity_context_and_ambiguous_lookup_fail(case):
    args = list(copy.deepcopy(fixtures()))
    if case == 'cofactor':
        args[3][0]['pdbx_entity_nonpoly']['comp_id'] = 'ATP'
    elif case == 'wrong_key':
        args[2]['rcsb_chem_comp_descriptor']['InChIKey'] = 'WRONG'
    elif case == 'parent_ambiguity':
        args[-1]['PropertyTable']['Properties'] *= 2
    elif case == 'orphan_target':
        args[0]['target_entity_ids'] = ['2']
    elif case == 'other_entry':
        args[4]['1']['rcsb_polymer_entity_container_identifiers']['entry_id'] = '2XYZ'
    elif case == 'doi':
        args[0]['primary_doi'] = '10.1234/other'
    elif case == 'nonexperimental':
        args[1]['exptl'] = [{'method': 'COMPUTATIONAL MODEL'}]
    elif case == 'resolution':
        args[1]['rcsb_entry_info']['resolution_combined'] = [float('nan')]
    else:
        args[0]['primary_doi'] = ''
    with pytest.raises(ValueError):
        audit_record(*args)


def test_offline_command_preserves_sources_and_records_verified_products(tmp_path):
    record, entry, component, nonpolymers, proteins, parent = fixtures()
    snapshots = tmp_path / 'sources'
    snapshots.mkdir()
    files = {'1ABC_entry.json': entry, '1ABC_nonpolymer_2.json': nonpolymers[0],
             '1ABC_polymer_1.json': proteins['1'], 'LIG_chemcomp.json': component, 'parent.json': parent}
    for name, data in files.items():
        (snapshots / name).write_text(json.dumps(data))
    (snapshots / 'paper.html').write_text('Synthetic fixture DOI 10.1234/fixture')
    resource = tmp_path / 'records.json'
    resource.write_text(json.dumps({'records': [record]}))
    before = {p: p.read_bytes() for p in snapshots.iterdir()}
    output = tmp_path / 'out'
    manifest = run(resource, snapshots, output)
    assert manifest['interactions'] == manifest['protein_entities'] == 1
    assert manifest['models_fitted'] == 0
    verify_manifest(output / 'manifest.json')
    assert {p: p.read_bytes() for p in snapshots.iterdir()} == before
    with pytest.raises(ValueError, match = 'new output'):
        run(resource, snapshots, output)
    record['primary_source_file'] = '../outside.html'
    resource.write_text(json.dumps({'records': [record]}))
    with pytest.raises(ValueError, match = 'local'):
        run(resource, snapshots, tmp_path / 'invalid')
    assert not (tmp_path / 'invalid').exists()
