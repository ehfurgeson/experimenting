import pytest

from data_sprint import sha256
from rebuild_joint_catalog import public_snapshot


def test_checksum_mismatch_leaves_no_public_snapshot_to_resume(tmp_path):
    cache = tmp_path / 'cached-archive'
    cache.write_bytes(b'known data')
    target = tmp_path / 'download' / 'archive'

    with pytest.raises(ValueError, match='checksum mismatch'):
        public_snapshot(target, 'https://example.invalid/archive', 'invalid-digest', cache)
    assert not target.exists()

    public_snapshot(target, 'https://example.invalid/archive', sha256(cache), cache)
    assert target.read_bytes() == cache.read_bytes()
    public_snapshot(target, 'https://example.invalid/archive', sha256(cache))
