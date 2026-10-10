"""Coordinate two independent executions and stage deterministic notebooks."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .campaign_pages import stage_campaign_overviews as stage_campaign_overviews
from .contracts import ContractError, verify_contract_inputs
from .models import InventoryEntry, NotebookSpec, SourceContract
from .notebook_admission import _validate_source as _validate_source
from .notebook_admission import admit_notebook
from .notebook_execution import _tree_snapshot, execute_notebook
from .notebook_policy import NotebookError as NotebookError
from .notebook_policy import RenderedNotebook
from .notebook_policy import _scan as _scan
from .notebook_rendering import _page_header as _page_header
from .notebook_rendering import render_executed
from .primitives import (
    FileOperationError,
    atomic_write_text,
    export_locked_tree,
    sha256_file,
)
from .staging import StagingPlan, notebook_page


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
    pristine = _tree_snapshot(source_build)
    provenance: list[dict[str, object]] = []
    for spec in contract.notebooks:
        source = contract.root / spec.path
        source_before = source.read_bytes()
        runs: list[RenderedNotebook] = []
        for number in (1,2):
            run_source=output_root/'source-build/notebook-runs'/Path(spec.path).stem/f'run-{number}'/'source'
            shutil.copytree(source_build,run_source)
            runs.append(_render_once(spec,run_source))
            if _tree_snapshot(source_build)!=pristine:raise NotebookError('notebook modified the pristine build source')
        first,second=runs
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
    atomic_write_text(output_root/"notebook-execution-provenance.json",json.dumps({"notebook_execution_version":1,"notebooks":provenance},indent=2,sort_keys=True)+"\n")
    return tuple(inventory)
