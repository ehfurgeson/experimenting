"""Cross-reference plant response leads with provisional rat acute oral evidence."""

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from rdkit import Chem

from accepted_plant import ecotox_basis, ecotox_response, finite
from accepted_sprint import rows
from catalog_hazard_review import ld50_support
from data_sprint import read_csv, sha256
from evidence_release import ld50_bin, write_csv
from research_followup import GENERATOR, analogue_queue, evidence_band
from sprint_report import compressed_rows, verify_bundle
from sprint_toxval import identifier_crosswalk


def point_response(row, result):
    """Require a point exposure and reported response scale before assigning a band."""
    if (row['endpoint'] != 'NR' or row['qualifier'] not in {'', '='}
            or result.get('conc1_mean_op', '') not in {'', '='}):
        return None
    dose = finite(row['concentration'])
    if (dose is None or dose <= 0 or row['concentration_unit'] in {'', 'NR', '-'}
            or row['control_context'] in {'', 'NR', '-'}):
        return None
    basis = ecotox_basis(result)
    inhibition, label = ecotox_response({
        **row, 'response_basis': basis,
        'effect_pct_comments': result.get('effect_pct_comments', ''),
        'additional_comments': result.get('additional_comments', ''),
    })
    if label is None:
        return None
    return basis, inhibition, label


def structure_profile(group, rows):
    halogen_counts = Counter()
    for row in rows:
        elements = {atom.GetSymbol() for atom in Chem.MolFromSmiles(row['smiles']).GetAtoms()}
        halogen_counts.update(elements & {'F', 'Cl', 'Br', 'I'})
        halogen_counts['any'] += bool(elements & {'F', 'Cl', 'Br', 'I'})
    return {'group': group, 'structures': len(rows),
            **{f'with_{element}': halogen_counts[element]
               for element in ('F', 'Cl', 'Br', 'I', 'any')},
            'median_molecular_weight': median(float(r['molecular_weight']) for r in rows),
            'median_tpsa': median(float(r['tpsa']) for r in rows)}


def high_ld50_support(keys, observations):
    by_key = defaultdict(list)
    for row in observations:
        if row['full_key'] in keys and row['status'] in {'exact', 'censored'}:
            by_key[row['full_key']].append(row)
    return {key: ld50_support(by_key[key]) for key in sorted(keys)}


def ranked_analogues(queries, pool, support):
    fingerprints = [GENERATOR.GetFingerprint(Chem.MolFromSmiles(row['smiles'])) for row in pool]
    analogues = analogue_queue(queries, pool, fingerprints)
    for row in analogues:
        row['provisional_ice_mg_kg'] = row.pop('accepted_ld50_mg_kg')
        row['evidence'] = 'catalog membership and provisional ICE dose'
        row.update(support[row['analogue_full_key']])
    return analogues


