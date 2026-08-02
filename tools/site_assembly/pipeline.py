"""Deterministic staging, link rewriting, inventory, build, and artifact scans."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote

import yaml

from .contracts import ContractError, load_contract, load_locks
from .models import AssemblyResult as AssemblyResult
from .models import InventoryEntry, PublishedFile, SourceContract

LOCAL_PATH_RE = re.compile(r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\\\)")
LINK_RE = re.compile(r"(?P<prefix>!?\[[^\]]*\]\()(?P<target>[^)\s]+)(?P<suffix>[^)]*\))")
CREDENTIAL_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b"),
)
TEXT_SUFFIXES = {"", ".md", ".svg", ".css", ".js", ".json", ".csv", ".yaml", ".yml", ".txt", ".cff", ".html", ".xml"}
ARTIFACT_SUFFIXES = TEXT_SUFFIXES | {".png", ".jpg", ".jpeg", ".gif", ".gz", ".map", ".ico"}


class AssemblyError(ValueError):
    """The website assembly could not be completed safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _build_timestamp() -> str:
    value = os.environ.get("SOURCE_DATE_EPOCH")
    if value is None:
        raise AssemblyError("SOURCE_DATE_EPOCH is required for deterministic assembly")
    try:
        instant = dt.datetime.fromtimestamp(int(value), tz=dt.timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise AssemblyError("SOURCE_DATE_EPOCH must be a valid integer timestamp") from exc
    return instant.isoformat().replace("+00:00", "Z")


def _scan_text(text: str, label: str) -> None:
    if LOCAL_PATH_RE.search(text):
        raise AssemblyError(f"local absolute path detected in {label}")
    for pattern in CREDENTIAL_PATTERNS:
        if pattern.search(text):
            raise AssemblyError(f"credential-like material detected in {label}")


def _source_url(contract: SourceContract, path: str, *, edit: bool = False, directory: bool = False) -> str:
    action = "edit" if edit else ("tree" if directory else "blob")
    return f"{contract.lock.repository}/{action}/{contract.lock.commit}/{quote(path)}"


def _resolve_source_target(source_path: str, target: str) -> tuple[str, str]:
    decoded = unquote(target)
    path_part, separator, fragment = decoded.partition("#")
    base = PurePosixPath(source_path).parent
    resolved = base.joinpath(path_part)
    normalized: list[str] = []
    for part in resolved.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not normalized:
                raise AssemblyError(f"link escapes source root in {source_path}: {target}")
            normalized.pop()
        else:
            normalized.append(part)
    return "/".join(normalized), f"#{fragment}" if separator else ""


def _rewrite_markdown(
    text: str,
    published: PublishedFile,
    contract: SourceContract,
    destinations: dict[str, Path],
    destination: Path,
    timestamp: str,
    source_sha256: str,
) -> str:
    _scan_text(text, f"source Markdown {contract.lock.name}:{published.path}")

    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        if target.startswith(("#", "http://", "https://", "mailto:", "data:")):
            return match.group(0)
        if target.startswith(("/", "file:")):
            raise AssemblyError(f"unsafe root/local link in {published.path}: {target}")
        resolved, fragment = _resolve_source_target(published.path, target)
        source_target = contract.root / resolved
        if resolved in destinations:
            relative = os.path.relpath(destinations[resolved], destination.parent).replace(os.sep, "/")
            rewritten = quote(relative, safe="/._-") + fragment
        elif source_target.exists() and contract.rewrite_unpublished_links:
            rewritten = _source_url(contract, resolved, directory=source_target.is_dir()) + fragment
        else:
            raise AssemblyError(f"broken or unpublished link in {published.path}: {target}")
        return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

    rewritten = LINK_RE.sub(replace, text).rstrip() + "\n"
    limitations = (
        "\n".join(f"- {item}" for item in published.known_limitations)
        if published.known_limitations
        else "- None recorded by the source contract."
    )
    provenance = f"""

---

## Provenance

- **Source:** [{published.path} at `{contract.lock.commit}`]({_source_url(contract, published.path)})
- **Edit in source repository:** [Propose a source change]({_source_url(contract, published.path, edit=True)})
- **Repository:** [{contract.lock.repository}]({contract.lock.repository})
- **Publication status:** {published.publication_status}
- **Source SHA-256:** `{source_sha256}`
- **Website build timestamp:** {timestamp}

### Known limitations

{limitations}
"""
    return rewritten + provenance


def _copy_contract(
    contract: SourceContract,
    imported_root: Path,
    timestamp: str,
) -> tuple[InventoryEntry, ...]:
    source_root = imported_root / contract.lock.name
    destinations = {item.path: source_root / item.path for item in contract.files}
    inventory: list[InventoryEntry] = []
    for published in contract.files:
        source = contract.root / published.path
        source_sha256 = _sha256(source)
        destination = destinations[published.path]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".md":
            rewritten = _rewrite_markdown(
                source.read_text(encoding="utf-8"),
                published,
                contract,
                destinations,
                destination,
                timestamp,
                source_sha256,
            )
            destination.write_text(rewritten, encoding="utf-8")
        else:
            if source.suffix.lower() in TEXT_SUFFIXES:
                _scan_text(source.read_text(encoding="utf-8"), f"source asset {published.path}")
            shutil.copyfile(source, destination)
        inventory.append(
            InventoryEntry(
                contract.lock.name,
                published.path,
                destination.relative_to(imported_root.parent).as_posix(),
                source_sha256,
                _sha256(destination),
                published.publication_status,
                published.known_limitations,
            )
        )
    actual = {
        path.relative_to(imported_root.parent).as_posix()
        for path in source_root.rglob("*")
        if path.is_file()
    }
    expected = {item.staged_path for item in inventory}
    if actual != expected:
        raise AssemblyError(
            f"staged inventory mismatch for {contract.lock.name}: "
            f"unknown={sorted(actual - expected)}, missing={sorted(expected - actual)}"
        )
    return tuple(inventory)


def _write_inventory(
    path: Path,
    contracts: tuple[SourceContract, ...],
    entries: tuple[InventoryEntry, ...],
    timestamp: str,
) -> None:
    payload = {
        "inventory_version": 1,
        "build_timestamp": timestamp,
        "sources": {
            contract.lock.name: {
                "repository": contract.lock.repository,
                "commit": contract.lock.commit,
                "publication_manifest": contract.lock.manifest_path,
            }
            for contract in contracts
        },
        "files": [
            {
                "source": item.source,
                "source_path": item.source_path,
                "staged_path": item.staged_path,
                "source_sha256": item.source_sha256,
                "staged_sha256": item.staged_sha256,
                "publication_status": item.publication_status,
                "known_limitations": list(item.known_limitations),
            }
            for item in entries
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_site(website_root: Path, output_root: Path) -> Path:
    config = yaml.safe_load((website_root / "mkdocs.yml").read_text(encoding="utf-8"))
    shutil.copytree(website_root / "overrides", output_root / "overrides")
    config["docs_dir"] = "content"
    config["site_dir"] = "site"
    config["not_in_nav"] = "/imported/**"
    config["theme"]["custom_dir"] = "overrides"
    config_path = output_root / "mkdocs.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    try:
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--strict", "--config-file", str(config_path)],
            cwd=output_root,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise AssemblyError("strict MkDocs build failed") from exc
    return output_root / "site"


def _scan_artifact(site: Path) -> None:
    if not site.is_dir() or not (site / "index.html").is_file():
        raise AssemblyError("MkDocs artifact is incomplete")
    for path in site.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ARTIFACT_SUFFIXES:
            raise AssemblyError(f"unexpected final artifact type: {path.relative_to(site)}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise AssemblyError(f"non-UTF-8 text artifact: {path.relative_to(site)}") from exc
            _scan_text(text, f"artifact {path.relative_to(site)}")


def assemble_site(
    website_root: Path,
    lock_path: Path,
    euvics_source: Path,
    pyeuvics_source: Path,
    output_root: Path,
) -> AssemblyResult:
    """Assemble approved source files into a new output tree and build strictly."""

    website_root = website_root.resolve()
    output_root = output_root.resolve()
    source_roots = {"euvics": euvics_source.resolve(), "pyeuvics": pyeuvics_source.resolve()}
    if output_root.exists():
        raise AssemblyError(f"output path already exists: {output_root}")
    if output_root in {website_root, *source_roots.values()} or any(
        root in output_root.parents for root in source_roots.values()
    ):
        raise AssemblyError("output path must not be a repository or lie inside a source checkout")
    timestamp = _build_timestamp()
    try:
        locks = load_locks(lock_path)
        contracts = tuple(
            load_contract(locks[name], source_roots[name]) for name in ("euvics", "pyeuvics")
        )
    except ContractError as exc:
        raise AssemblyError(str(exc)) from exc
    output_root.mkdir(parents=True)
    staged_content = output_root / "content"
    shutil.copytree(website_root / "content", staged_content)
    imported_root = staged_content / "imported"
    imported_root.mkdir()
    entries = tuple(
        sorted(
            (
                item
                for contract in contracts
                for item in _copy_contract(contract, imported_root, timestamp)
            ),
            key=lambda item: (item.source, item.source_path),
        )
    )
    inventory_path = output_root / "staged-content-inventory.json"
    _write_inventory(inventory_path, contracts, entries, timestamp)
    shutil.copyfile(inventory_path, imported_root / "staged-content-inventory.json")
    site = _build_site(website_root, output_root)
    _scan_artifact(site)
    return AssemblyResult(output_root, staged_content, site, entries)
