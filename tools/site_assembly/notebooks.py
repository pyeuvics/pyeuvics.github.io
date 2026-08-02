"""Execute and render explicitly approved pyEUVICS notebooks."""

from __future__ import annotations

import hashlib
import io
import os
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from nbconvert import MarkdownExporter

from .models import InventoryEntry, NotebookSpec, SourceContract

LOCAL_PATH = re.compile(r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\)")
SECRET = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
DATA_LITERAL = re.compile(
    r"[\"']([^\"']+\.(?:csv|json|ya?ml|npy|npz|h5|hdf5|parquet|dat|txt))[\"']",
    re.IGNORECASE,
)
NETWORK_CODE = re.compile(r"\b(?:requests\.|httpx\.|urlopen\s*\(|socket\.|wget\b|curl\b)")
UNSAFE_HTML = re.compile(r"<(?:script|iframe)\b|javascript:", re.IGNORECASE)
SAFE_OUTPUT_MIMES = {"text/plain", "text/markdown", "image/png", "image/jpeg"}


class NotebookError(ValueError):
    """An approved notebook cannot be safely rendered."""


def _archive_checkout(contract: SourceContract, destination: Path) -> None:
    try:
        archive = subprocess.check_output(
            ["git", "archive", "--format=tar", contract.lock.commit],
            cwd=contract.root,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise NotebookError(f"cannot archive locked pyEUVICS source: {exc.output.decode(errors='replace')}") from exc
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise NotebookError(f"unsafe member in locked pyEUVICS archive: {member.name}")
        stream.extractall(destination, filter="data")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _scan(value: str, label: str) -> None:
    if LOCAL_PATH.search(value):
        raise NotebookError(f"absolute local path in {label}")
    if SECRET.search(value):
        raise NotebookError(f"credential-like value in {label}")


def _validate_source(spec: NotebookSpec, source: Path, root: Path) -> Any:
    raw = source.read_bytes()
    if len(raw) > spec.max_source_bytes:
        raise NotebookError(f"notebook exceeds source size limit: {spec.path}")
    try:
        text = raw.decode("utf-8")
        notebook = nbformat.reads(text, as_version=4)  # type: ignore[no-untyped-call]
    except (UnicodeDecodeError, ValueError) as exc:
        raise NotebookError(f"invalid UTF-8 notebook: {spec.path}") from exc
    _scan(text, f"source notebook {spec.path}")
    if UNSAFE_HTML.search(text):
        raise NotebookError(f"unsafe active content in source notebook: {spec.path}")
    for dependency in spec.dependencies:
        dependency_path = root / dependency
        if dependency_path.suffix.lower() in {".csv", ".json", ".yaml", ".yml", ".txt"}:
            try:
                dependency_text = dependency_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise NotebookError(f"approved text dependency is not UTF-8: {dependency}") from exc
            _scan(dependency_text, f"notebook dependency {dependency}")
    for cell in notebook.cells:
        if cell.cell_type == "code" and (cell.get("outputs") or cell.get("execution_count") is not None):
            raise NotebookError(f"source notebook contains outputs or execution counts: {spec.path}")
        if cell.cell_type == "code" and NETWORK_CODE.search(str(cell.get("source", ""))):
            raise NotebookError(f"network-dependent code is not approved for static execution: {spec.path}")
    approved = set(spec.dependencies)
    for raw_path in DATA_LITERAL.findall(text):
        candidate = PurePosixPath(raw_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise NotebookError(f"unsafe data dependency in notebook {spec.path}: {raw_path}")
        root_relative = candidate.as_posix()
        notebook_relative = (PurePosixPath(spec.path).parent / candidate).as_posix()
        relative = root_relative if (root / root_relative).exists() else notebook_relative
        if (root / relative).exists() and relative not in approved:
            raise NotebookError(f"unapproved data dependency in notebook {spec.path}: {relative}")
    return notebook


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def _render_once(spec: NotebookSpec, source_root: Path) -> tuple[str, dict[str, bytes]]:
    source = source_root / spec.path
    notebook = _validate_source(spec, source, source_root)
    before = _tree_snapshot(source_root)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    source_path = source_root / "src"
    if source_path.is_dir():
        environment["PYTHONPATH"] = str(source_path)
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        allow_errors=False,
        record_timing=False,
    )
    try:
        executed = client.execute(cwd=str(source_root), env=environment)
    except (CellExecutionError, TimeoutError, RuntimeError, OSError) as exc:
        raise NotebookError(f"notebook execution failed: {spec.path}: {exc}") from exc
    after = _tree_snapshot(source_root)
    if after != before:
        raise NotebookError(f"notebook execution modified its temporary source tree: {spec.path}")
    for cell in executed.cells:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            if isinstance(data, dict):
                unexpected_mimes = set(data) - SAFE_OUTPUT_MIMES
                if unexpected_mimes:
                    raise NotebookError(
                        f"unsafe or unsupported notebook output MIME types in {spec.path}: "
                        f"{sorted(unexpected_mimes)}"
                    )
    exporter = MarkdownExporter()  # type: ignore[no-untyped-call]
    asset_directory = f"{Path(spec.path).stem}_files"
    body, resources = exporter.from_notebook_node(
        executed,
        resources={"output_files_dir": asset_directory},
    )
    raw_outputs = resources.get("outputs", {})
    if not isinstance(raw_outputs, dict):
        raise NotebookError(f"invalid rendered output resources: {spec.path}")
    outputs: dict[str, bytes] = {}
    for name, value in raw_outputs.items():
        pure = PurePosixPath(str(name))
        if pure.is_absolute() or ".." in pure.parts or not isinstance(value, bytes):
            raise NotebookError(f"unsafe rendered notebook asset: {name}")
        outputs[pure.as_posix()] = value
    _scan(body, f"rendered notebook {spec.path}")
    if UNSAFE_HTML.search(body):
        raise NotebookError(f"unsafe active content in rendered notebook: {spec.path}")
    total_size = len(body.encode("utf-8")) + sum(len(value) for value in outputs.values())
    if total_size > spec.max_rendered_bytes:
        raise NotebookError(f"rendered notebook exceeds size limit: {spec.path}")
    return body, outputs


def _page_header(spec: NotebookSpec, contract: SourceContract, timestamp: str) -> str:
    configurations = ", ".join(f"`{item}`" for item in spec.configurations) or "None"
    requirements = "\n".join(f"- {item}" for item in spec.local_requirements)
    limitations = "\n".join(f"- {item}" for item in spec.known_limitations)
    source_url = f"{contract.lock.repository}/blob/{contract.lock.commit}/{spec.path}"
    return f"""# {spec.title}

!!! info "Static notebook rendering"
    This page is a static build artifact. It is not a running Python or Jupyter environment.

| Field | Value |
| --- | --- |
| pyEUVICS version | {spec.package_version} |
| Source commit | `{contract.lock.commit}` |
| Notebook source | [{spec.path}]({source_url}) |
| Build execution policy | Executed during this website build |
| Random seed | {spec.random_seed} |
| Configuration | {configurations} |
| Scientific validation status | {spec.validation_status} |
| Publication status | {spec.publication_status} |
| Website build timestamp | {timestamp} |

## Expected local execution requirements

{requirements}

## Known limitations

{limitations}

## Rendered notebook

"""


def render_approved_notebooks(
    contract: SourceContract,
    output_root: Path,
    staged_content: Path,
    timestamp: str,
) -> tuple[InventoryEntry, ...]:
    """Execute every approved notebook twice and stage deterministic Markdown."""

    inventory: list[InventoryEntry] = []
    if not contract.notebooks:
        return ()
    source_build = output_root / "source-build/pyeuvics-notebooks"
    _archive_checkout(contract, source_build)
    index_links: list[str] = []
    for spec in contract.notebooks:
        source = contract.root / spec.path
        source_before = source.read_bytes()
        first_body, first_assets = _render_once(spec, source_build)
        second_body, second_assets = _render_once(spec, source_build)
        if first_body != second_body or first_assets != second_assets:
            raise NotebookError(f"notebook rendering is nondeterministic: {spec.path}")
        if source.read_bytes() != source_before:
            raise NotebookError(f"source notebook changed during rendering: {spec.path}")
        stem = Path(spec.path).stem
        relative_page = Path("software/notebooks") / f"{stem}.md"
        page = staged_content / relative_page
        page.parent.mkdir(parents=True, exist_ok=True)
        rendered = _page_header(spec, contract, timestamp) + first_body
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
        index_links.append(f"- [{spec.title}]({stem}.md)")
    index = staged_content / "software/notebooks/index.md"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(
        "# Static pyEUVICS notebooks\n\n"
        "These pages are deterministic static renderings, not an interactive Jupyter environment.\n\n"
        + "\n".join(index_links)
        + "\n",
        encoding="utf-8",
    )
    return tuple(inventory)


def stage_campaign_overviews(contract: SourceContract, staged_content: Path, timestamp: str) -> None:
    """Replace campaign placeholders only when exact campaign files are approved."""

    campaigns = {
        "reference_6p7nm": ("6.7 nm reference campaign", Path("campaigns/6-7-nm.md")),
        "reference_13p5nm": ("13.5 nm reference campaign", Path("campaigns/13-5-nm.md")),
    }
    for campaign, (title, overview_relative) in campaigns.items():
        approved = tuple(
            item for item in contract.files if item.path.startswith(f"campaigns/{campaign}/")
        )
        if not approved:
            continue
        status = {item.publication_status for item in approved}
        validation = {item.validation_status for item in approved}
        limitations = sorted({value for item in approved for value in item.known_limitations})
        if len(status) != 1 or len(validation) != 1 or None in validation:
            raise NotebookError(f"inconsistent approved campaign metadata: {campaign}")
        links = "\n".join(
            f"- [{item.title}](../imported/pyeuvics/{item.path})" for item in approved
        )
        limitation_text = "\n".join(f"- {item}" for item in limitations)
        (staged_content / overview_relative).write_text(
            f"""# {title}

| Field | Value |
| --- | --- |
| pyEUVICS version | {approved[0].version} |
| Source commit | `{contract.lock.commit}` |
| Publication status | {next(iter(status))} |
| Scientific validation status | {next(iter(validation))} |
| Website build timestamp | {timestamp} |

## Approved campaign material

{links}

## Known limitations

{limitation_text}
""",
            encoding="utf-8",
        )