def run(root, panel, output, coconut=None, toxval_extra=None):
    root, panel, output = map(Path, (root, panel, output))
    public = root / 'public-cohorts'
    sources = {name: root / name for name in ('coconut', 'npass', 'ecotox', 'toxval')}
    if coconut is not None:
        sources['coconut'] = Path(coconut)
    if toxval_extra is not None:
        sources['toxval-extra'] = Path(toxval_extra)
    sources['npass-context'] = root / 'npass-context-v2'
    manifests = [public / 'manifest.json', panel / 'manifest.json']
    verify_bundle(public)
    verify_bundle(panel)
    for path in sources.values():
        verify_bundle(path)
        manifests.append(path / 'manifest.json')
    a = {row['full_key']: row for row in read_csv(public / 'A_compounds.csv')}
    b = {row['full_key']: row for row in read_csv(public / 'B_compounds.csv')}
    matches = {
        name: {row['full_inchikey'] for row in read_csv(sources[name] / f'{name}_overlap.csv')
               if row['match_tier'] == 'exact_full_key'}
        for name in ('coconut', 'npass')
    }
    catalog = matches['coconut'] | matches['npass']
    occurrence_keys = {
        row['full_inchikey'] for row in compressed_rows(
            sources['npass-context'] / 'npass_occurrences.csv.gz')
        if row['occurrence_evidence_type'] == 'taxon_and_publication_linked_unreviewed'
    }
    mappings = identifier_crosswalk(public)
    plant, labels = [], defaultdict(set)
    for row in compressed_rows(sources['ecotox'] / 'plant_activity_observations.csv.gz'):
        keys = mappings.get(row['dtxsid'], set())
        if len(keys) != 1:
            continue
        key, = keys
        if key not in a and key not in b:
            continue
        raw = json.loads(row['source_record_json'])
        point = point_response(row, raw['result'])
        if point is None:
            continue
        basis, inhibition, label = point
        labels[key].add(label)
        plant.append({**row, 'full_inchikey': key,
                      'identity_status': 'unambiguous_source_DTXSID_review_lead',
                      'response_basis': basis, 'signed_inhibition_percent': inhibition,
                      'provisional_context_band': 'high' if label else 'low'})
    panel_rows = read_csv(panel / 'panel.csv')
    herbicides = {r['full_key'] for r in panel_rows if r['panel'] == 'HRAC_2026' and r['full_key']}
    reviewed_herbicides = {r['full_key'] for r in panel_rows
                          if r['panel'] == 'reviewed_selection_herbicide' and r['full_key']}
    herbicide_keys = herbicides | reviewed_herbicides
    primary = {r['full_key']: r['compound_name'] for r in panel_rows
               if r['panel'] == 'Annona_reticulata' and r['full_key']}
    measured = []
    for key, item in a.items():
        measured.append({
            **item, 'ice_mg_kg': 10 ** float(item['target_log10_mg_kg']),
            'coconut_exact': key in matches['coconut'], 'npass_exact': key in matches['npass'],
            'npass_taxon_reference_lead': key in occurrence_keys, 'hrac_name_lead': key in herbicides,
            'reviewed_herbicide_selection': key in reviewed_herbicides,
            'plant_trial_band': (evidence_band(labels[key]) if labels.get(key)
                                 else 'no_qualified_point_response'),
            'primary_annona_assay': primary.get(key, ''),
        })
    groups = defaultdict(list)
    for row in measured:
        key = row['full_key']
        if key in herbicides:
            groups['HRAC_name_link'].append(row)
        if key in reviewed_herbicides:
            groups['reviewed_herbicide_selection'].append(row)
        if key in catalog:
            groups['catalog_exact_ICE'].append(row)
        if key in occurrence_keys and key not in herbicide_keys:
            groups['NPASS_taxon_reference_' + row['plant_trial_band']].append(row)
    totals = Counter((group, row['ld50_bin']) for group, members in groups.items() for row in members)
    for key in catalog & b.keys():
        totals['catalog_exact_CATMoS_teacher', b[key]['ld50_bin']] += 1
    epa, epa_bins = [], defaultdict(set)
    for source in (path for name, path in sources.items() if name.startswith('toxval')):
        for row in rows(source / 'toxval_candidate_rat_oral.csv.gz'):
            key = row['full_inchikey']
            if key in catalog and key not in a and row['status'] == 'endpoint_eligible_exact':
                epa.append(row)
                epa_bins[key].add(ld50_bin(math.log10(float(row['value']))))
    pool = [row for row in measured if row['full_key'] in catalog
            and row['full_key'] not in herbicide_keys and row['ld50_bin'] == '2']
    queries = [{'compound_id': name, 'original_structure': a.get(key, b.get(key, {})).get('smiles'),
                'full_inchikey': key} for key, name in primary.items() if key in a or key in b]
    queries += [{'compound_id': r['source_locator'] if r['panel'].startswith('reviewed_selection')
                 else r['compound_name'], 'original_structure': r['canonical_smiles'],
                 'full_inchikey': r['full_key']}
                for r in panel_rows if r.get('canonical_smiles') and
                (r['panel'] in {'Annona_reticulata', 'reviewed_selection_natural_product'}
                 or r.get('source_kind') == 'plant_literature')]
    queries = list({(r['compound_id'], r['full_inchikey']): r for r in queries}.values())
    support = high_ld50_support({r['full_key'] for r in pool},
                                read_csv(public / 'A_observations.csv'))
    all_exact_high_pool = [r for r in pool if support[r['full_key']]['exact_report_bins'] == 'high']
    analogues = ranked_analogues(queries, pool, support)
    exact_high_analogues = ranked_analogues(queries, all_exact_high_pool, support)
    output.mkdir(parents=True, exist_ok=False)
    products = {
        'measured_context': measured, 'plant_response_leads': plant,
        'catalog_new_epa_exact_leads': epa, 'primary_plant_analogues': analogues,
        'primary_plant_analogues_all_exact_high': exact_high_analogues,
        'analogue_pool_ld50_support': [{'full_key': key, **value} for key, value in support.items()],
        'group_structure_profiles': [structure_profile(group, members)
                                     for group, members in sorted(groups.items())],
        'group_ld50_bins': [{'group': group, 'bin': int(bucket), 'structures': count}
                            for (group, bucket), count in sorted(totals.items())],
    }
    for name, records in products.items():
        if records:
            write_csv(output / f'{name}.csv', records)
    summary = {
        'inputs': {str(path): sha256(path) for path in manifests},
        'products': {path.name: sha256(path) for path in output.iterdir()},
        'output_row_counts': {name: len(rows) for name, rows in products.items()},
        'epa_held_structures': len({r['full_inchikey'] for r in epa}),
        'epa_held_exact_bands': dict(Counter(
            str(next(iter(bands))) if len(bands) == 1 else 'conflict'
            for bands in epa_bins.values())),
        'plant_point_structures': len(labels),
        'analogue_pool_structures': {'median_high': len(pool),
                                     'all_exact_reports_high': len(all_exact_high_pool)},
        'limits': 'Catalog and DTXSID links are review leads. Rat LD50 is one hazard endpoint.',
    }
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'panel', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--coconut', type=Path)
    parser.add_argument('--toxval-extra', type=Path)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
