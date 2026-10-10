#!/usr/bin/env python3
"""Run the complete website validation identically in CI and local reviews."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.site_assembly.promotion import promote_directory
from tools.site_assembly.timestamps import TimestampError, parse_timestamp
from tools.site_assembly.primitives import atomic_write_text, sha256_file

from tools.site_assembly import AssemblyError, assemble_site
from tools.site_assembly.contracts import ContractError, load_locks, verify_checkout


class ValidationError(ValueError):
    """The CI-equivalent validation could not complete safely."""


def _run(arguments: list[str], cwd: Path, epoch: str | None = None) -> None:
    try:
        environment = dict(os.environ)
        if epoch is not None:
            environment["SOURCE_DATE_EPOCH"] = epoch
        subprocess.run(arguments, cwd=cwd, check=True, env=environment)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationError(f"validation command failed: {' '.join(arguments)}") from exc


def _source_date_epoch(website_root: Path) -> str:
    value = os.environ.get("SOURCE_DATE_EPOCH")
    if value is None:
        try:
            value = subprocess.check_output(
                ["git", "show", "-s", "--format=%ct", "HEAD"], cwd=website_root,
                text=True, stderr=subprocess.STDOUT,
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValidationError("cannot derive SOURCE_DATE_EPOCH from the website commit") from exc
    try:
        return parse_timestamp(value).epoch
    except TimestampError as exc:
        raise ValidationError(str(exc)) from exc


_sha256 = sha256_file


def write_review_manifest(output_root: Path) -> Path:
    """Record every review-artifact file and checksum in stable order."""

    site = output_root / "site"
    inventory = output_root / "staged-content-inventory.json"
    if not site.is_dir() or not inventory.is_file():
        raise ValidationError("assembled review artifact is incomplete")
    files = [
        {
            "path": path.relative_to(output_root).as_posix(),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(site.rglob("*"))
        if path.is_file()
    ]
    files.append(
        {
            "path": inventory.relative_to(output_root).as_posix(),
            "sha256": _sha256(inventory),
            "bytes": inventory.stat().st_size,
        }
    )
    manifest_path = output_root / "review-artifact-manifest.json"
    atomic_write_text(
        manifest_path, json.dumps({"manifest_version": 1, "files": files}, indent=2, sort_keys=True) + "\n",
    )
    return manifest_path


def validate(
    website_root: Path,
    lock_path: Path,
    euvics_source: Path,
    pyeuvics_source: Path,
    output_root: Path,
) -> Path:
    """Run source contracts, tests, strict build, assembly, scan, and hashing."""

    if output_root.exists() or output_root.is_symlink():
        raise ValidationError("CI validation output path must not already exist")
    website_root = website_root.resolve()
    output_root = output_root.resolve()
    euvics_source = euvics_source.resolve()
    pyeuvics_source = pyeuvics_source.resolve()
    try:
        locks = load_locks(lock_path)
        for name, source in (("euvics", euvics_source), ("pyeuvics", pyeuvics_source)):
            verify_checkout(locks[name], source)
    except ContractError as exc:
        raise ValidationError(str(exc)) from exc
    if output_root.exists() or output_root.is_symlink():
        raise ValidationError("CI validation output path must not already exist")
    epoch = _source_date_epoch(website_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.validation-", dir=output_root.parent))
    strict_site = workspace / "strict-site"
    assembly = workspace / "assembly"
    try:
        _run(
            [
                sys.executable,
                str(euvics_source / "tools/publication_contract.py"),
                "validate",
                "--repository-root",
                str(euvics_source),
                "--manifest",
                str(euvics_source / locks["euvics"].manifest_path),
            ],
            website_root,
            epoch,
        )
        _run(
            [
                sys.executable,
                str(pyeuvics_source / "tools/publication_contract.py"),
                "validate",
                "--repository-root",
                str(pyeuvics_source),
                "--manifest",
                str(pyeuvics_source / locks["pyeuvics"].manifest_path),
            ],
            website_root,
            epoch,
        )
        _run([sys.executable, "-m", "pytest"], website_root, epoch)
        _run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "tools/site_assembly",
                "tools/assemble_site.py",
                "tools/ci_source_locks.py",
                "tools/source_update.py",
                "tools/validate_ci.py",
            ],
            website_root,
            epoch,
        )
        _run(
            [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(strict_site)],
            website_root,
            epoch,
        )
        assemble_site(website_root, lock_path, euvics_source, pyeuvics_source, assembly, source_date_epoch=epoch)
        write_review_manifest(assembly)
        promote_directory(assembly, output_root)
    except Exception as exc:
        atomic_write_text(workspace / "INCOMPLETE.json", json.dumps({"status": "incomplete", "error_type": type(exc).__name__}, sort_keys=True) + "\n")
        raise ValidationError(f"{exc}; incomplete validation workspace retained at {workspace}") from exc
    shutil.rmtree(workspace)  # Only this invocation's owned scratch directory.
    return output_root / "review-artifact-manifest.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--website-root", type=Path, default=Path("."))
    parser.add_argument("--lock", type=Path, default=Path("sources.lock.yml"))
    parser.add_argument("--euvics-source", type=Path, required=True)
    parser.add_argument("--pyeuvics-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = validate(
            args.website_root,
            args.lock,
            args.euvics_source,
            args.pyeuvics_source,
            args.output,
        )
    except ValidationError as exc:
        print(f"CI validation error: {exc}", file=sys.stderr)
        return 1
    print(f"review artifact manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
