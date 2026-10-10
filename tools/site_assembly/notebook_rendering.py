"""Validate executed MIME/resources and render notebook presentation."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
from nbconvert import MarkdownExporter
from .assets import AssetError, validate_raster_bytes
from .models import NotebookSpec, SourceContract
from .notebook_policy import ExecutedNotebook, RenderedNotebook, NotebookError, SAFE_OUTPUT_MIMES, UNSAFE_HTML, _scan, _validate_markup
from .notebook_headings import normalize_headings
from .presentation import Code, Link, MetadataRow, NotebookPage, render_notebook, source_url


def render_executed(result: ExecutedNotebook) -> RenderedNotebook:
    spec, executed = result.spec, result.notebook
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
        if (not isinstance(name, str) or pure.as_posix() != name or pure.is_absolute()
                or ".." in pure.parts or "\\" in name or ":" in name
                or len(pure.parts) != 2 or pure.parts[0] != asset_directory
                or pure.suffix.lower() not in {'.png', '.jpg', '.jpeg'}
                or not isinstance(value, bytes)):
            raise NotebookError("unsafe rendered notebook asset path or payload")
        try:
            validate_raster_bytes(value,pure.suffix.lower())
        except AssetError as exc:
            raise NotebookError('invalid rendered raster resource') from exc
        outputs[pure.as_posix()] = value
    total_size = len(body.encode("utf-8")) + sum(len(value) for value in outputs.values())
    if total_size > spec.max_rendered_bytes:
        raise NotebookError(f"rendered notebook exceeds size limit: {spec.path}")
    body = normalize_headings(body)
    if len(body.encode("utf-8")) + sum(len(value) for value in outputs.values()) > spec.max_rendered_bytes:
        raise NotebookError(f"rendered notebook exceeds size limit: {spec.path}")
    _scan(body, f"rendered notebook {spec.path}")
    _validate_markup(body, f"rendered notebook {spec.path}")
    if UNSAFE_HTML.search(body):
        raise NotebookError(f"unsafe active content in rendered notebook: {spec.path}")
    return RenderedNotebook(body,outputs)


def _page_header(spec: NotebookSpec, contract: SourceContract, timestamp: str) -> str:
    page = NotebookPage(
        spec.title,
        (
            MetadataRow("pyEUVICS version", spec.package_version),
            MetadataRow("Source commit", Code(contract.lock.commit)),
            MetadataRow("Notebook source", Link(spec.path, source_url(contract.lock, spec.path))),
            MetadataRow("Build execution policy", "Executed during this website build"),
            MetadataRow("Random seed", spec.random_seed),
            MetadataRow("Configuration", Code(", ".join(spec.configurations)) if spec.configurations else "None"),
            MetadataRow("Scientific validation status", spec.validation_status),
            MetadataRow("Publication status", spec.publication_status),
            MetadataRow("License", spec.license),
            MetadataRow("Attribution", spec.attribution),
            MetadataRow("Website build timestamp", timestamp),
        ),
        spec.local_requirements,
        spec.known_limitations,
    )
    return render_notebook(page)
