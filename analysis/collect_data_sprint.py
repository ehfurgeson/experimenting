"""Acquire explicitly selected public sprint exports, preserving bytes and failures."""

import argparse
import gzip
import hashlib
import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from data_sprint import sha256

NPASS = 'https://bidd.group/NPASS/downloadFiles/'
SOURCES = {
    name: (NPASS + filename, 'NPASS 3.0', 'Provider terms not yet qualified; local research only')
    for name, filename in [
        ('npass-structure', 'NPASS3.0_naturalproducts_structure.txt'),
        ('npass-general', 'NPASS3.0_naturalproducts_generalinfo.txt'),
        ('npass-toxicity', 'NPASS3.0_toxicity.txt'),
        ('npass-occurrence', 'NPASS3.0_naturalproducts_species_pair.txt'),
        ('npass-species', 'NPASS3.0_species_info.txt'),
        ('npass-activity', 'NPASS3.0_activities.txt'),
        ('npass-target', 'NPASS3.0_target.txt'),
    ]
}
SOURCES['coconut-lite'] = (
    'https://coconut.s3.uni-jena.de/prod/downloads/2026-11/coconut_csv_lite-11-2026.zip',
    'COCONUT November 2026', 'CC0 per provider download page')
for name, file_id in [
    ('toxval-chemid', '68d3f821e4b02565fc7deb11'),
    ('toxval-echa', '68d3f824e4b02565fc7deb2d'),
    ('toxval-test', '68d3f81ee4b02565fc7dea49'),
    ('toxval-dictionary', '68d3f77be4b02565fc7de6bb'),
    ('toxval-opp', '68d3f81ee4b02565fc7dea4c'),
    ('toxval-tsca8e', '68d3f81ee4b02565fc7dea63'),
    ('toxval-hpvis', '68d3f81fe4b02565fc7deac6'),
    ('toxval-dod', '68d3f81fe4b02565fc7deae6'),
    ('toxval-toxref', '68d3f821e4b02565fc7deb07'),
    ('toxval-efsa', '68d3f81fe4b02565fc7deaca'),
    ('toxval-ecotox', '68d3f820e4b02565fc7deaf8'),
    ('toxval-jecfa-studies', '68d3f81ee4b02565fc7de9e3'),
]:
    SOURCES[name] = (f'https://clowder.edap-cluster.com/api/files/{file_id}/blob',
                     'ToxValDB v9.7.0', 'EPA public data; retain upstream source restrictions')


def collect(run, names):
    run = Path(run)
    raw = run / 'raw'
    raw.mkdir(parents = True, exist_ok = True)
    registry = run / 'sources.json'
    records = json.loads(registry.read_text()) if registry.exists() else []
    for name in names:
        filename = name + '.gz' if name.startswith('npass-') else name
        if any(r['source_id'] == name for r in records) or (raw / filename).exists():
            raise ValueError(f'Refusing to overwrite source: {name}')
        if shutil.disk_usage(raw).free < 64 * 1024 * 1024:
            raise OSError('Less than 64 MiB free; stop acquisition before filling local disk')
        url, version, license_note = SOURCES[name]
        record = {'source_id': name, 'url': url, 'version': version, 'license': license_note,
                  'acquired_at': datetime.now(UTC).isoformat(), 'file': f'raw/{filename}',
                  'storage_encoding': 'gzip' if filename.endswith('.gz') else 'identity'}
        started = time.monotonic()
        native_digest, native_bytes = hashlib.sha256(), 0
        try:
            with requests.get(url, stream = True, timeout = (15, 60)) as response:
                record.update(http_status = response.status_code, final_url = response.url,
                              content_type = response.headers.get('Content-Type'),
                              last_modified = response.headers.get('Last-Modified'))
                opener = gzip.open if filename.endswith('.gz') else open
                with opener(raw / filename, 'xb') as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        if time.monotonic() - started > 1800:
                            raise TimeoutError('30 minute source acquisition budget exhausted')
                        stream.write(chunk)
                        native_digest.update(chunk)
                        native_bytes += len(chunk)
                record['status'] = 'downloaded' if response.ok else 'http_error'
        except (requests.RequestException, TimeoutError, OSError) as exc:
            record.update(status = 'failed', error = type(exc).__name__)
        if (raw / filename).exists():
            record.update(sha256 = sha256(raw / filename), bytes = (raw / filename).stat().st_size,
                          native_sha256 = native_digest.hexdigest(), native_bytes = native_bytes)
        record['seconds'] = round(time.monotonic() - started, 2)
        records.append(record)
        registry.write_text(json.dumps(records, indent = 2) + '\n')
        print(name, record['status'], record.get('bytes'), flush = True)
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('--run', type = Path, required = True)
    parser.add_argument('--only', choices = list(SOURCES), nargs = '+', required = True)
    args = parser.parse_args()
    collect(args.run, args.only)
