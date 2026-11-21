"""Collect stored TEST outputs for a structure-reviewed feature inventory."""
import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import requests
from agrotox.epa_identity import resolve_identities
from agrotox.epa_test import fetch_test_predictions, prediction_table
from agrotox.sources.comptox import ComptoxClient

from evidence_release import sha, structure, write_csv


def expand(features, output, client = None):
    features, output = Path(features), Path(output)
    client = client if client is not None else ComptoxClient()
    if isinstance(client, ComptoxClient) and not client.api_key:
        raise ValueError('Configure COMPTOX_API_KEY before acquisition')
    if output.exists():
        raise FileExistsError('Choose a new acquisition directory')
    rows = pl.read_parquet(features).to_dicts()
    required = {'compound_id', 'query', 'canonical_structure', 'structure_inchikey'}
    if any(not required.issubset(r) for r in rows):
        raise ValueError('Input requires reviewed structure feature columns')
    output.mkdir(parents = True)
    ledger, candidates, crosswalk, predictions = [], [], [], []
    for r in rows:
        cid = r['compound_id'].upper()
        item = {'compound_id': cid, 'query': r['query'], 'source_cohort': 'dietary_inventory',
                'retrieved_at': datetime.now(UTC).isoformat()}
        identity = structure(r['canonical_structure'])
        if identity.get('full_key') != r['structure_inchikey'] or identity['identity_status'] != 'valid':
            ledger.append({**item, 'state': 'input_identity_not_verified'})
            continue
        compound = pl.DataFrame([{
            'compound_id': cid, 'pubchem_cid': int(cid.split(':')[-1]),
            'preferred_name': r['query'], 'input_queries': [r['query']],
            'inchikey': r['structure_inchikey'], 'resolution_status': 'resolved',
        }])
        try:
            found, mapped = resolve_identities(output, compound, client)
            candidates.extend(found.to_dicts())
            crosswalk.extend(mapped.to_dicts())
            item['identity_status'] = mapped['status'][0]
            item['dtxsid'] = mapped['dtxsid'][0]
            if mapped['status'][0] != 'approved':
                item['state'] = 'identity_' + mapped['status'][0]
            else:
                values, _ = fetch_test_predictions(output, mapped, client)
                if any(v['dtxsid'] != mapped['dtxsid'][0] for v in values.to_dicts()):
                    raise ValueError('Provider record identity mismatch')
                predictions.extend(values.to_dicts())
                item['test_rows'] = values.height
                item['state'] = 'stored_output' if values.height else 'no_stored_output'
        except (requests.RequestException, ValueError, TypeError, RuntimeError, OSError) as exc:
            # Never serialize exception messages, Requests objects or environment values.
            item['state'] = 'failed'
            item['error_type'] = type(exc).__name__
        ledger.append(item)
        write_csv(output / 'collection_log.csv', ledger)
        print(cid, item['state'], flush = True)
    write_csv(output / 'collection_log.csv', ledger)
    write_csv(output / 'identity_candidates.csv', candidates)
    write_csv(output / 'identity_crosswalk.csv', crosswalk)
    prediction_table(predictions).write_parquet(output / 'B_TEST_predictions.parquet')
    write_csv(output / 'B_TEST_predictions.csv', predictions)
    (output / 'reproduction').mkdir()
    code = [Path(__file__), Path('pipeline/src/agrotox/epa_identity.py'),
            Path('pipeline/src/agrotox/epa_test.py'), Path('pipeline/src/agrotox/sources/comptox.py')]
    root = Path(__file__).resolve().parents[1]
    for p in code:
        relative = p.resolve().relative_to(root) if p.is_absolute() else p
        name = relative.as_posix().replace('/', '__')
        (output / 'reproduction' / name).write_bytes((root / relative).read_bytes())
    code = [root / p for p in code]
    manifest = {'status': 'stored_external_predictions_not_new_structure_inference',
                'input': {str(features): sha(features)}, 'code': {str(p): sha(p) for p in code},
                'states': dict(Counter(r['state'] for r in ledger)),
                'attempted': len(rows), 'prediction_rows': len(predictions),
                'prediction_compounds': len({r['compound_id'] for r in predictions}),
                'outputs': {str(p.relative_to(output)): sha(p)
                            for p in sorted(output.rglob('*')) if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent = 2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--features', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(expand(args.features, args.output)['states'], indent = 2))
