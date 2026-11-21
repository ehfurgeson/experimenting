"""Retain NPASS taxon/reference links and separate plant mechanism/phenotype leads."""

import argparse
import csv
import gzip
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from data_sprint import sha256, write_csv
from sprint_natural import baseline_members, source_file, tab_rows

PRODUCTION_TABLES = {
    'Coculture': 'producer_inducer_context',
    'Elicitation': 'elicited_production_context',
    'Engineer': 'engineered_production_context',
    'Symbiont': 'symbiont_association_context',
}


def production_rows(path, evidence_type, identities, wanted):
    for ordinal, raw in tab_rows(path):
        identity = identities.get(raw['np_id'], {})
        key = identity.get('full_inchikey', '')
        if key not in wanted:
            status = 'outside_cohort'
        elif identity['identity_status'] != 'valid':
            status = 'identity_hold'
        else:
            status = 'exact_catalog_structure'
        yield {'source_table': Path(path).name, 'source_record_ordinal': ordinal,
               'source_compound_id': raw['np_id'], 'full_inchikey': key,
               'evidence_type': evidence_type, 'join_status': status,
               'source_record_json': json.dumps(raw, sort_keys=True)}


def plant_taxa(species):
    # Missing sentinels must never join to each other as a taxonomic match.
    return {r['org_tax_id'] for r in species.values()
            if r['kingdom_name'] == 'Viridiplantae' and r['org_tax_id'].isdigit()}


def activity_channel(raw, target, taxa):
    if not ({raw['assay_tax_id'], target.get('target_organism_tax_id', '')} & taxa):
        return None
    kind = target.get('target_type', '')
    if kind in {'Individual protein', 'Single protein', 'Protein complex', 'Protein family'}:
        return 'plant_protein_mechanism'
    if kind in {'Organism', 'Phenotype'}:
        description = raw['activity_type'] + ' ' + target.get('target_name', '')
        if re.search(r'growth|germinat|radicle|root|shoot|biomass|herbicid|phytotox',
                     description, re.IGNORECASE):
            return 'plant_phenotype_candidate'
        return 'plant_organism_endpoint_unresolved'
    return 'plant_tissue_or_other_context'


def occurrence_tier(raw, organism, compound):
    if compound['identity_status'] != 'valid':
        return 'identity_hold'
    if (raw['ref_type'] == 'Publication' and raw['ref_id_type'] in {'PMID', 'DOI'} and
            raw['ref_id'] not in {'', '-', 'n.a.'} and organism.get('org_tax_id', '').isdigit()):
        return 'taxon_and_publication_linked_unreviewed'
    return 'catalog_or_incomplete_occurrence_link'


