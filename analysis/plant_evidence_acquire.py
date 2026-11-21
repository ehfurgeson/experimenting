"""Bounded acquisition of complete ChEMBL publication series and open primary text."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import requests

from data_sprint import sha256

BASE = 'https://www.ebi.ac.uk/chembl/api/data'
DOCUMENTS = ['CHEMBL3044838', 'CHEMBL1158691', 'CHEMBL3044763', 'CHEMBL3046702',
             'CHEMBL3046139', 'CHEMBL1139894', 'CHEMBL3046625', 'CHEMBL3046670']


def run(output):
    output = Path(output)
    output.mkdir(parents = True, exist_ok = False)
    registry = []
    session = requests.Session()

    def get(name, url, params = None):
        record = {'name': name, 'url': url, 'params': params,
                  'retrieved_at': datetime.now(UTC).isoformat()}
        path = output / name
        try:
            response = session.get(url, params = params, timeout = (15, 45))
            path.write_bytes(response.content)
            record.update(status = response.status_code, final_url = response.url,
                          sha256 = sha256(path), bytes = path.stat().st_size)
            response.raise_for_status()
            value = response.json() if '.json' in name else response.text
        except (requests.RequestException, ValueError) as exc:
            record['error'] = type(exc).__name__
            value = None
        registry.append(record)
        (output / 'sources.json').write_text(json.dumps(registry, indent = 2) + '\n')
        print(name, record.get('status', record.get('error')), flush = True)
        return value

    get('chembl-status.json', BASE + '/status.json')
    for doc in DOCUMENTS:
        get(doc + '-document.json', BASE + '/document/' + doc + '.json')
        offset, total = 0, None
        while True:
            data = get(f'{doc}-activities-{offset}.json', BASE + '/activity.json', {
                'document_chembl_id': doc, 'limit': 1000, 'offset': offset,
                'order_by': 'activity_id'})
            if data is None:
                break
            meta = data['page_meta']
            if total is not None and total != meta['total_count']:
                raise ValueError('Changed source count')
            total = meta['total_count']
            if total > 10000:
                raise ValueError('Document exceeds bounded acquisition')
            offset += len(data['activities'])
            if offset == total:
                break
            if not data['activities']:
                raise ValueError('Incomplete document activity page')
    get('coumarins2020.xml', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7238165/fullTextXML')
    get('cuscuta-search.json', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search', {
        'query': 'DOI:10.3390/agriculture12101746', 'format': 'json'})
    get('pubchem-growth-discovery.json', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', {
        'db': 'pcassay', 'term': '"Arabidopsis thaliana" AND ("root growth" OR "seedling growth")',
        'retmode': 'json', 'retmax': 30})
    return {'requests': len(registry), 'successful': sum(r.get('status') == 200 for r in registry)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--output', type = Path, required = True)
    print(json.dumps(run(parser.parse_args().output), indent = 2))
