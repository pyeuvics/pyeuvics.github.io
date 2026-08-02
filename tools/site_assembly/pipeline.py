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
from .documents import DocumentError, build_approved_documents
from .notebooks import (
    NotebookError,
    render_approved_notebooks,
    stage_campaign_overviews,
)
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
ARTIFACT_SUFFIXES = TEXT_SUFFIXES | {".png", ".jpg", ".jpeg", ".gif", ".gz", ".map", ".ico", ".pdf"}


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
- **Version:** {published.version}
- **Publication status:** {published.publication_status}
{f"- **Scientific validation status:** {published.validation_status}" if published.validation_status else ""}
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
    destination_overrides: dict[str, Path] | None = None,
) -> tuple[InventoryEntry, ...]:
    source_root = imported_root / contract.lock.name
    ordinary_files = tuple(item for item in contract.files if item.kind != "pdf")
    destinations = {item.path: source_root / item.path for item in ordinary_files}
    destinations.update(destination_overrides or {})
    inventory: list[InventoryEntry] = []
    for published in ordinary_files:
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


def _relative_markdown_link(source_path: str, destination: Path, imported_root: Path) -> str:
    target = imported_root / "pyeuvics" / source_path
    return os.path.relpath(target, destination.parent).replace(os.sep, "/")


def _stage_source_entry_pages(
    contracts: tuple[SourceContract, ...],
    staged_content: Path,
    imported_root: Path,
    timestamp: str,
) -> None:
    """Make website-owned entry pages reflect the validated build contents."""

    euvics = next(contract for contract in contracts if contract.lock.name == "euvics")
    pyeuvics = next(contract for contract in contracts if contract.lock.name == "pyeuvics")
    approved_markdown = {
        item.path: item for item in pyeuvics.files if Path(item.path).suffix.lower() == ".md"
    }
    versions = sorted({item.version for item in pyeuvics.files})
    statuses = sorted({item.publication_status for item in pyeuvics.files})
    limitations = sorted(
        {limitation for item in pyeuvics.files for limitation in item.known_limitations}
    )

    home = staged_content / "index.md"
    package_index = "docs/index.md"
    package_link = (
        f"[{len(pyeuvics.files)} manifest-approved pyEUVICS files]"
        f"({_relative_markdown_link(package_index, home, imported_root)})"
        if package_index in approved_markdown
        else f"{len(pyeuvics.files)} manifest-approved pyEUVICS files"
    )
    home_text = home.read_text(encoding="utf-8").rstrip()
    home.write_text(
        f"{home_text}\n\n## Approved content in this assembled build\n\n"
        f"- **pyEUVICS:** {package_link} from commit `{pyeuvics.lock.commit}`.\n"
        f"- **EUVICS documents:** {len(euvics.files)} manifest-approved files from commit "
        f"`{euvics.lock.commit}`.\n"
        f"- **Build timestamp:** {timestamp}\n",
        encoding="utf-8",
    )

    sections: tuple[tuple[str, str, tuple[str, ...]], ...] = (
        (
            "software/installation.md",
            "pyEUVICS installation",
            ("README.md", "docs/index.md", "docs/getting-started/"),
        ),
        ("software/science.md", "pyEUVICS science and conventions", ("docs/science/",)),
        ("software/api.md", "pyEUVICS API reference", ("docs/api/",)),
        ("software/tutorials.md", "pyEUVICS tutorials", ("docs/tutorials/",)),
        ("software/workflows.md", "pyEUVICS workflows", ("docs/workflows/",)),
        ("software/validation.md", "pyEUVICS validation", ("docs/validation/",)),
    )
    for destination_name, heading, prefixes in sections:
        destination = staged_content / destination_name
        selected = [
            item
            for path, item in sorted(approved_markdown.items())
            if any(path == prefix or path.startswith(prefix) for prefix in prefixes)
        ]
        links = "\n".join(
            f"- [{item.title}]({_relative_markdown_link(item.path, destination, imported_root)})"
            for item in selected
        ) or "No source documents in this section are approved by the locked manifest."
        limitations_text = (
            "\n".join(f"- {item}" for item in limitations)
            if limitations
            else "- No global limitation is recorded by the source contract."
        )
        destination.write_text(
            f"# {heading}\n\n"
            "This assembled entry page links only to documentation authorized by the "
            "locked pyEUVICS publication contract. Scientific and software corrections "
            "belong in the authoritative source repository.\n\n"
            "## Build provenance\n\n"
            f"- **Source commit:** `{pyeuvics.lock.commit}`\n"
            f"- **Package version:** {', '.join(versions) if versions else 'No approved version'}\n"
            f"- **Publication status:** {', '.join(statuses) if statuses else 'No approved status'}\n"
            f"- **Build timestamp:** {timestamp}\n\n"
            "## Approved documentation\n\n"
            f"{links}\n\n"
            "## Known limitations\n\n"
            f"{limitations_text}\n",
            encoding="utf-8",
        )


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
    euvics_contract = next(contract for contract in contracts if contract.lock.name == "euvics")
    try:
        document_entries, document_destinations = build_approved_documents(
            euvics_contract,
            output_root,
            staged_content,
            timestamp,
        )
    except DocumentError as exc:
        raise AssemblyError(str(exc)) from exc
    imported_root = staged_content / "imported"
    imported_root.mkdir()
    ordinary_entries = tuple(
        sorted(
            (
                item
                for contract in contracts
                for item in _copy_contract(
                    contract,
                    imported_root,
                    timestamp,
                    document_destinations if contract.lock.name == "euvics" else None,
                )
            ),
            key=lambda item: (item.source, item.source_path),
        )
    )
    pyeuvics_contract = next(
        contract for contract in contracts if contract.lock.name == "pyeuvics"
    )
    try:
        notebook_entries = render_approved_notebooks(
            pyeuvics_contract,
            output_root,
            staged_content,
            timestamp,
        )
        stage_campaign_overviews(pyeuvics_contract, staged_content, timestamp)
    except NotebookError as exc:
        raise AssemblyError(str(exc)) from exc
    _stage_source_entry_pages(contracts, staged_content, imported_root, timestamp)
    entries = tuple(
        sorted(
            (*ordinary_entries, *document_entries, *notebook_entries),
            key=lambda item: (item.source, item.source_path),
        )
    )
    inventory_path = output_root / "staged-content-inventory.json"
    _write_inventory(inventory_path, contracts, entries, timestamp)
    shutil.copyfile(inventory_path, imported_root / "staged-content-inventory.json")
    site = _build_site(website_root, output_root)
    _scan_artifact(site)
    return AssemblyResult(output_root, staged_content, site, entries)
