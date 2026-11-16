"""Offline audit of declared X-ray protein/ligand complexes; no affinity inference."""
import argparse
import hashlib
import json
import math
import re
from importlib.metadata import version
from pathlib import Path

from rdkit import Chem

from screen import HERE, hashes, write_csv
from structure import structure_features


def hydrolysis_connectivity(parent_smiles, bound_smiles):
    """Check one anhydride opening without claiming stereo or protonation equivalence."""
    parent, bound = Chem.MolFromSmiles(parent_smiles), Chem.MolFromSmiles(bound_smiles)
    if parent is None or bound is None:
        raise ValueError('Valid parent and bound SMILES required')
    Chem.RemoveStereochemistry(bound)
    expected = Chem.MolToSmiles(bound)
    query = Chem.MolFromSmarts('[CX3](=O)[OX2][CX3](=O)')
    for match in parent.GetSubstructMatches(query):
        for carbon in (match[0], match[3]):
            candidate = Chem.RWMol(parent)
            candidate.RemoveBond(match[2], carbon)
            oxygen = candidate.AddAtom(Chem.Atom(8))
            candidate.AddBond(carbon, oxygen, Chem.BondType.SINGLE)
            product = candidate.GetMol()
            Chem.SanitizeMol(product)
            Chem.RemoveStereochemistry(product)
            if Chem.MolToSmiles(product) == expected:
                return True
    return False


