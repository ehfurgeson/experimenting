"""Retrieve bounded follow-up primary sources and PubChem assay descriptions."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import requests

from data_sprint import sha256


def run(sources, output):
    sources, output = Path(sources), Path(output)
    output.mkdir(parents = True, exist_ok = False)
    ids = json.loads((sources / 'pubchem-growth-discovery.json').read_text())['esearchresult']['idlist']
    urls = {
        'pubchem-assay-descriptions.json': 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/' + ','.join(ids) + '/description/JSON',
        'cuscuta2022.pdf': 'https://rodin.uca.es/bitstream/handle/10498/28834/2022_946.pdf?isAllowed=y&sequence=1',
        'coumarins2020.pdf': 'https://mdpi-res.com/d_attachment/plants/plants-09-00533/article_deploy/plants-09-00533.pdf',
        'kava2006.pdf': 'https://drugs-forum.com/data/attachment-files/2009/10/134425_herbicie__fungicide_Xuan.pdf',
        'rhodanines1996.html': 'https://www.jstage.jst.go.jp/article/bbb1961/60/8/60_8_1368/_article',
    }
    registry = []
    for name, url in urls.items():
        record = {'url': url, 'file': name, 'retrieved_at': datetime.now(UTC).isoformat()}
        try:
            response = requests.get(url, timeout = (15, 45))
            (output / name).write_bytes(response.content)
            record.update(status = response.status_code, final_url = response.url,
                          sha256 = sha256(output / name), bytes = len(response.content),
                          content_type = response.headers.get('Content-Type'))
        except requests.RequestException as exc:
            record['error'] = type(exc).__name__
        registry.append(record)
        (output / 'sources.json').write_text(json.dumps(registry, indent = 2) + '\n')
        print(name, record.get('status', record.get('error')), flush = True)
    return registry


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--sources', type = Path, required = True)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    run(args.sources, args.output)
