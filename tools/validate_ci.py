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

from tools.quality import run_command as _run,run_checks,write_receipt,verify_receipt
from tools.validation_evidence import EvidenceError,ARTIFACT_EVIDENCE,website_identity,environment_identity,lock_identity,write_record
from tools.review_manifest import ReviewManifest,ReviewFile,ReviewManifestError,write_manifest
from tools.site_assembly.promotion import promote_directory
from tools.site_assembly.timestamps import TimestampError, parse_timestamp
from tools.site_assembly.primitives import atomic_write_text, sha256_file

from tools.site_assembly import AssemblyError, assemble_site
from tools.site_assembly.contracts import ContractError, load_locks, verify_checkout


class ValidationError(ValueError):
    """The CI-equivalent validation could not complete safely."""


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
    files=[]
    for path in sorted(site.rglob('*')):
        if path.is_symlink():raise ValidationError('aliased review artifact file or directory')
        if path.is_dir():continue
        if not path.is_file():raise ValidationError('nonregular review artifact file')
        files.append(ReviewFile(path.relative_to(output_root).as_posix(),_sha256(path),path.stat().st_size))
    if inventory.is_symlink() or site.is_symlink():raise ValidationError('aliased review artifact root or inventory')
    files.append(ReviewFile(inventory.relative_to(output_root).as_posix(),_sha256(inventory),inventory.stat().st_size))
    for name in (*ARTIFACT_EVIDENCE,'notebook-execution-provenance.json','source-build/document-build-evidence.json'):
        if name=='staged-content-inventory.json':continue
        path=output_root/name
        if path.exists():
            if path.is_symlink() or not path.is_file():raise ValidationError('aliased internal artifact evidence')
            files.append(ReviewFile(name,_sha256(path),path.stat().st_size))
    manifest_path=output_root/'review-artifact-manifest.json'
    try:
        write_manifest(manifest_path,ReviewManifest(tuple(sorted(files,key=lambda item:item.path))))
    except ReviewManifestError as exc:
        raise ValidationError(str(exc)) from exc
    return manifest_path


def validate(
    website_root: Path,
    lock_path: Path,
    euvics_source: Path,
    pyeuvics_source: Path,
    output_root: Path,
    quality_receipt: Path | None = None,
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
    try:
        website_before=website_identity(website_root)
        environment_before=environment_identity(website_root)
        lock_before=lock_identity(lock_path)
    except (OSError,ValueError) as exc:
        raise ValidationError(str(exc)) from exc
    epoch = _source_date_epoch(website_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.validation-", dir=output_root.parent))
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
        if quality_receipt is None:
            run_checks(website_root,workspace/'website-quality',epoch,_run)
            quality_record=workspace/'quality-record.json'
            write_receipt(quality_record,website_before,environment_before,epoch)
        else:
            verify_receipt(quality_receipt,website_before,environment_before,epoch)
            quality_record=quality_receipt
        assemble_site(website_root, lock_path, euvics_source, pyeuvics_source, assembly, source_date_epoch=epoch)
        shutil.copyfile(quality_record,assembly/"quality-record.json")
        verify_receipt(assembly/"quality-record.json",website_before,environment_before,epoch)
        write_review_manifest(assembly)
        if website_identity(website_root)!=website_before or environment_identity(website_root)!=environment_before or lock_identity(lock_path)!=lock_before:
            raise EvidenceError('validated website, environment or lock changed during execution')
        write_record(assembly/'validation-record.json',website_before,environment_before,lock_before,epoch)
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
    parser.add_argument("--quality-receipt",type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = validate(
            args.website_root,
            args.lock,
            args.euvics_source,
            args.pyeuvics_source,
            args.output,
            args.quality_receipt,
        )
    except ValidationError as exc:
        print(f"CI validation error: {exc}", file=sys.stderr)
        return 1
    print(f"review artifact manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