def audit_record(record, entry, component, nonpolymers, polymers, parent_payload):
    """Cross-check entry/component/parent identity and preserve the exact bound form."""
    pdb, ligand = record['pdb_id'], record['ligand_component_id']
    if entry.get('rcsb_id') != pdb or entry.get('rcsb_accession_info', {}).get('status_code') != 'REL':
        raise ValueError('Require the declared released PDB entry')
    if 'X-RAY DIFFRACTION' not in {r['method'] for r in entry.get('exptl', [])}:
        raise ValueError('This pilot requires an experimental X-ray complex')
    citation = entry.get('rcsb_primary_citation', {})
    if citation.get('pdbx_database_id_DOI', '').casefold() != record['primary_doi'].casefold():
        raise ValueError('Primary citation DOI disagrees with the declared complex')
    if component.get('chem_comp', {}).get('id') != ligand:
        raise ValueError('Wrong chemical-component snapshot')
    matching = [r for r in nonpolymers if r.get('pdbx_entity_nonpoly', {}).get('comp_id') == ligand]
    if not matching or any(r.get('rcsb_nonpolymer_entity_container_identifiers', {}).get('entry_id') != pdb
                           for r in matching):
        raise ValueError('Declared ligand is absent from the entry or belongs to another entry')
    descriptors = component.get('rcsb_chem_comp_descriptor', {})
    bound = structure_features(descriptors.get('SMILES_stereo'))
    if bound['structure_status'] != 'valid' or bound['structure_inchikey'] != descriptors.get('InChIKey'):
        raise ValueError('Bound-component SMILES and deposited full InChIKey disagree')
    properties = parent_payload.get('PropertyTable', {}).get('Properties', [])
    if len(properties) != 1:
        raise ValueError('Parent lookup must have exactly one structure, not a first-hit choice')
    parent_property = properties[0]
    parent = structure_features(parent_property.get('SMILES'))
    if (parent['structure_status'] != 'valid' or
            parent['structure_inchikey'] != parent_property.get('InChIKey')):
        raise ValueError('Parent SMILES and full InChIKey disagree')
    relation = record['parent_bound_relationship']
    exact = parent['structure_inchikey'] == bound['structure_inchikey']
    if relation == 'exact_parent':
        if not exact:
            raise ValueError('Parent and bound ligand are not the same exact structure')
        relation_check = 'full_inchikey_agrees'
    elif relation == 'source_reported_anhydride_hydrolysis':
        if exact or not record.get('relationship_locator') or not hydrolysis_connectivity(
                parent_property['SMILES'], descriptors['SMILES_stereo']):
            raise ValueError('Source-reported hydrolysis must match anhydride-opening connectivity')
        relation_check = 'anhydride_opening_connectivity_agrees_stereo_requires_source_review'
    else:
        raise ValueError('Unsupported parent/bound relationship; never silently substitute a form')
    container = entry['rcsb_entry_container_identifiers']
    targets, sequences = [], []
    if (not isinstance(record['target_entity_ids'], list) or not record['target_entity_ids'] or
            len(set(record['target_entity_ids'])) != len(record['target_entity_ids'])):
        raise ValueError('Declare unique target entity IDs')
    for entity_id in record['target_entity_ids']:
        if entity_id not in container.get('polymer_entity_ids', []) or entity_id not in polymers:
            raise ValueError('Declared target entity missing from the complex')
        entity = polymers[entity_id]
        ids = entity['rcsb_polymer_entity_container_identifiers']
        if ids.get('entry_id') != pdb or ids.get('entity_id') != entity_id:
            raise ValueError('Protein entity snapshot belongs to another entry/entity')
        polymer = entity.get('entity_poly', {})
        if polymer.get('rcsb_entity_polymer_type') != 'Protein':
            raise ValueError('Declared target must be a protein')
        sequence = re.sub(r'\s+', '', polymer.get('pdbx_seq_one_letter_code_can', ''))
        if not sequence or not re.fullmatch('[A-Z]+', sequence):
            raise ValueError('Canonical protein entity sequence is missing or unsupported')
        mappings = ids.get('reference_sequence_identifiers', [])
        uniprot = sorted({r['database_accession'] for r in mappings if r['database_name'] == 'UniProt'})
        organisms = entity.get('rcsb_entity_source_organism', [])
        hosts = entity.get('rcsb_entity_host_organism', [])
        targets.append({'pdb_id': pdb, 'entity_id': entity_id,
            'protein_name': entity.get('rcsb_polymer_entity', {}).get('pdbx_description'),
            'target_organism': ';'.join(sorted({r['scientific_name'] for r in organisms})),
            'expression_host': ';'.join(sorted({r['scientific_name'] for r in hosts})),
            'uniprot_accessions': ';'.join(uniprot), 'uniprot_sequence_version': None,
            'sequence_length': len(sequence),
            'sequence_sha256': hashlib.sha256(sequence.encode()).hexdigest(),
            'label_chain_ids': ';'.join(ids.get('asym_ids', [])),
            'author_chain_ids': ';'.join(ids.get('auth_asym_ids', [])),
            'sequence_scope': 'deposited entity construct; not an independently retrieved current UniProt sequence'})
        sequences.append((f'{pdb}_entity_{entity_id}', sequence))
    info = entry.get('rcsb_entry_info', {})
    resolution = min(info.get('resolution_combined', []), default = None)
    if type(resolution) not in {int, float} or not math.isfinite(resolution) or resolution <= 0:
        raise ValueError('The X-ray pilot requires a positive finite reported resolution')
    interaction = {'interaction_id': record['interaction_id'], 'pdb_id': pdb,
        'entry_title': entry.get('struct', {}).get('title'), 'ligand_component_id': ligand,
        'ligand_name': component['chem_comp'].get('name'), 'parent_name': record['parent_name'],
        'parent_pubchem_cid': parent_property.get('CID'),
        'parent_inchikey': parent['structure_inchikey'], 'bound_inchikey': bound['structure_inchikey'],
        'parent_formula': parent['derived_formula'], 'bound_formula': bound['derived_formula'],
        'parent_bound_relationship': relation, 'relationship_check': relation_check,
        'experimental_method': 'X-RAY DIFFRACTION',
        'resolution_angstrom': resolution,
        'experimental_data_released': entry.get('rcsb_accession_info', {}).get('has_released_experimental_data'),
        'entry_revision_date': entry.get('rcsb_accession_info', {}).get('revision_date'),
        'target_entity_ids': ';'.join(record['target_entity_ids']), 'primary_doi': record['primary_doi'],
        'evidence_class': 'experimental_complex_structure', 'affinity_endpoint': None,
        'affinity_value': None, 'affinity_unit': None, 'natural_origin_label': 'unknown',
        'natural_product_context': record['natural_product_context'],
        'source_locator': record['source_locator'], 'relationship_locator': record.get('relationship_locator', ''),
        'review_status': 'AI_experimental_not_independently_reviewed',
        'limits': record['limits']}
    return interaction, targets, sequences


