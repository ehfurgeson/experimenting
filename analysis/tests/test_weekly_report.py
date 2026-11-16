"""Walkthroughs verify research bytes without rewriting frozen code history."""
import hashlib
import json
import sys
from pathlib import Path

import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from weekly_report import table, verify_manifest


def test_manifest_rejects_changed_research_bytes(tmp_path):
    data = tmp_path / 'evidence.txt'
    data.write_text('original')
    manifest = tmp_path / 'manifest.json'
    expected = hashlib.sha256(data.read_bytes()).hexdigest()
    manifest.write_text(json.dumps({'input_hashes': {str(data): expected},
                                    'code_hashes': {'historical/unavailable.py': 'historical'}}))
    assert verify_manifest(manifest)['input_hashes'][str(data)] == expected
    data.write_text('changed')
    with pytest.raises(ValueError, match = 'Hash mismatch'):
        verify_manifest(manifest)


def test_html_table_escapes_source_content():
    result = table(pl.DataFrame([{'name': '<script>bad</script>', 'value': 1.23456}]),
                   ['name', 'value'])
    assert '<script>' not in result
    assert '&lt;script&gt;' in result
    assert '1.235' in result


def test_archived_input_copy_requires_exact_original_hash_and_is_recorded(tmp_path):
    old, archive = tmp_path / 'resource.json', tmp_path / 'archived.json'
    old.write_text('later annotations')
    archive.write_text('original acquisition resource')
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'input_hashes': {str(old): expected}}))
    resolutions = {}
    verify_manifest(manifest, {expected: archive}, resolutions)
    assert resolutions == {str(old): str(archive)}
    archive.write_text('tampered archive')
    with pytest.raises(ValueError, match = 'Hash mismatch'):
        verify_manifest(manifest, {expected: archive})
    manifest.write_text(json.dumps({'output_hashes': {str(old): expected}}))
    with pytest.raises(ValueError, match = 'Hash mismatch'):
        verify_manifest(manifest, {expected: archive})
