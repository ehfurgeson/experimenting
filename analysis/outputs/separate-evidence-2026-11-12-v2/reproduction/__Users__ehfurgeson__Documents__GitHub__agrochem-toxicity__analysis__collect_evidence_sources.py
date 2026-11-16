"""Explicit public-source acquisition into a fresh immutable local directory."""
import argparse
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

OPERA_COMMIT = '01b07c769dd86eadb71843e057783a64a364c885'
PUBLIC_SOURCES = [
    ('ice-acute-oral.xlsx', 'https://ice.ntp.niehs.nih.gov/downloads/DataonICE/acute_oral.xlsx',
     'NIH ICE', 'experimental', 'Workbook metadata 4.1; original study lineage incomplete'),
    ('ice-acute-oral-summary.xlsx',
     'https://ice.ntp.niehs.nih.gov/downloads/DataonICE/Acute_Oral_Toxicity.xlsx',
     'NIH ICE older export', 'mixed_inventory', 'Possible mirror; not pooled'),
    ('ice-index.html', 'https://ice.ntp.niehs.nih.gov/downloads/DataonICE/',
     'NIH ICE index', 'documentation', 'Bulk resource availability'),
    ('OPERA_Data.zip', f'https://raw.githubusercontent.com/kmansouri/OPERA/{OPERA_COMMIT}/OPERA_Data.zip',
     'OPERA CATMoS', 'predicted_and_embedded_comparators', 'Shared NICEATM lineage'),
    ('opera-readme.md', f'https://raw.githubusercontent.com/kmansouri/OPERA/{OPERA_COMMIT}/README.md',
     'OPERA documentation', 'documentation', 'CATMoS scale Log mg/kg'),
    ('opera-tree.json', f'https://api.github.com/repos/kmansouri/OPERA/git/trees/{OPERA_COMMIT}?recursive=1',
     'OPERA repository', 'documentation', 'Pinned source version'),
    ('opera-license.txt', f'https://raw.githubusercontent.com/kmansouri/OPERA/{OPERA_COMMIT}/LICENSE',
     'OPERA license', 'documentation', 'Inspect license scope before redistribution'),
    ('zenodo-ld50.xlsx',
     'https://zenodo.org/api/records/3300664/files/LD50_PublicCollectedData.xlsx/content',
     'Zenodo3300664', 'held_aggregation', 'Shares TESTEPA, NICEATM and Toolbox'),
    ('zenodo.json', 'https://zenodo.org/api/records/3300664',
     'Zenodo metadata', 'documentation', 'Author source and rights metadata'),
    ('test.html', 'https://www.epa.gov/comptox-tools/toxicity-estimation-software-tool-test',
     'EPA TEST', 'documentation', 'Installation/batch route; not a prediction service call'),
    ('vega.html', 'https://www.vegahub.eu/portfolio-item/vega-qsar/',
     'VEGA', 'documentation', 'Java batch route; no outputs acquired'),
    ('genra.html', 'https://www.epa.gov/comptox-tools/generalized-read-across-genra',
     'EPA GenRA', 'documentation', 'Analogue workflow; no outputs acquired'),
    ('toolbox.html', 'https://qsartoolbox.org/download/',
     'OECD QSAR Toolbox', 'documentation', 'Installation/endpoint qualification pending'),
]


def collect(output):
    output = Path(output)
    output.mkdir(parents = True, exist_ok = False)
    log = []
    session = requests.Session()
    for name, url, provider, evidence, lineage in PUBLIC_SOURCES:
        item = {'file': name, 'url': url, 'provider': provider, 'evidence': evidence,
                'lineage': lineage, 'retrieved_at': datetime.now(UTC).isoformat()}
        try:
            response = session.get(url, timeout = (15, 120))
            # Preserve failures, including provider error bodies; no credentials are used.
            (output / name).write_bytes(response.content)
            item.update(status = response.status_code, bytes = len(response.content),
                        sha256 = hashlib.sha256(response.content).hexdigest(),
                        final_url = response.url, content_type = response.headers.get('Content-Type'),
                        last_modified = response.headers.get('Last-Modified'))
        except requests.RequestException as exc:
            item.update(error = type(exc).__name__)
        log.append(item)
        (output / 'collection-http.json').write_text(json.dumps(log, indent = 2) + '\n')
        time.sleep(.25)
    return log


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--output', type = Path, required = True)
    args = parser.parse_args()
    for item in collect(args.output):
        print(item['file'], item.get('status', item.get('error')))
