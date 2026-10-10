"""Small filesystem/process mechanisms without publication-policy decisions."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from collections.abc import Mapping
import re
import subprocess
import tarfile
import tempfile


class FileOperationError(ValueError):
    """A bounded filesystem or subprocess operation failed."""


def sha256_file(path: Path) -> str:
    """Hash file bytes in bounded blocks, without reading the whole file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    """Replace a small UTF-8/LF file atomically; retain the old file on failure."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_text(arguments: list[str], cwd: Path, label: str, *, max_bytes: int = 8_388_608, environment: Mapping[str, str] | None = None) -> str:
    """Capture bounded output; never echo command arguments or failure output."""
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(arguments, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, env=environment)
        except OSError as exc:
            raise FileOperationError(f"{label} unavailable") from exc
        if result.returncode:
            raise FileOperationError(f"{label} failed (exit {result.returncode}); output withheld")
        if output.tell() > max_bytes:
            raise FileOperationError(f"{label} output exceeds capture limit")
        output.seek(0)
        return output.read().decode("utf-8", errors="replace")


def extract_regular_archive(archive: Path, destination: Path) -> None:
    """Validate all POSIX members before extracting ordinary files/directories."""
    if destination.exists():
        raise FileOperationError("archive destination already exists")
    try:
        with tarfile.open(archive, mode="r:") as stream:
            seen: set[str] = set()
            for member in stream:
                name = member.name.rstrip("/") if member.isdir() else member.name
                path = PurePosixPath(name)
                if (not name or path.is_absolute() or ".." in path.parts
                        or path.as_posix() != name or name == "."
                        or "\\" in name or ":" in name
                        or any(ord(char) < 32 or ord(char) == 127 for char in name)
                        or not (member.isfile() or member.isdir()) or name in seen):
                    raise FileOperationError("unsafe member in locked source archive")
                seen.add(name)
        destination.mkdir(parents=True)
        with tarfile.open(archive, mode="r:") as stream:
            stream.extractall(destination, filter="data")
    except (OSError, tarfile.TarError) as exc:
        raise FileOperationError("cannot extract locked source archive") from exc


def export_locked_tree(root: Path, commit: str, destination: Path) -> None:
    """Spool a locked Git archive to disk and validate before extraction."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise FileOperationError("locked archive requires an exact Git commit")
    with tempfile.TemporaryDirectory(prefix="website-archive-") as temporary:
        archive = Path(temporary) / "source.tar"
        with archive.open("wb") as output, tempfile.TemporaryFile() as errors:
            try:
                result = subprocess.run(["git", "archive", "--format=tar", commit],
                                        cwd=root, stdout=output, stderr=errors)
            except OSError as exc:
                raise FileOperationError("git archive unavailable") from exc
        if result.returncode:
            raise FileOperationError(f"git archive failed (exit {result.returncode}); output withheld")
        extract_regular_archive(archive, destination)