def run(resource, snapshots, output):
    resource, snapshots, output = [Path(p).resolve() for p in (resource, snapshots, output)]
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (resource, snapshots)):
        raise ValueError('Use a new output directory separate from source inputs')
    resource_bytes = resource.read_bytes()
    records = json.loads(resource_bytes)['records']
    identities = [r['interaction_id'] for r in records]
    if (not records or any(not isinstance(i, str) or not i.strip() for i in identities) or
            len(set(identities)) != len(identities)):
        raise ValueError('Declare nonempty unique interaction records')
    inputs = [resource]
    before = {str(resource): hashlib.sha256(resource_bytes).hexdigest()}
    def remember(path, body):
        digest = hashlib.sha256(body).hexdigest()
        if str(path) in before and before[str(path)] != digest:
            raise ValueError('Inputs changed during structural audit')
        before[str(path)] = digest
    def read(name):
        path = (snapshots / name).resolve()
        if not path.is_relative_to(snapshots) or not path.is_file():
            raise ValueError('Snapshot must be inside the declared source directory')
        inputs.append(path)
        body = path.read_bytes()
        remember(path, body)
        return json.loads(body)
    interactions, targets, sequences = [], [], []
    for record in records:
        pdb, ligand = record['pdb_id'], record['ligand_component_id']
        if not re.fullmatch(r'[1-9][A-Z0-9]{3}', pdb) or not re.fullmatch('[A-Z0-9]{1,5}', ligand):
            raise ValueError('Use explicit four-character PDB and component identifiers')
        entry = read(f'{pdb}_entry.json')
        ids = entry['rcsb_entry_container_identifiers']
        nonpolymers = [read(f'{pdb}_nonpolymer_{eid}.json') for eid in ids.get('non_polymer_entity_ids', [])]
        polymers = {eid: read(f'{pdb}_polymer_{eid}.json') for eid in record['target_entity_ids']}
        interaction, proteins, fasta = audit_record(record, entry, read(f'{ligand}_chemcomp.json'),
            nonpolymers, polymers, read(record['parent_snapshot']))
        paper = (snapshots / record['primary_source_file']).resolve()
        if not paper.is_relative_to(snapshots):
            raise ValueError('Primary source file must be local and contain the declared DOI')
        body = paper.read_bytes()
        remember(paper, body)
        if record['primary_doi'].casefold() not in body.decode().casefold():
            raise ValueError('Primary source file must be local and contain the declared DOI')
        inputs.append(paper)
        interactions.append(interaction)
        targets.extend(proteins)
        sequences.extend(fasta)
    # The same target entity may occur in multiple ligand records; keep its one sequence.
    protein_map = {(r['pdb_id'], r['entity_id']): r for r in targets}
    sequence_map = dict(sequences)
    if hashes(inputs) != before:
        raise ValueError('Inputs changed during structural audit')
    output.mkdir(parents = True)
    write_csv(output / 'interactions.csv', interactions, list(interactions[0]))
    write_csv(output / 'protein_entities.csv', list(protein_map.values()), list(targets[0]))
    (output / 'protein_sequences.fasta').write_text(''.join(
        f'>{key}\n{sequence}\n' for key, sequence in sorted(sequence_map.items())))
    manifest = {'input_hashes': before, 'output_hashes': hashes(list(output.iterdir())),
        'code_hashes': hashes([Path(__file__), HERE / 'structure.py', HERE / 'formula.py', HERE / 'screen.py']),
        'lock_hashes': hashes([HERE / 'uv.lock', HERE / 'pyproject.toml']),
        'versions': {name: version(name) for name in ('rdkit', 'polars')},
        'interactions': len(interactions), 'protein_entities': len(protein_map), 'models_fitted': 0,
        'scope': 'Declared experimental structural-evidence pilot, not a validated affinity model, '
                 'natural-origin label set or safety claim. No docking scores or crystal incubation '
                 'concentrations become Kd/Ki. Protein construct sequences and parent/bound forms remain distinct.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2, allow_nan = False) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('resource', 'snapshots', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.resource, args.snapshots, args.output), indent = 2))
