import io
from zipfile import ZipFile

from import_inventory import inventory


def test_inventory_profiles_nested_tables_and_counts_blank_records_separately(tmp_path):
    (tmp_path / 'one.tsv').write_text('id\tname\n1\talpha\n\t\n2\tbravo\n')
    (tmp_path / 'data_desc.md').write_text('Source notes')
    inner = io.BytesIO()
    with ZipFile(inner, 'w') as archive:
        archive.writestr('data.csv', 'id,name\n3,"charlie\n delta"\n')
    with ZipFile(tmp_path / 'two.zip', 'w') as archive:
        archive.writestr('nested.zip', inner.getvalue())
    by_path = {entry['path']: entry for entry in inventory(tmp_path)}
    assert by_path['one.tsv']['tables'][0]['records'] == 2
    assert by_path['one.tsv']['tables'][0]['blank_records'] == 1
    assert by_path['two.zip']['tables'][0]['name'] == 'nested.zip!data.csv'
    assert by_path['two.zip']['tables'][0]['records'] == 1
    assert by_path['data_desc.md']['tables'] == []
    assert all(len(entry['sha256']) == 64 for entry in by_path.values())


def test_inventory_uses_sheet_relationships_and_excludes_style_only_rows(tmp_path):
    main = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rel = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with ZipFile(tmp_path / 'source.xlsx', 'w') as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{main}" xmlns:r="{rel}">'
                         '<sheets><sheet name="Data" r:id="rId9"/></sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels',
                         '<Relationships><Relationship Id="rId9" '
                         'Target="/xl/worksheets/sheet2.xml"/></Relationships>')
        archive.writestr('xl/worksheets/sheet2.xml', f'<worksheet xmlns="{main}"><sheetData>'
                         '<row><c t="inlineStr"><is><t>id</t></is></c></row>'
                         '<row><c><v>7</v></c></row><row><c s="1"/></row>'
                         '</sheetData></worksheet>')
    [entry] = inventory(tmp_path)
    assert entry['tables'] == [{'name': 'Data', 'populated_rows': 2}]
