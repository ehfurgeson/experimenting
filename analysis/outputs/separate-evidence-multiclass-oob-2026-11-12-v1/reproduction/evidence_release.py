"""Offline, source-first A/B release; never changes an accepted evidence bundle."""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from xml.etree import ElementTree as ET

import polars as pl
from agrotox.epa_test import parse_test_predictions
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

from collect_evidence_sources import PUBLIC_SOURCES

RDLogger.DisableLog('rdApp.error')
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
FEATURES = ['molecular_weight', 'tpsa', 'hbd', 'hba', 'rotatable_bonds', 'rings', 'fraction_sp3']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows, fields = None):
    rows = list(rows)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = fields)
        writer.writeheader()
        writer.writerows(rows)


def workbook_rows(path, sheet):
    """Read source cells without evaluating formulas; reject duplicate/blank headers."""
    with zipfile.ZipFile(path) as archive:
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']: r.attrib['Target'] for r in rels}
        names = {s.attrib['name']: s.attrib[
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
            for s in book.find('m:sheets', NS)}
        target = targets[names[sheet]]
        member = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            root = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [''.join(e.itertext()) for e in root.findall('m:si', NS)]
        header = None
        with archive.open(member) as stream:
            for _, row in ET.iterparse(stream, events = ('end',)):
                if row.tag != '{' + NS['m'] + '}row':
                    continue
                cells = {}
                for cell in row.findall('m:c', NS):
                    if cell.find('m:f', NS) is not None:
                        raise ValueError('Source formulas require separate review')
                    col = re.match(r'[A-Z]+', cell.attrib['r'])[0]
                    index = 0
                    for char in col:
                        index = index * 26 + ord(char) - 64
                    value = cell.find('m:v', NS)
                    value = value.text if value is not None else None
                    if cell.attrib.get('t') == 's' and value is not None:
                        value = strings[int(value)]
                    elif cell.attrib.get('t') == 'inlineStr':
                        value = ''.join(cell.find('m:is', NS).itertext())
                    cells[index - 1] = value
                if header is None:
                    header = [cells.get(i) for i in range(max(cells, default = -1) + 1)]
                    if not header or None in header or len(set(header)) != len(header):
                        raise ValueError('Unique populated headers required')
                else:
                    if cells and max(cells) >= len(header):
                        raise ValueError('Source cell exceeds header width')
                    yield int(row.attrib['r']), {h: cells.get(i) for i, h in enumerate(header)}
                row.clear()


def sdf_properties(archive, member = 'CATMoS_QR50k.sdf'):
    """Stream all SDF properties, retaining blanks and rejecting truncated records."""
    with zipfile.ZipFile(archive) as z, z.open(member) as raw:
        props, field, values, ordinal = {}, None, [], 0
        for line in io.TextIOWrapper(raw, encoding = 'utf-8'):
            line = line.rstrip('\r\n')
            match = re.match(r'>\s*<([^>]+)>', line)
            if match or line == '$$$$':
                if field is not None:
                    props[field] = '\n'.join(values).strip()
                field, values = (match[1], []) if match else (None, [])
                if line == '$$$$':
                    ordinal += 1
                    yield ordinal, props
                    props = {}
            elif field is not None:
                values.append(line)
        if props or field is not None:
            raise ValueError('Truncated SDF record')


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def structure(smiles):
    mol = Chem.MolFromSmiles(smiles or '')
    if mol is None or not mol.GetNumAtoms():
        return {'identity_status': 'invalid_or_missing_structure'}
    key = Chem.MolToInchiKey(mol)
    if not key:
        return {'identity_status': 'no_full_key'}
    return {
        'full_key': key, 'connectivity': key.split('-')[0],
        'smiles': Chem.MolToSmiles(mol, isomericSmiles = True),
        'identity_status': 'multiple_components' if len(Chem.GetMolFrags(mol)) != 1 else 'valid',
        'scaffold': MurckoScaffold.MurckoScaffoldSmiles(mol = mol) or 'ACYCLIC',
        'molecular_weight': Descriptors.MolWt(mol), 'tpsa': rdMolDescriptors.CalcTPSA(mol),
        'hbd': Lipinski.NumHDonors(mol), 'hba': Lipinski.NumHAcceptors(mol),
        'rotatable_bonds': Lipinski.NumRotatableBonds(mol), 'rings': Lipinski.RingCount(mol),
        'fraction_sp3': rdMolDescriptors.CalcFractionCSP3(mol),
    }


def ice_observation(raw, locator, identity):
    value = number(raw.get('Response'))
    qualifier = raw.get('Response_Modifier') or '='
    reasons = []
    for okay, reason in [
        (raw.get('Data_Type') == 'In Vivo', 'not_explicit_in_vivo'),
        (raw.get('Species') == 'Rat', 'not_explicit_rat'),
        (raw.get('Assay') == 'Rat Acute Oral Toxicity', 'not_acute_oral'),
        (raw.get('Mixture') == 'Chemical', 'mixture_or_unknown'),
        (raw.get('Endpoint') == 'LD50', 'not_ld50'),
        (raw.get('Response_Unit') == 'mg/kg', 'not_mg_kg'),
        (value is not None and value > 0, 'missing_nonpositive_or_nonfinite'),
        (bool(raw.get('Reference')), 'missing_reference'),
        (identity['identity_status'] == 'valid', identity['identity_status']),
        (qualifier in {'=', '<', '>', '<=', '>='}, 'unknown_qualifier'),
    ]:
        if not okay:
            reasons.append(reason)
    status = 'excluded' if reasons else 'exact' if qualifier == '=' else 'censored'
    return {'source': 'NIH_ICE_4.1', 'source_record_id': raw.get('Record_ID'),
            'source_locator': f'Data!row{locator}', 'full_key': identity.get('full_key'),
            'dtxsid': raw.get('DTXSID'), 'value_mg_kg': value, 'qualifier': qualifier,
            'reference': raw.get('Reference'), 'sex': raw.get('Sex'),
            'status': status, 'reasons': ';'.join(reasons), 'evidence_class':
            {'In Vivo': 'experimental', 'In Vitro': 'experimental',
             'In Silico': 'predicted'}.get(raw.get('Data_Type'), 'unknown'),
            'source_record_json': json.dumps(raw, sort_keys = True)}


def catmos_prediction(raw, locator, identity):
    value = number(raw.get('CATMoS_LD50_pred'))
    domain = {'1': 'Inside', '0': 'Outside'}.get(raw.get('AD_CATMoS'), 'unknown')
    reasons = []
    if value is None:
        reasons.append('missing_or_nonfinite_prediction')
    if identity['identity_status'] != 'valid':
        reasons.append(identity['identity_status'])
    if raw.get('InChI Key_QSARr') and raw['InChI Key_QSARr'] != identity.get('full_key'):
        reasons.append('provider_full_key_mismatch')
    if domain != 'Inside':
        reasons.append('not_inside_domain')
    # The source documents Log mg/kg. Do not interpret this as -log mol/kg.
    return {'source': 'OPERA_CATMoS_bulk', 'source_record_id': raw.get('ChemID'),
            'source_locator': f'OPERA_Data.zip:CATMoS_QR50k.sdf:record{locator}',
            'dtxsid': raw.get('DTXSID'), 'full_key': identity.get('full_key'),
            'source_qsar_key': raw.get('InChI Key_QSARr'),
            'original_smiles': raw.get('Original_SMILES'),
            'queried_qsar_smiles': raw.get('Canonical_QSARr'),
            'model': 'CATMoS_LD50_pred', 'unit': 'log10(mg/kg)',
            'value_log10_mg_kg': value, 'ad_conclusion': domain,
            'ad_index': raw.get('AD_index_CATMoS'), 'confidence': raw.get('Conf_index_CATMoS'),
            'training_membership': raw.get('CATMoS_Tr_Tst') or 'unknown',
            'embedded_experimental_mg_kg': raw.get('CATMoS_LD50_mgkg'),
            'consortium_consensus_log10_mg_kg': raw.get('consensus_LD50'),
            'status': 'excluded' if reasons else 'eligible', 'reasons': ';'.join(reasons),
            'evidence_class': 'predicted', 'source_record_json': json.dumps(raw, sort_keys = True)}


def ld50_bin(log_value):
    return 0 if log_value <= math.log10(1080) else 1 if log_value <= math.log10(3400) else 2


def freeze(sources, data, output):
    sources, data, output = map(Path, (sources, data, output))
    if output.exists():
        raise FileExistsError('Choose a new versioned release directory')
    for input_dir in (sources, data):
        if output.resolve().is_relative_to(input_dir.resolve()):
            raise ValueError('Release must be separate from raw inputs')
    output.mkdir(parents = True)
    identities, memo = {}, {}

    def identify(smiles, cohort, native_id):
        if smiles not in memo:
            memo[smiles] = structure(smiles)
        identity = memo[smiles]
        key = (cohort, native_id)
        identities[key] = {'source_cohort': cohort, 'native_id': native_id,
                           'source_smiles': smiles, **identity}
        return identity

    inputs = [sources / 'ice-acute-oral.xlsx', sources / 'OPERA_Data.zip',
              sources / 'zenodo-ld50.xlsx', sources / 'collection-http.json',
              sources / 'opera-readme.md', sources / 'opera-tree.json',
              data / 'epa_identity_crosswalk.parquet', data / 'compound_traits.parquet']
    inputs.extend(data.joinpath('raw/comptox/chemical/property/predicted').glob('*.json'))
    a = []
    for locator, raw in workbook_rows(inputs[0], 'Data'):
        ident = identify(raw.get('SMILES'), 'ICE', raw['Record_ID'])
        a.append(ice_observation(raw, locator, ident))
    b = []
    for locator, raw in sdf_properties(inputs[1]):
        ident = identify(raw.get('Canonical_QSARr'), 'CATMoS', raw['ChemID'])
        b.append(catmos_prediction(raw, locator, ident))
    # This author-curated aggregation shares TEST/NICEATM/Toolbox lineage.
    # pLD50 scale and primary-study/form reconciliation remain unverified.
    zenodo = [{'source_locator': f'default!row{loc}', 'status': 'held_for_scale_lineage_review',
               'source_record_json': json.dumps(raw, sort_keys = True)}
              for loc, raw in workbook_rows(inputs[2], 'default')]
    http_log = json.loads((sources / 'collection-http.json').read_text())
    byfile = {r['file']: r for r in http_log}
    source_inventory = []
    for name, url, provider, evidence, lineage in PUBLIC_SOURCES:
        path = sources / name
        source_inventory.append({
            'provider': provider, 'product_file': name, 'official_url': url,
            'evidence_scope': evidence, 'lineage': lineage,
            'method': 'public_HTTP_bulk_or_documentation',
            'retrieved_at': byfile.get(name, {}).get('retrieved_at'),
            'http_status': byfile.get(name, {}).get('status'),
            'raw_sha256': sha(path) if path.exists() else None,
            'state': 'acquired' if path.exists() else 'not_acquired',
            'rights': 'local research copy; redistribution rights not adjudicated',
        })
        if path.exists() and path not in inputs:
            inputs.append(path)
    write_csv(output / 'sources.csv', source_inventory)
    write_csv(output / 'A_observations.csv', a)
    write_csv(output / 'B_predictions.csv', b)
    write_csv(output / 'held_zenodo_aggregation.csv', zenodo)
    seen, values, support = set(), defaultdict(list), defaultdict(list)
    for r in a:
        if r['status'] != 'exact':
            continue
        sig = (r['full_key'], r['reference'], r['sex'], r['value_mg_kg'])
        if sig not in seen:
            values[r['full_key']].append(r['value_mg_kg'])
            seen.add(sig)
        support[r['full_key']].append(r['source_record_id'])
    bykey = {r['full_key']: r for r in identities.values() if r.get('full_key')}
    ac = [{**{k: bykey[key][k] for k in ['full_key', 'connectivity', 'smiles', 'scaffold',
                                       *FEATURES]},
           'target_log10_mg_kg': math.log10(median(vals)),
           'ld50_bin': ld50_bin(math.log10(median(vals))), 'deduplicated_values': len(vals),
           'source_record_ids': json.dumps(support[key]), 'source_cohort': 'ICE'}
          for key, vals in sorted(values.items())]
    bkeys = defaultdict(list)
    for r in b:
        if r['status'] == 'eligible':
            bkeys[r['full_key']].append(r)
    bc = []
    for key, rs in sorted(bkeys.items()):
        # Conflicting provider outputs must not be silently averaged.
        vals = {r['value_log10_mg_kg'] for r in rs}
        if len(vals) != 1:
            continue
        value = next(iter(vals))
        bc.append({**{k: bykey[key][k] for k in ['full_key', 'connectivity', 'smiles',
                                               'scaffold', *FEATURES]},
                   'target_log10_mg_kg': value, 'ld50_bin': ld50_bin(value),
                   'source_record_ids': json.dumps([r['source_record_id'] for r in rs]),
                   'training_membership': ';'.join(sorted({r['training_membership'] for r in rs})),
                   'ad_conclusion': 'Inside', 'source_cohort': 'OPERA_CATMoS_bulk'})
    write_csv(output / 'A_compounds.csv', ac)
    write_csv(output / 'B_compounds.csv', bc)
    write_csv(output / 'chemical_identity.csv', identities.values())
    write_csv(output / 'excluded_records.csv', [
        {'pathway': pathway, 'source_record_id': r['source_record_id'],
         'status': r['status'], 'reasons': r['reasons']}
        for pathway, rows in [('A', a), ('B', b)] for r in rows
        if r['status'] not in {'exact', 'eligible'}])
    write_csv(output / 'B_duplicate_resolution.csv', [
        {'full_key': k, 'records': len(rs), 'distinct_predictions':
         len({r['value_log10_mg_kg'] for r in rs}), 'status':
         'conflict_excluded' if len({r['value_log10_mg_kg'] for r in rs}) > 1 else 'collapsed'}
        for k, rs in bkeys.items() if len(rs) > 1],
        ['full_key', 'records', 'distinct_predictions', 'status'])
    # Inventory original selection and all cached provider/model families.
    traits = pl.read_parquet(data / 'compound_traits.parquet').to_dicts()
    crosswalk = pl.read_parquet(data / 'epa_identity_crosswalk.parquet').to_dicts()
    test, props, collection = [], [], []
    for r in crosswalk:
        native = r['dtxsid']
        cache = data / f'raw/comptox/chemical/property/predicted/{native}.json'
        state = 'identity_' + r['status']
        n = 0
        if r['status'] == 'approved':
            if cache.exists():
                envelope = json.loads(cache.read_text())
                if envelope['dtxsid'] != native or not isinstance(envelope['response'], list):
                    raise ValueError('Invalid EPA cache envelope')
                records = envelope['response']
                if any(x.get('dtxsid') != native for x in records):
                    raise ValueError('EPA cached record identity mismatch')
                parsed = parse_test_predictions(records, r['compound_id'], envelope['retrieved_at'])
                test.extend({**x, 'raw_file': str(cache), 'raw_sha256': sha(cache)} for x in parsed)
                props.extend({'compound_id': r['compound_id'], 'dtxsid': native,
                              'model': x.get('modelName'), 'source_name': x.get('sourceName'),
                              'endpoint': x.get('propName'), 'value': x.get('propValue'),
                              'unit': x.get('propUnit'), 'ad_conclusion': x.get('adConclusion'),
                              'evidence_class': 'predicted', 'raw_file': str(cache),
                              'source_record_json': json.dumps(x, sort_keys = True)} for x in records)
                n = len(parsed)
                state = 'stored_output' if n else 'no_stored_output'
            else:
                state = 'missing_cache_not_queried'
        collection.append({'compound_id': r['compound_id'], 'dtxsid': native,
                           'source': 'CTX_TEST', 'state': state, 'test_records': n})
    write_csv(output / 'B_TEST_cache.csv', test)
    write_csv(output / 'B_all_cached_properties.csv', props)
    write_csv(output / 'collection_log.csv', collection)
    native_keys = set()
    for r in traits:
        ident = structure(r.get('canonical_smiles'))
        if ident.get('full_key'):
            native_keys.add(ident['full_key'])
    counts = {'A': dict(Counter(r['status'] for r in a)),
              'B': dict(Counter(r['status'] for r in b)),
              'A_compounds': len(ac), 'B_compounds': len(bc),
              'A_structures_beyond_selection': len({r['full_key'] for r in ac} - native_keys),
              'B_structures_beyond_selection': len({r['full_key'] for r in bc} - native_keys),
              'B_domains': dict(Counter(r['ad_conclusion'] for r in b)),
              'B_training_membership': dict(Counter(r['training_membership'] for r in b)),
              'selection_TEST_states': dict(Counter(r['state'] for r in collection)),
              'TEST_records': len(test), 'TEST_compounds': len({r['compound_id'] for r in test}),
              'TEST_versions': dict(Counter(r['source_name'] for r in test)),
              'cached_property_versions': dict(Counter(r['source_name'] for r in props)),
              'held_zenodo_rows': len(zenodo),
              'independent_measured_study_count': None}
    endpoint_counts = Counter((r['endpoint'], r['source_name'], r['predicted_unit'],
                               r['ad_conclusion'], number(r['predicted_value']) is not None)
                              for r in test)
    write_csv(output / 'TEST_endpoint_audit.csv', [
        dict(zip(['endpoint', 'source_name', 'unit', 'ad_conclusion', 'finite', 'records'],
                 [*key, count])) for key, count in sorted(endpoint_counts.items())])
    write_csv(output / 'lineage_links.csv', [
        {'left': 'ICE', 'right': 'TEST', 'relationship': 'shared_ChemIDplus_TEST_reference',
         'independence': 'not_established'},
        {'left': 'CATMoS', 'right': 'ICE', 'relationship': 'shared_NICEATM_acute_oral_compilation',
         'independence': 'not_established'},
        {'left': 'Zenodo3300664', 'right': 'ICE/TEST/Toolbox',
         'relationship': 'source_database_concatenation_in_workbook',
         'independence': 'not_established'},
        {'left': 'OPERA_consensus_LD50', 'right': 'OPERA_CATMoS_LD50_pred',
         'relationship': 'related_fields_not_independent_models', 'independence': 'no'}])
    (output / 'coverage.json').write_text(json.dumps(counts, indent = 2) + '\n')
    code_files = [Path(__file__), Path(__file__).parent / 'collect_evidence_sources.py',
                  Path('pipeline/src/agrotox/epa_test.py'), Path('pipeline/src/agrotox/tables.py'),
                  Path(__file__).parent / 'docs/modeled-evidence.md',
                  Path('analysis/uv.lock'), Path('pipeline/uv.lock')]
    (output / 'reproduction').mkdir()
    for path in code_files:
        destination = output / 'reproduction' / str(path).replace('/', '__')
        shutil.copyfile(path, destination)
    manifest = {'status': 'AI_experimental_frozen_separate_A_B', 'counts': counts,
                'protocol_sha256': sha(Path(__file__).parent / 'docs/modeled-evidence.md'),
                'inputs': {str(p): sha(p) for p in sorted(inputs)},
                'code': {str(p): sha(p) for p in [Path(__file__),
                         Path(__file__).parent / 'collect_evidence_sources.py',
                         Path('pipeline/src/agrotox/epa_test.py'),
                         Path('pipeline/src/agrotox/tables.py')]},
                'locks': {str(p): sha(p) for p in [Path('analysis/uv.lock'),
                                                   Path('pipeline/uv.lock')]},
                'outputs': {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                            if p.is_file()},
                'limits': 'Provisional source identities and study context; no human admissions; '
                          'teacher training overlap unknown; no measured-property feature cohort.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--sources', type = Path, required = True)
    parser.add_argument('--data', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.sources, args.data, args.output), indent = 2))