def run(registry, npass, baseline_path, output, production=None):
    npass, output = Path(npass), Path(output)
    names = ['npass-species', 'npass-occurrence', 'npass-activity', 'npass-target', 'npass-general']
    sources = {name: source_file(registry, name) for name in names}
    identity_path = npass / 'npass_identity.csv.gz'
    upstream = json.loads((npass / 'manifest.json').read_text())
    if sha256(identity_path) != upstream['products'][identity_path.name]:
        raise ValueError('NPASS identity bundle hash mismatch')
    inputs = [*sources.values(), identity_path, Path(baseline_path)]
    production_paths = {
        Path(production) / f'NPASS3.0_{table}.tsv': kind
        for table, kind in PRODUCTION_TABLES.items()
    } if production is not None else {}
    inputs.extend(production_paths)
    before = {str(p): sha256(p) for p in inputs}
    baseline = baseline_members(baseline_path)
    wanted = {r['full_inchikey'] for r in baseline if r['identity_status'] == 'valid'}
    with gzip.open(identity_path, 'rt') as stream:
        identities = {r['source_compound_id']: r for r in csv.DictReader(stream)}
    species = {r['org_id']: r for _, r in tab_rows(sources['npass-species'])}
    targets = {r['target_id']: r for _, r in tab_rows(sources['npass-target'])}
    general = {r['np_id']: r for _, r in tab_rows(sources['npass-general'])}
    taxa = plant_taxa(species)
    output.mkdir(parents = True, exist_ok = False)
    if production_paths:
        production_counts = {}
        with gzip.open(output / 'npass_production_context.jsonl.gz', 'wt',
                       encoding='utf-8') as stream:
            for path, kind in production_paths.items():
                counts = Counter()
                for record in production_rows(path, kind, identities, wanted):
                    counts[record['join_status']] += 1
                    stream.write(json.dumps(record) + '\n')
                production_counts[path.name] = dict(counts)
    tiers, channels, occurrence_keys, activity_keys = Counter(), Counter(), set(), set()
    occurrences, acquired_occurrences = 0, 0
    occurrence_fields = ['full_inchikey', 'source_database', 'source_compound_id',
                         'source_record_id', 'source_organism_id', 'taxon_id', 'taxon_name',
                         'citation', 'occurrence_evidence_type', 'exact_match',
                         'identity_confidence', 'provenance_confidence', 'original_structure',
                         'independent_primary_review', 'source_record_json']
    with gzip.open(output / 'npass_occurrences.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = occurrence_fields)
        writer.writeheader()
        for _, raw in tab_rows(sources['npass-occurrence']):
            acquired_occurrences += 1
            compound = identities.get(raw['np_id'])
            if not compound or compound['full_inchikey'] not in wanted:
                continue
            organism = species.get(raw['org_id'], {})
            tier = occurrence_tier(raw, organism, compound)
            writer.writerow({
                'full_inchikey': compound['full_inchikey'], 'source_database': 'NPASS_3.0',
                'source_compound_id': raw['np_id'], 'source_record_id': raw['src_org_record_id'],
                'source_organism_id': raw['org_id'], 'taxon_id': organism.get('org_tax_id', ''),
                'taxon_name': organism.get('org_name', ''),
                'citation': raw['ref_id_type'] + ':' + raw['ref_id'],
                'occurrence_evidence_type': tier, 'exact_match': compound['identity_status'] == 'valid',
                'identity_confidence': compound['identity_status'],
                'provenance_confidence': 'database_reported_not_primary_verified',
                'original_structure': compound['original_structure'],
                'independent_primary_review': False,
                'source_record_json': json.dumps({'occurrence': raw, 'organism': organism},
                                                 sort_keys = True)})
            occurrences += 1
            tiers[tier] += 1
            if tier == 'taxon_and_publication_linked_unreviewed':
                occurrence_keys.add(compound['full_inchikey'])
    fields = ['full_inchikey', 'source_compound_id', 'compound_name', 'source_record_id',
              'source_assay_id', 'source_target_id', 'evidence_channel', 'target_type',
              'target_name', 'plant_species',
              'plant_taxon_id', 'endpoint', 'reported_value', 'reported_unit', 'qualifier',
              'citation', 'experimental_dose', 'duration', 'control_context', 'activity_label',
              'review_status', 'identity_status', 'source_record_json']
    groups = defaultdict(list)
    acquired_activities = 0
    with gzip.open(output / 'npass_plant_assay_leads.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = fields)
        writer.writeheader()
        for ordinal, raw in tab_rows(sources['npass-activity']):
            acquired_activities += 1
            target = targets.get(raw['target_id'], {})
            channel = activity_channel(raw, target, taxa)
            if channel is None:
                continue
            compound = identities.get(raw['np_id'], {})
            key = compound.get('full_inchikey', '')
            writer.writerow({
                'full_inchikey': key, 'source_compound_id': raw['np_id'],
                'compound_name': general.get(raw['np_id'], {}).get('pref_name', ''),
                'source_record_id': f'activity:record{ordinal}',
                'source_assay_id': '', 'source_target_id': raw['target_id'],
                'evidence_channel': channel,
                'target_type': target.get('target_type', ''),
                'target_name': target.get('target_name', ''),
                'plant_species': raw['assay_organism'], 'plant_taxon_id': raw['assay_tax_id'],
                'endpoint': raw['activity_type'], 'reported_value': raw['activity_value'],
                'reported_unit': raw['activity_units'], 'qualifier': raw['activity_relation'],
                'citation': raw['ref_id_type'] + ':' + raw['ref_id'], 'experimental_dose': '',
                'duration': '', 'control_context': '', 'activity_label': 'unknown',
                'review_status': 'review_only_missing_assay_protocol_dose_control',
                'identity_status': compound.get('identity_status', 'unresolved'),
                'source_record_json': json.dumps({'activity': raw, 'target': target}, sort_keys = True)})
            channels[channel] += 1
            groups[(channel, raw['target_id'], raw['ref_id_type'] + ':' + raw['ref_id'],
                    raw['activity_type'], raw['activity_units'])].append((raw['np_id'], key))
            if channel == 'plant_phenotype_candidate' and compound.get('identity_status') == 'valid':
                activity_keys.add(key)
    registry_rows = []
    for group, rows in sorted(groups.items()):
        registry_rows.append(dict(zip(['evidence_channel', 'source_target_id', 'citation',
                                      'endpoint', 'reported_unit'], group, strict = True)) | {
            'observations': len(rows), 'source_compounds': len({r[0] for r in rows}),
            'full_structures': len({r[1] for r in rows if r[1]}),
            'high_labels': 0, 'low_labels': 0, 'review_status': 'review_only'})
    write_csv(output / 'npass_plant_assay_registry.csv', registry_rows,
              ['evidence_channel', 'source_target_id', 'citation', 'endpoint', 'reported_unit',
               'observations', 'source_compounds', 'full_structures', 'high_labels', 'low_labels',
               'review_status'])
    summary = {'inputs': before, 'acquired_occurrence_rows': acquired_occurrences,
               'cohort_occurrence_rows': occurrences, 'occurrence_tiers': dict(tiers),
               'cohort_taxon_publication_linked_full_keys': len(occurrence_keys),
               'acquired_activity_rows': acquired_activities, 'plant_channels': dict(channels),
               'phenotype_candidate_full_keys': len(activity_keys),
               'new_adopted_activity_labels': 0, 'verified_occurrence_labels_added': 0,
               'limits': 'Taxon/reference links are database assertions, not primary verified '
                         'occurrence. Organism targets do not specify assay phenotype. NPASS '
                         'activity values are endpoint scalars, not necessarily tested doses. '
                         'Plant taxonomy is bounded by the species export, includes green algae, '
                         'and excludes missing taxonomy sentinels from all joins.'}
    if production_paths:
        summary['production_context'] = production_counts
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during context extraction')
    reproduction = output / 'reproduction'
    reproduction.mkdir()
    for p in [Path(__file__), Path(__file__).with_name('sprint_natural.py'),
              Path(__file__).with_name('data_sprint.py')]:
        shutil.copyfile(p, reproduction / p.name)
    summary['products'] = {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('registry', 'npass', 'baseline', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    parser.add_argument('--production', type=Path, help='Directory with the four NPASS TSVs')
    args = parser.parse_args()
    print(json.dumps(run(args.registry, args.npass, args.baseline, args.output, args.production),
                     indent = 2))
