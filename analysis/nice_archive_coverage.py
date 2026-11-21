"""Profile ClassyFire and cHTS coverage for the reconstructed measured cohort."""

import argparse
import csv
import io
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import SpooledTemporaryFile
from zipfile import ZipFile

from data_sprint import read_csv, sha256
from evidence_release import write_csv
from nice_context import match
from sprint_report import verify_bundle


def tsv(archive, member):
    with archive.open(member) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig',
                                                      newline='') as stream:
        yield from csv.DictReader(stream, delimiter='\t')


def assay_coverage(rows, known):
    cells = defaultdict(Counter)
    counts = Counter()
    for row in rows:
        counts['source_rows'] += 1
        sid = row['DTXSID']
        if sid in known:
            cells[sid][row['Endpoint']] += 1
            counts['matched_rows'] += 1
    return cells, dict(counts)


def run(nice, release, output):
    nice, release, output = map(Path, (nice, release, output))
    sources = [nice / name for name in ('ChemicalTaxonomies.zip', 'cHTS_AllDownloadFiles.zip')]
    inputs = {str(path): sha256(path) for path in [*sources, release / 'manifest.json']}
    verify_bundle(release)
    wanted = {row['full_key'] for row in read_csv(release / 'A_compounds.csv')}
    mappings = defaultdict(set)
    for row in read_csv(release / 'A_observations.csv'):
        if row['status'] in {'exact', 'censored'} and row['full_key'] and row['dtxsid']:
            mappings[row['dtxsid']].add(row['full_key'])
    known = {sid: next(iter(keys)) for sid, keys in mappings.items()
             if len(keys) == 1 and keys <= wanted}
    output.mkdir(parents=True, exist_ok=False)
    taxonomy, tally, cache = [], Counter(), {}
    with ZipFile(sources[0]) as archive:
        members = [name for name in archive.namelist() if name.startswith('ChemicalTaxonomies_v')]
        member, = members
        for ordinal, row in enumerate(tsv(archive, member), 1):
            tally['source_rows'] += 1
            if row['DTXSID'] not in mappings and row['InChiKey'] not in wanted:
                continue
            found = match(row, mappings, wanted, cache)
            if found is None:
                found = ('identity_hold', {row['InChiKey']})
            tier, keys = found
            if tier == 'exact_structure' and keys != {row['InChiKey']}:
                tier = 'identity_hold'
            tally[tier] += 1
            taxonomy.append({'member': member, 'record_ordinal': ordinal,
                             'identity_tier': tier, 'candidate_full_keys': ';'.join(sorted(keys)),
                             **row})
    with (ZipFile(sources[1]) as archive, archive.open('cHTS_DataDownload.zip') as raw,
          SpooledTemporaryFile(max_size=8 << 20) as temp):
        shutil.copyfileobj(raw, temp)
        with ZipFile(temp) as nested:
            member, = [n for n in nested.namelist() if 'readme' not in n.casefold()]
            coverage, counts = assay_coverage(tsv(nested, member), known)
    if taxonomy:
        write_csv(output / 'classyfire_context.csv', taxonomy)
    assay_rows = [{'dtxsid': sid, 'full_key': known[sid], 'endpoint': endpoint, 'rows': n}
                  for sid, tallies in sorted(coverage.items()) for endpoint, n in sorted(tallies.items())]
    if assay_rows:
        write_csv(output / 'chts_coverage.csv', assay_rows)
    summary = {'inputs': inputs, 'products': {p.name: sha256(p) for p in output.iterdir()},
               'taxonomy': dict(tally),
               'chts': counts | {'matched_dtxsids': len(coverage),
                                 'matched_full_keys': len({known[sid] for sid in coverage})},
               'limits': 'cHTS counts coverage only. Assay activity needs interference and QC review.'}
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('nice', 'release', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
