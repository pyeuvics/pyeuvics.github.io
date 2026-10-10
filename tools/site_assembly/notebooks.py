"""Coordinate two independent executions and stage deterministic notebooks."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .primitives import FileOperationError, atomic_write_text, export_locked_tree, sha256_file
from .contracts import ContractError, verify_contract_inputs
from .models import InventoryEntry, NotebookSpec, SourceContract
from .staging import StagingPlan, notebook_page
from .presentation import Link, render_link
from .notebook_policy import NotebookError as NotebookError, RenderedNotebook, _scan as _scan
from .notebook_admission import admit_notebook, _validate_source as _validate_source
from .notebook_execution import execute_notebook
from .notebook_rendering import render_executed, _page_header as _page_header
from .campaign_pages import stage_campaign_overviews as stage_campaign_overviews

def _archive_checkout(contract: SourceContract, destination: Path) -> None:
    try:
        export_locked_tree(contract.root, contract.lock.commit, destination)
    except FileOperationError as exc:
        raise NotebookError(f"cannot archive locked pyEUVICS source: {exc}") from exc


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


_sha256 = sha256_file



def _render_once(spec: NotebookSpec, source_root: Path) -> RenderedNotebook:
    result = render_executed(execute_notebook(admit_notebook(spec,source_root)))
    return result


def render_approved_notebooks(
    contract: SourceContract,
    output_root: Path,
    staged_content: Path,
    timestamp: str,
    plan: StagingPlan | None = None,
) -> tuple[InventoryEntry, ...]:
    """Execute every approved notebook twice and stage deterministic Markdown."""

    inventory: list[InventoryEntry] = []
    if not contract.notebooks:
        return ()
    try:
        verify_contract_inputs(contract)
    except ContractError as exc:
        raise NotebookError(str(exc)) from exc
    source_build = output_root / "source-build/pyeuvics-notebooks"
    _archive_checkout(contract, source_build)
    index_links: list[str] = []
    provenance: list[dict[str, object]] = []
    for spec in contract.notebooks:
        source = contract.root / spec.path
        source_before = source.read_bytes()
        first = _render_once(spec, source_build)
        second = _render_once(spec, source_build)
        first_body, first_assets = first.body, first.assets
        if first.body != second.body or first.assets != second.assets or first.environment != second.environment:
            raise NotebookError(f"notebook rendering is nondeterministic: {spec.path}")
        if source.read_bytes() != source_before:
            raise NotebookError(f"source notebook changed during rendering: {spec.path}")
        if first.environment is None:raise NotebookError('notebook environment provenance is missing')
        provenance.append({'notebook':spec.path,'source_commit':contract.lock.commit,'source_sha256':_sha256_bytes(source_before),'matching_executions':2,'environment':first.environment.to_dict(),'environment_sha256':first.environment.fingerprint})
        stem = Path(spec.path).stem
        relative_page = Path(notebook_page(spec.path))
        if plan is not None:
            relative_page = plan.source_destinations(contract.lock.name, staged_content)[spec.path].relative_to(staged_content)
            plan.emitted_assets(contract.lock.name, tuple((relative_page.parent / name).as_posix() for name in first_assets))
        page = staged_content / relative_page
        page.parent.mkdir(parents=True, exist_ok=True)
        rendered = _page_header(spec, contract, timestamp, first.environment.fingerprint) + first_body
        page.write_text(rendered, encoding="utf-8")
        inventory.append(
            InventoryEntry(
                contract.lock.name,
                spec.path,
                relative_page.as_posix(),
                _sha256_bytes(source_before),
                _sha256(page),
                spec.publication_status,
                spec.known_limitations,
            )
        )
        for name, value in sorted(first_assets.items()):
            asset = page.parent / name
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.write_bytes(value)
            inventory.append(
                InventoryEntry(
                    contract.lock.name,
                    f"{spec.path}#output:{name}",
                    asset.relative_to(staged_content).as_posix(),
                    _sha256_bytes(value),
                    _sha256_bytes(value),
                    spec.publication_status,
                    spec.known_limitations,
                )
            )
        index_links.append("- " + render_link(Link(spec.title, f"{stem}.md")))
    index = staged_content / "software/notebooks/index.md"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(
        "# Static pyEUVICS notebooks\n\n"
        "These pages are deterministic static renderings, not an interactive Jupyter environment.\n\n"
        + "\n".join(index_links)
        + "\n",
        encoding="utf-8",
    )
    atomic_write_text(output_root/"notebook-execution-provenance.json",json.dumps({"notebook_execution_version":1,"notebooks":provenance},indent=2,sort_keys=True)+"\n")
    return tuple(inventory)
