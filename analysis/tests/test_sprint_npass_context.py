import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sprint_npass_context import activity_channel, occurrence_tier, plant_taxa, production_rows


def test_missing_taxonomy_never_joins_as_plant():
    taxa = plant_taxa({'a': {'kingdom_name': 'Viridiplantae', 'org_tax_id': '3702'},
                       'b': {'kingdom_name': 'Viridiplantae', 'org_tax_id': 'n.a.'}})
    assert taxa == {'3702'}
    raw = {'assay_tax_id': 'n.a.', 'activity_type': 'Inhibition'}
    target = {'target_organism_tax_id': 'n.a.', 'target_type': 'Cell line'}
    assert activity_channel(raw, target, taxa) is None


def test_plant_proteins_are_separate_from_growth_phenotypes():
    raw = {'assay_tax_id': '3702', 'activity_type': 'IC50'}
    target = {'target_organism_tax_id': '3702', 'target_type': 'Individual protein',
              'target_name': 'Growth enzyme'}
    assert activity_channel(raw, target, {'3702'}) == 'plant_protein_mechanism'
    target['target_type'] = 'Organism'
    target['target_name'] = 'Arabidopsis thaliana'
    assert activity_channel(raw, target, {'3702'}) == 'plant_organism_endpoint_unresolved'
    raw['activity_type'] = 'Root growth inhibition'
    assert activity_channel(raw, target, {'3702'}) == 'plant_phenotype_candidate'


def test_database_reference_is_not_taxon_publication_evidence():
    raw = {'ref_type': 'Database', 'ref_id_type': 'Database', 'ref_id': 'TM-MC'}
    assert occurrence_tier(raw, {'org_tax_id': '3702'}, {'identity_status': 'valid'}) == (
        'catalog_or_incomplete_occurrence_link')
    raw.update(ref_type = 'Publication', ref_id_type = 'PMID', ref_id = '12345')
    assert occurrence_tier(raw, {'org_tax_id': '3702'}, {'identity_status': 'valid'}) == (
        'taxon_and_publication_linked_unreviewed')
    assert occurrence_tier(raw, {'org_tax_id': '3702'}, {'identity_status': 'identity_hold'}) == (
        'identity_hold')


def test_production_context_keeps_distinct_roles_and_identity_holds(tmp_path):
    path = tmp_path / 'NPASS3.0_Coculture.tsv'
    path.write_text('np_id\torg_producer\torg_inducer\nA\tplant\tfungus\nB\tfungus\tplant\n')
    rows = list(production_rows(path, 'producer_inducer_context', {
        'A': {'full_inchikey': 'exact', 'identity_status': 'valid'},
        'B': {'full_inchikey': 'held', 'identity_status': 'provider_key_conflict'},
    }, {'exact', 'held'}))
    assert [r['join_status'] for r in rows] == ['exact_catalog_structure', 'identity_hold']
    assert '"org_inducer": "fungus"' in rows[0]['source_record_json']
