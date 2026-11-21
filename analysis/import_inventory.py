"""Inventory local provider imports without extracting archives into the workspace."""

import argparse
import csv
import io
import json
import posixpath
import shutil
from hashlib import file_digest
from pathlib import Path
from tempfile import SpooledTemporaryFile
from xml.etree import ElementTree as ET
from xml.parsers import expat
from zipfile import ZipFile

MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def workbook_tables(archive):
    book = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    targets = {r.attrib['Id']: r.attrib['Target'] for r in rels}
    for sheet in book.find(MAIN + 'sheets'):
        target = targets[sheet.attrib[REL]]
        member = target.lstrip('/') if target.startswith('/') else posixpath.join('xl', target)
        with archive.open(member) as stream:
            yield {'name': sheet.attrib['name'], 'populated_rows': populated_rows(stream)}


def populated_rows(stream):
    rows = 0
    populated = False

    def start(tag):
        nonlocal populated
        if tag == 'row':
            populated = False
        elif tag in {'v', 'is', 'f'}:
            populated = True

    def end(tag):
        nonlocal rows
        if tag == 'row' and populated:
            rows += 1

    parser = expat.ParserCreate(namespace_separator='}')
    parser.StartElementHandler = lambda tag, _: start(tag.rsplit('}', 1)[-1])
    parser.EndElementHandler = lambda tag: end(tag.rsplit('}', 1)[-1])
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        parser.Parse(chunk, False)
    parser.Parse(b'', True)
    return rows


def text_profile(stream, name):
    first = stream.readline()
    suffix = Path(name).suffix.lower()
    delimiter = '\t' if suffix == '.tsv' else ','
    if suffix == '.txt':
        delimiter = max(('\t', '|', ',', ';'), key=first.count)
        if first.count(delimiter) == 0:
            return {'name': name, 'kind': 'documentation'}
    header = next(csv.reader([first], delimiter=delimiter), [])
    records = blank = irregular = 0
    for row in csv.reader(stream, delimiter=delimiter):
        if not any(value.strip() for value in row):
            blank += 1
        else:
            records += 1
            irregular += len(row) != len(header)
    return {'name': name, 'columns': header, 'records': records,
            'blank_records': blank, 'irregular_width_records': irregular}


def zip_tables(archive, prefix=''):
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = prefix + info.filename
        suffix = Path(info.filename).suffix.lower()
        if suffix in {'.zip', '.xlsx'}:
            with archive.open(info) as stream, SpooledTemporaryFile(max_size=8 << 20) as temp:
                shutil.copyfileobj(stream, temp)
                with ZipFile(temp) as nested:
                    if suffix == '.zip':
                        yield from zip_tables(nested, name + '!')
                    else:
                        for table in workbook_tables(nested):
                            yield {**table, 'name': name + '!' + table['name']}
        elif 'readme' in Path(info.filename).stem.casefold():
            yield {'name': name, 'kind': 'documentation'}
        elif suffix in {'.txt', '.tsv', '.csv'}:
            with archive.open(info) as raw, io.TextIOWrapper(raw, 'utf-8-sig', newline='') as stream:
                yield text_profile(stream, name)
        else:
            yield {'name': name, 'kind': 'unprofiled_member', 'bytes': info.file_size}


def inventory(root):
    root = Path(root)
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        with path.open('rb') as stream:
            digest = file_digest(stream, 'sha256').hexdigest()
        tables = []
        suffix = path.suffix.lower()
        if suffix in {'.zip', '.xlsx'}:
            with ZipFile(path) as archive:
                tables = list(zip_tables(archive) if suffix == '.zip' else workbook_tables(archive))
        elif suffix in {'.txt', '.tsv', '.csv'}:
            with path.open(encoding='utf-8-sig', newline='') as stream:
                tables = [text_profile(stream, path.name)]
        yield {'path': name, 'bytes': path.stat().st_size, 'sha256': digest, 'tables': tables}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with args.output.open('x', encoding='utf-8') as stream:
        for entry in inventory(args.root):
            stream.write(json.dumps(entry) + '\n')
