"""Offline targeted ChEMBL phenotype review, preserving source-form and dose holds."""

import argparse
import json
import math
import shutil
from collections import Counter
from pathlib import Path

from rdkit import Chem

from data_sprint import sha256, write_csv
from sprint_natural import identity

PODOLACTONE_DOI = '10.1021/jf990321y'


def source_bound(activity):
    """Describe source bounds only; this function never creates a training label."""
    if activity.get('standard_units') != '%' or activity.get('standard_type') != 'Inhibition':
        return 'not_compatible_inhibition_bound'
    try:
        value = float(activity['standard_value'])
    except (TypeError, ValueError):
        return 'unknown'
    if not math.isfinite(value):
        return 'unknown'
    relation = activity.get('standard_relation')
    if relation == '>' and value >= 40:
        return 'reported_inhibition_over_40_percent'
    if relation == '<' and 0 <= value <= 20:
        return 'reported_inhibition_under_20_percent'
    return 'other_reported_response'


def holds(activity, doi):
    reasons = ['independent_primary_review_pending', 'source_sample_stereochemistry_pending']
    if doi == PODOLACTONE_DOI:
        reasons += ['qualitative_summary_not_resolved_to_single_dose',
                    'primary_pdf_bytes_and_visual_verification_unavailable']
        if activity['molecule_chembl_id'] == 'CHEMBL1896787':
            reasons.append('Logran_formulated_control_not_single_ingredient')
    else:
        reasons.append('original_protocol_control_and_response_direction_review_pending')
    return reasons


def run(snapshots, output):
    snapshots, output = Path(snapshots), Path(output)
    registry = json.loads((snapshots / 'sources.json').read_text())
    inputs = [snapshots / 'sources.json', snapshots / 'podolactone-molecules.json',
              snapshots / 'podolactone-molecules-source.json']
    molecule_metadata = json.loads(inputs[-1].read_text())
    if molecule_metadata['http_status'] != 200 or sha256(inputs[1]) != molecule_metadata['sha256']:
        raise ValueError('Unverified molecule snapshot')
    molecule_data = json.loads(inputs[1].read_text())
    molecules = {r['molecule_chembl_id']: r for r in molecule_data['molecules']}
    if (set(molecules) != set(molecule_metadata['requested_ids']) or
            molecule_data['page_meta']['next'] is not None):
        raise ValueError('Incomplete molecule identity request')
    observations, assays = [], []
    for entry in registry:
        if entry['status'] != 'complete':
            continue
        path = snapshots / entry['file']
        if sha256(path) != entry['sha256']:
            raise ValueError('Assay snapshot hash mismatch')
        inputs.append(path)
        m = json.loads(path.read_text())
        activities = [r for page in m['activity_pages'] for r in page['activities']]
        if len(activities) != m['activity_count'] or len({r['activity_id'] for r in activities}) != len(activities):
            raise ValueError('Assay count/uniqueness mismatch')
        doi = m['document'].get('doi') or ''
        counts = Counter()
        for raw in activities:
            molecule = molecules.get(raw['molecule_chembl_id'], {}).get('molecule_structures') or {}
            smiles = raw.get('canonical_smiles') or ''
            provider_key = molecule.get('standard_inchi_key', '')
            derived = identity(smiles, provider_key)
            if derived['identity_status'] == 'missing_provider_key':
                derived['identity_status'] = 'derived_key_not_provider_verified'
            reasons = holds(raw, doi)
            if derived['identity_status'] != 'valid':
                reasons.append(derived['identity_status'])
            band = source_bound(raw)
            counts[band] += 1
            observations.append({
                'source': 'ChEMBL', 'source_version': m['status']['chembl_db_version'],
                'source_assay_id': raw['assay_chembl_id'], 'source_record_id': raw['activity_id'],
                'source_compound_id': raw['molecule_chembl_id'],
                'compound_name': raw.get('molecule_pref_name'), 'doi': doi,
                'plant_species': m['assay'].get('assay_organism'),
                'full_inchikey': derived['full_inchikey'], 'original_structure': smiles,
                'identity_status': derived['identity_status'],
                'endpoint': raw.get('standard_type'), 'observed_response': raw.get('standard_value'),
                'response_unit': raw.get('standard_units'), 'qualifier': raw.get('standard_relation'),
                'source_response_band': band, 'assay_description': m['assay']['description'],
                'dose_context': 'retained in source description; primary mapping not assumed',
                'activity_label': 'unknown', 'review_status': 'review_only',
                'hold_reasons': ';'.join(reasons), 'source_locator': str(path),
                'source_record_json': json.dumps(raw, sort_keys = True)})
        assays.append({'source_assay_id': entry['assay_id'], 'doi': doi,
                       'description': m['assay']['description'], 'observations': len(activities),
                       'source_compounds': len({r['molecule_chembl_id'] for r in activities}),
                       'reported_over40_bounds': counts['reported_inhibition_over_40_percent'],
                       'reported_under20_bounds': counts['reported_inhibition_under_20_percent'],
                       'adopted_high': 0, 'adopted_low': 0, 'review_status': 'review_only'})
    before = {str(p): sha256(p) for p in inputs}
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'plant_activity_observations.csv', observations, list(observations[0]))
    write_csv(output / 'plant_assay_registry.csv', assays, list(assays[0]))
    for r in observations:
        mol = Chem.MolFromSmiles(r['original_structure'])
        if mol and r['full_inchikey'] != Chem.MolToInchiKey(mol):
            raise ValueError('Output identity disagreement')
    summary = {'inputs': before, 'complete_assays': len(assays),
               'activity_observations': len(observations),
               'source_publications': len({r['doi'] for r in observations}),
               'source_compounds': len({r['source_compound_id'] for r in observations}),
               'identity_status': dict(Counter(r['identity_status'] for r in observations)),
               'new_adopted_labels': 0, 'models_fitted': 0,
               'primary_review': {
                   'url': 'https://bibrepo.uca.es/articuloscientificos/31850200.pdf',
                   'doi': PODOLACTONE_DOI, 'mode': 'web_parsed_text_AI_review',
                   'pdf_download_attempts': 'two HTTP 403; preserved error bodies',
                   'visual_review': 'web screenshot cache miss; unavailable',
                   'control_locator': 'p.3005, Comparison with the Commercial Herbicide Logran',
                   'summary_locator': 'p.3006, Table 1 and footnote; no single-dose table heading',
                   'methods_locator': 'p.3003, Bioassays: buffered Petri dishes, 25 C dark, '
                                      '5 days for lettuce, parallel controls, 100 seeds per condition'},
               'limits': 'Complete ChEMBL assay snapshots do not resolve tested-product form '
                         'or transform an across-dose qualitative table into fixed-dose data. '
                         'Source bounds are descriptions, not independently adopted activity labels.'}
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during phenotype review')
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
    parser.add_argument('--snapshots', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.snapshots, args.output), indent = 2))
