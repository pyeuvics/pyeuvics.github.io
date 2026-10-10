from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import tarfile

import pytest

from tests.support.publication import create_repo, euvics_manifest
from tools.site_assembly.primitives import (
    FileOperationError, atomic_write_text, export_locked_tree,
    extract_regular_archive, run_text, sha256_file,
)


def test_streaming_hash_and_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "input"
    payload = b"abc" * 1_000_000
    path.write_bytes(payload)
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()
    with pytest.raises(OSError):
        sha256_file(tmp_path)


def test_atomic_write_preserves_original_after_replace_failure(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "record.json"
    atomic_write_text(path, '{"value": "old"}\n')
    def fail(*args):
        raise OSError("synthetic replacement failure")
    monkeypatch.setattr("tools.site_assembly.primitives.os.replace", fail)
    with pytest.raises(OSError):
        atomic_write_text(path, "new\n")
    assert path.read_bytes() == b'{"value": "old"}\n'
    assert set(tmp_path.iterdir()) == {path}


@pytest.mark.parametrize("command,message", [
    (["/missing-website-test-command"], "unavailable"),
    ([sys.executable, "-c", "print('synthetic-secret'); raise SystemExit(7)"], "exit 7"),
    ([sys.executable, "-c", "print('a' * 20)"], "capture limit"),
])
def test_command_failures_hide_output(tmp_path: Path, command, message: str) -> None:
    with pytest.raises(FileOperationError, match=message) as caught:
        run_text(command, tmp_path, "fixture command", max_bytes=10)
    assert "synthetic-secret" not in str(caught.value)


@pytest.mark.parametrize("name,kind", [
    ("../escape", tarfile.REGTYPE), ("/absolute", tarfile.REGTYPE),
    ("a/../escape", tarfile.REGTYPE), ("a\\escape", tarfile.REGTYPE),
    ("C:/escape", tarfile.REGTYPE), ("alias", tarfile.SYMTYPE),
    ("hardlink", tarfile.LNKTYPE), ("device", tarfile.CHRTYPE),
])
def test_archive_rejects_unsafe_members_before_writing(tmp_path: Path, name, kind) -> None:
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w") as stream:
        safe = tarfile.TarInfo("safe"); safe.size = 2
        stream.addfile(safe, io.BytesIO(b"ok"))
        bad = tarfile.TarInfo(name); bad.type = kind; bad.linkname = "safe"
        stream.addfile(bad)
    destination = tmp_path / "output"
    with pytest.raises(FileOperationError, match="unsafe member"):
        extract_regular_archive(archive, destination)
    assert not destination.exists()


def test_export_uses_exact_tree_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    commit = create_repo(source, euvics_manifest(), {"docs/overview.md": "approved\n"})
    (source / "docs/overview.md").write_text("uncommitted\n", encoding="utf-8")
    output = tmp_path / "export"
    export_locked_tree(source, commit, output)
    assert (output / "docs/overview.md").read_bytes() == b"approved\n"
    assert (source / "docs/overview.md").read_bytes() == b"uncommitted\n"
    with pytest.raises(FileOperationError, match="already exists"):
        export_locked_tree(source, commit, output)
    with pytest.raises(FileOperationError, match="git archive failed"):
        export_locked_tree(source, "0" * 40, tmp_path / "missing")
