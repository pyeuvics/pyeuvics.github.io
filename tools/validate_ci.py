#!/usr/bin/env python3
"""Run the complete website validation identically in CI and local reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.site_assembly import AssemblyError, assemble_site
from tools.site_assembly.contracts import ContractError


class ValidationError(ValueError):
    """The CI-equivalent validation could not complete safely."""


def _run(arguments: list[str], cwd: Path) -> None:
    try:
        subprocess.run(arguments, cwd=cwd, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationError(f"validation command failed: {' '.join(arguments)}") from exc


def _source_date_epoch(website_root: Path) -> str:
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured is not None:
        try:
            if int(configured) < 0:
                raise ValueError
        except ValueError as exc:
            raise ValidationError("SOURCE_DATE_EPOCH must be a non-negative integer") from exc
        return configured
    try:
        value = subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", "HEAD"],
            cwd=website_root,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValidationError("cannot derive SOURCE_DATE_EPOCH from the website commit") from exc
    if not value.isdigit():
        raise ValidationError("website commit timestamp is invalid")
    os.environ["SOURCE_DATE_EPOCH"] = value
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    manifest_path.write_text(
        json.dumps({"manifest_version": 1, "files": files}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
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

    website_root = website_root.resolve()
    output_root = output_root.resolve()
    strict_site = output_root.parent / f"{output_root.name}-strict-site"
    if output_root.exists() or strict_site.exists():
        raise ValidationError("CI validation output paths must not already exist")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    _source_date_epoch(website_root)
    _run(
        [
            sys.executable,
            str(euvics_source / "tools/publication_contract.py"),
            "validate",
            "--repository-root",
            str(euvics_source),
            "--manifest",
            str(euvics_source / "publication/public-content-v1.json"),
        ],
        website_root,
    )
    _run(
        [
            sys.executable,
            str(pyeuvics_source / "tools/publication_contract.py"),
            "validate",
            "--repository-root",
            str(pyeuvics_source),
            "--manifest",
            str(pyeuvics_source / "publication/public-content-v1.json"),
        ],
        website_root,
    )
    _run([sys.executable, "-m", "pytest"], website_root)
    _run(
        [sys.executable, "-m", "mypy", "--strict", "tools/site_assembly", "tools/assemble_site.py", "tools/ci_source_locks.py", "tools/validate_ci.py"],
        website_root,
    )
    _run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(strict_site)],
        website_root,
    )
    try:
        assemble_site(website_root, lock_path, euvics_source, pyeuvics_source, output_root)
    except (AssemblyError, ContractError) as exc:
        raise ValidationError(str(exc)) from exc
    return write_review_manifest(output_root)


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
