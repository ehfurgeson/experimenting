"""Join all qualified NPASS structures to an already verified COCONUT snapshot."""

import argparse
import csv
import gzip
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from data_sprint import sha256
from sprint_report import verify_bundle


def run(npass, coconut, output):
    npass, coconut, output = Path(npass), Path(coconut), Path(output)
    n_manifest, c_manifest = verify_bundle(npass), verify_bundle(coconut)
    archives = [Path(p) for p in c_manifest['inputs'] if Path(p).name == 'coconut-lite']
    if len(archives) != 1:
        raise ValueError('One verified COCONUT archive required')
    with gzip.open(npass / 'npass_identity.csv.gz', 'rt') as stream:
        compounds = list(csv.DictReader(stream))
    with gzip.open(coconut / 'coconut_identity_conflicts.csv.gz', 'rt') as stream:
        held_ids = {r['source_compound_id'] for r in csv.DictReader(stream)}
    wanted = {r['full_inchikey'].split('-')[0] for r in compounds
              if r['identity_status'] == 'valid'}
    exact, connected, source_count = defaultdict(set), defaultdict(set), 0
    with ZipFile(archives[0]) as archive:
        names = [n for n in archive.namelist() if n.endswith('.csv')]
        if len(names) != 1:
            raise ValueError('One source CSV required')
        with archive.open(names[0]) as raw, io.TextIOWrapper(raw, encoding = 'utf-8-sig',
                                                           newline = '') as stream:
            for r in csv.DictReader(stream):
                source_count += 1
                if r['identifier'] in held_ids:
                    continue
                key = r['standard_inchi_key']
                if key.split('-')[0] in wanted:
                    exact[key].add(r['identifier'])
                    connected[key.split('-')[0]].add(r['identifier'])
    if source_count != c_manifest['source_records']:
        raise ValueError('Verified source row count mismatch')
    fields = ['npass_compound_id', 'full_inchikey', 'npass_identity_status', 'match_tier',
              'coconut_ids', 'occurrence_evidence_type']
    output.mkdir(parents = True, exist_ok = False)
    counts = Counter()
    distinct = defaultdict(set)
    with gzip.open(output / 'npass_coconut_overlap.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = fields)
        writer.writeheader()
        for r in compounds:
            key = r['full_inchikey']
            full = exact.get(key, set()) if r['identity_status'] == 'valid' else set()
            maybe = connected.get(key.split('-')[0], set()) if key else set()
            tier = ('identity_hold' if r['identity_status'] != 'valid' else 'exact_full_key' if full
                    else 'connectivity_only_review' if maybe else 'unresolved')
            writer.writerow({'npass_compound_id': r['source_compound_id'], 'full_inchikey': key,
                             'npass_identity_status': r['identity_status'], 'match_tier': tier,
                             'coconut_ids': ';'.join(sorted(full or maybe)),
                             'occurrence_evidence_type': 'catalog_membership_only'})
            counts[tier] += 1
            if key:
                distinct[tier].add(key)
    result = {'inputs': {str(p / 'manifest.json'): sha256(p / 'manifest.json')
                         for p in (npass, coconut)},
              'npass_source_ids': n_manifest['identity_records'], 'source_id_match_counts': dict(counts),
              'distinct_full_keys_by_tier': {k: len(v) for k, v in distinct.items()},
              'limits': 'Reuses the prior all-structure provider-key verification; held COCONUT '
                        'IDs are excluded. Catalog overlap adds no independent occurrence or '
                        'toxicity study. Connectivity stays review-only.',
              'code_sha256': sha256(__file__),
              'products': {'npass_coconut_overlap.csv.gz': sha256(output / 'npass_coconut_overlap.csv.gz')}}
    (output / 'manifest.json').write_text(json.dumps(result, indent = 2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ('npass', 'coconut', 'output'):
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.npass, args.coconut, args.output), indent = 2))
