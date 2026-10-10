"""Deterministic staging, link rewriting, inventory, build, and artifact scans."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit

import yaml

from tools.privacy import PrivacyError, ScanProfile, scan_file, scan_text

from .assets import validate_asset
from .content_policy import (
    ContentPolicyError,
    parse_fragment,
)
from .content_policy import (
    RenderedLinkParser as _RenderedLinkParser,
)
from .content_policy import (
    css_targets as _css_targets,
)
from .content_policy import (
    srcset_targets as _srcset_targets,
)
from .context import BuildContext, BuildInputs
from .contracts import ContractError, load_contract, load_locks, verify_contract_inputs
from .documents import DocumentError, build_approved_documents
from .entry_pages import stage_source_entry_pages
from .links import LinkRewriteError, RenderedLinks, rewrite_destinations
from .models import AssemblyResult as AssemblyResult  # noqa: PLC0414
from .models import InventoryEntry, PublishedFile, SourceContract
from .notebooks import (
    NotebookError,
    render_approved_notebooks,
    stage_campaign_overviews,
)
from .overview_figures import OverviewFigureError, stage_overview_figure
from .ownership import RenderedBuild, plan_artifact, stage_receipt, verify_ownership
from .page_actions import correction_url, page_actions
from .presentation import (
    Code,
    Link,
    MetadataRow,
    markdown_text,
    render_fields,
    render_limitations,
    render_link,
    source_url,
)
from .primitives import atomic_write_text, run_text, sha256_file
from .promotion import promote_directory
from .publication_pages import stage_publication_indexes
from .rendering import (
    MarkdownRenderer,
    RenderingError,
    final_relative_url,
    load_renderer,
)
from .staging import StagingError, StagingPlan, create_staging_plan
from .template_slots import TemplateSlotError
from .timestamps import TimestampError, parse_timestamp

TEXT_SUFFIXES = {
    "",
    ".md",
    ".svg",
    ".css",
    ".js",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".txt",
    ".cff",
    ".html",
    ".xml",
    ".tex",
    ".bib",
}
ARTIFACT_SUFFIXES = TEXT_SUFFIXES | {".png", ".jpg", ".jpeg", ".gif", ".gz", ".map", ".ico", ".pdf"}


class AssemblyError(ValueError):
    """The website assembly could not be completed safely."""


_sha256 = sha256_file


def _build_timestamp(value: str | None = None) -> str:
    try:
        return parse_timestamp(value if value is not None else os.environ.get("SOURCE_DATE_EPOCH")).iso
    except TimestampError as exc:
        raise AssemblyError(str(exc)) from exc


def _scan_text(text: str, label: str) -> None:
    try:
        scan_text(text, label, ScanProfile.SOURCE)
    except PrivacyError as exc:
        raise AssemblyError(str(exc)) from exc


def _source_url(contract: SourceContract, path: str, *, edit: bool = False, directory: bool = False) -> str:
    return source_url(contract.lock, path, edit=edit, directory=directory)


def _local_link_parts(target: str) -> tuple[str, str] | None:
    parsed = urlsplit(target.strip())
    if parsed.scheme.lower() in {
        "data", "ftp", "ftps", "http", "https", "mailto", "tel"
    } or parsed.netloc or not parsed.path:
        return None
    if parsed.scheme:
        raise AssemblyError(f"unsafe or unsupported link scheme: {target}")
    path = unquote(parsed.path)
    suffix = f"?{parsed.query}" if parsed.query else ""
    if parsed.fragment:
        suffix += f"#{parsed.fragment}"
    return path, suffix


def _resolve_source_target(source_path: str, target: str) -> tuple[str, str]:
    parts = _local_link_parts(target)
    if parts is None:
        raise AssemblyError(f"link is not a local path in {source_path}: {target}")
    path_part, suffix = parts
    if path_part.startswith("/"):
        raise AssemblyError(f"unsafe root/local link in {source_path}: {target}")
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
    return "/".join(normalized), suffix


def _inspect_links(text: str, renderer: MarkdownRenderer) -> RenderedLinks:
    rendered, managed = renderer.inspect(text)
    try:
        parser = parse_fragment(rendered)
    except ContentPolicyError as exc:
        raise AssemblyError(str(exc)) from exc
    return RenderedLinks(tuple(parser.targets), managed)


def _validate_rendered_links(
    text: str,
    published: PublishedFile,
    destinations: dict[str, Path],
    renderer: MarkdownRenderer | None = None,
) -> RenderedLinks:
    """Validate the parsed destinations used by source-span transformation."""
    try:
        document = _inspect_links(text, renderer or load_renderer())
    except RenderingError as exc:
        raise AssemblyError(str(exc)) from exc
    for target in document.targets:
        if _local_link_parts(target) is None:
            continue
        resolved, _ = _resolve_source_target(published.path, target)
        if resolved not in destinations:
            raise AssemblyError(f"broken or unpublished link in {published.path}: {target}")
    return document


def _rewrite_markdown(
    text: str,
    published: PublishedFile,
    contract: SourceContract,
    destinations: dict[str, Path],
    destination: Path,
    timestamp: str,
    source_sha256: str,
    renderer: MarkdownRenderer | None = None,
) -> str:
    _scan_text(text, f"source Markdown {contract.lock.name}:{published.path}")
    renderer = renderer or load_renderer()
    document = _validate_rendered_links(text, published, destinations, renderer)
    replacements: dict[str, tuple[str, str]] = {}
    for target in document.targets:
        if _local_link_parts(target) is None:
            continue
        resolved, suffix = _resolve_source_target(published.path, target)
        # Encode delimiter characters before inserting into either Markdown or
        # HTML; entity escaping is handled by the source-span transformer.
        suffix = quote(suffix, safe="/?#:@-._~!$&*+,;=%")
        mapped = destinations[resolved]
        relative = os.path.relpath(mapped, destination.parent).replace(os.sep, "/")
        replacements[target] = (
            quote(relative, safe="/._-") + suffix,
            final_relative_url(mapped, destination) + suffix,
        )
    try:
        rewritten = rewrite_destinations(
            text, document, replacements, lambda value: _inspect_links(value, renderer)
        ).rstrip() + "\n"
    except LinkRewriteError as exc:
        raise AssemblyError(f"cannot rewrite links in {published.path}: {exc}") from exc
    fields = [
        MetadataRow("Source", Link(published.path, _source_url(contract, published.path), contract.lock.commit)),
        MetadataRow("Source corrections", Link("Propose a source correction", correction_url(contract.lock.repository, _source_url(contract, published.path)))),
        MetadataRow("Repository", Link(contract.lock.repository, contract.lock.repository)),
        MetadataRow("Version", published.version),
        MetadataRow("Publication status", published.publication_status),
    ]
    if published.validation_status:
        fields.append(MetadataRow("Scientific validation status", published.validation_status))
    fields.extend((
        MetadataRow("Source SHA-256", Code(source_sha256)),
        MetadataRow("License", published.license),
        MetadataRow("Attribution", published.attribution),
        MetadataRow("Website build timestamp", timestamp),
    ))
    provenance = "\n\n---\n\n## Provenance\n\n" + render_fields(tuple(fields))
    provenance += "\n\n### Known limitations\n\n" + render_limitations(published.known_limitations) + "\n"
    return rewritten + provenance


def _copy_contract(
    contract: SourceContract,
    imported_root: Path,
    timestamp: str,
    destination_overrides: dict[str, Path] | None = None,
    renderer: MarkdownRenderer | None = None,
) -> tuple[InventoryEntry, ...]:
    try:
        verify_contract_inputs(contract)
    except ContractError as exc:
        raise AssemblyError(str(exc)) from exc
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
            try:
                source_text = source.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise AssemblyError(f"cannot inspect source Markdown {published.path}") from exc
            rewritten = _rewrite_markdown(
                source_text,
                published,
                contract,
                destinations,
                destination,
                timestamp,
                source_sha256,
                renderer,
            )
            destination.write_text(rewritten, encoding="utf-8")
        else:
            validate_asset(source, relative=published.path, approved=frozenset(item.path for item in ordinary_files if item.path in destinations and destinations[item.path] == source_root / item.path and Path(item.path).suffix.lower() != ".md"))
            if source.suffix.lower() in TEXT_SUFFIXES:
                try:
                    scan_file(source, f"source asset {published.path}", ScanProfile.SOURCE)
                except PrivacyError as exc:
                    raise AssemblyError(str(exc)) from exc
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
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _configure_site(website_root: Path, output_root: Path, plan: StagingPlan | None = None) -> Path:
    config = yaml.safe_load((website_root / "mkdocs.yml").read_text(encoding="utf-8"))
    shutil.copytree(website_root / "overrides", output_root / "overrides")
    config["docs_dir"] = "content"
    config["site_dir"] = "site"
    config["not_in_nav"] = "/imported/**"
    config["theme"]["custom_dir"] = "overrides"
    if plan is not None:
        revision=run_text(["git","rev-parse","HEAD"],website_root,"website action revision").strip()
        config.setdefault("extra",{})["publication_pages"]=page_actions(plan,revision)
    config_path = output_root / "mkdocs.yml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path


def _build_site(website_root: Path, output_root: Path, source_date_epoch: str | None = None) -> Path:
    config_path = output_root / "mkdocs.yml"
    if not config_path.exists():
        _configure_site(website_root, output_root)
    environment = dict(os.environ)
    if source_date_epoch is not None:
        environment["SOURCE_DATE_EPOCH"] = source_date_epoch
    try:
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--strict", "--config-file", str(config_path)],
            cwd=output_root,
            check=True,
            env=environment,
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
                scan_file(path, f"artifact {path.relative_to(site)}", ScanProfile.PUBLIC)
            except PrivacyError as exc:
                raise AssemblyError(str(exc)) from exc


def _prepare_build(
    website_root: Path, lock_path: Path, euvics_source: Path, pyeuvics_source: Path,
    output_root: Path, source_date_epoch: str | None,
) -> BuildInputs:
    if output_root.exists() or output_root.is_symlink():
        raise AssemblyError(f"output path already exists: {output_root}")
    website_root = website_root.resolve()
    output_root = output_root.resolve()
    source_roots = {"euvics": euvics_source.resolve(), "pyeuvics": pyeuvics_source.resolve()}
    if output_root.exists():
        raise AssemblyError(f"output path already exists: {output_root}")
    if output_root in {website_root, *source_roots.values()} or any(
        root in output_root.parents for root in source_roots.values()
    ):
        raise AssemblyError("output path must not be a repository or lie inside a source checkout")
    try:
        timestamp = parse_timestamp(source_date_epoch if source_date_epoch is not None else os.environ.get("SOURCE_DATE_EPOCH"))
    except TimestampError as exc:
        raise AssemblyError(str(exc)) from exc
    try:
        renderer = load_renderer(website_root)
    except RenderingError as exc:
        raise AssemblyError(str(exc)) from exc
    try:
        locks = load_locks(lock_path)
        contracts = tuple(
            load_contract(locks[name], source_roots[name]) for name in ("euvics", "pyeuvics")
        )
    except ContractError as exc:
        raise AssemblyError(str(exc)) from exc
    try:
        plan = create_staging_plan(website_root, contracts)
    except StagingError as exc:
        raise AssemblyError(str(exc)) from exc
    return BuildInputs(website_root, output_root, timestamp, contracts, plan, renderer)


def _materialize_build(context: BuildContext) -> tuple[InventoryEntry, ...]:
    website_root = context.inputs.website_root
    output_root = context.workspace
    contracts = context.inputs.contracts
    timestamp = context.inputs.timestamp.iso
    plan = context.inputs.plan
    renderer = context.inputs.renderer
    atomic_write_text(output_root / "staging-plan.json", json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n")
    staged_content = output_root / "content"
    shutil.copytree(website_root / "content", staged_content)
    euvics_contract = next(contract for contract in contracts if contract.lock.name == "euvics")
    try:
        document_entries, _ = build_approved_documents(
            euvics_contract,
            output_root,
            staged_content,
            timestamp,
            plan,
            context.inputs.timestamp.epoch,
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
                    plan.source_destinations(contract.lock.name, staged_content),
                    renderer,
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
            plan,
        )
        stage_campaign_overviews(next(item for item in plan.publication if item.lock.name=="pyeuvics"), staged_content, timestamp)
        stage_overview_figure(pyeuvics_contract, staged_content)
    except (NotebookError, OverviewFigureError, StagingError, TemplateSlotError) as exc:
        raise AssemblyError(str(exc)) from exc
    stage_source_entry_pages(plan.publication, staged_content, imported_root, timestamp)
    entries = tuple(
        sorted(
            (*ordinary_entries, *document_entries, *notebook_entries),
            key=lambda item: (item.source, item.source_path),
        )
    )
    stage_publication_indexes(plan.publication, entries, staged_content, timestamp)
    inventory_path = output_root / "staged-content-inventory.json"
    _write_inventory(inventory_path, contracts, entries, timestamp)
    shutil.copyfile(inventory_path, imported_root / "staged-content-inventory.json")
    return entries


def _render_build(context: BuildContext, entries: tuple[InventoryEntry, ...]) -> RenderedBuild:
    staged = stage_receipt(context, entries)
    _configure_site(context.inputs.website_root, context.workspace, context.inputs.plan)
    artifact = plan_artifact(context, staged)
    site = _build_site(context.inputs.website_root, context.workspace, context.inputs.timestamp.epoch)
    return RenderedBuild(site, artifact)


def _verify_build(context: BuildContext, rendered: RenderedBuild) -> None:
    verify_ownership(context, rendered)
    for item in rendered.plan.files:
        if Path(item.path).suffix != ".html":
            validate_asset(rendered.site / item.path, origin=item.origin, relative=item.path, approved=frozenset(entry.path for entry in rendered.plan.files))
    _scan_artifact(rendered.site)
    for contract in context.inputs.contracts:
        verify_contract_inputs(contract)


def _finalize_build(context: BuildContext, entries: tuple[InventoryEntry, ...]) -> AssemblyResult:
    destination = context.inputs.requested_output
    promote_directory(context.workspace, destination)
    return AssemblyResult(destination, destination / "content", destination / "site", entries)


def assemble_site(
    website_root: Path,
    lock_path: Path,
    euvics_source: Path,
    pyeuvics_source: Path,
    output_root: Path,
    *,
    source_date_epoch: str | None = None,
) -> AssemblyResult:
    """Plan, materialize, render, verify and exclusively promote one owned build."""
    try:
        prepared = _prepare_build(website_root, lock_path, euvics_source, pyeuvics_source, output_root, source_date_epoch)
    except (OSError, ValueError) as exc:
        raise AssemblyError(str(exc)) from exc
    prepared.requested_output.parent.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f".{prepared.requested_output.name}.assembly-", dir=prepared.requested_output.parent))
    context = BuildContext(prepared, workspace)
    phase = "materialize"
    try:
        entries = _materialize_build(context)
        phase = "render"
        rendered = _render_build(context, entries)
        phase = "verify"
        _verify_build(context, rendered)
        phase = "finalize"
        return _finalize_build(context, entries)
    except BaseException as exc:
        # This path is uniquely owned by this invocation. Never clean a caller's
        # requested directory or serialize exception contents into diagnostics.
        try:
            atomic_write_text(workspace / "INCOMPLETE.json", json.dumps({"status": "incomplete", "phase": phase, "error_type": type(exc).__name__}, sort_keys=True) + "\n")
        except OSError:
            pass  # Preserve the original error and the owned workspace.
        if not isinstance(exc, Exception):
            raise
        raise AssemblyError(f"{exc}; incomplete {phase} workspace retained at {workspace}") from exc
