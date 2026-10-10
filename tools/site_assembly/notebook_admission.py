"""Admit bounded, output-free source notebooks without executing them."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

import nbformat

from .models import NotebookSpec
from .notebook_policy import (
    DATA_LITERAL,
    NETWORK_CODE,
    UNSAFE_HTML,
    AdmittedNotebook,
    NotebookError,
    _scan,
    _validate_markup,
)
from .structured import _finite_tree, _nonfinite, _pairs


def _validate_source(spec: NotebookSpec, source: Path, root: Path) -> Any:
    with source.open('rb') as stream:
        raw = stream.read(spec.max_source_bytes + 1)
    if len(raw) > spec.max_source_bytes:
        raise NotebookError(f"notebook exceeds source size limit: {spec.path}")
    try:
        text = raw.decode("utf-8")
        _finite_tree(json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite))
        notebook = nbformat.reads(text, as_version=4)  # type: ignore[no-untyped-call]
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
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
        if "skip-execution" in cell.get("metadata",{}).get("tags",[]):
            raise NotebookError("approved notebooks cannot silently skip execution")
        if cell.cell_type == "markdown":
            _validate_markup(str(cell.get("source", "")), f"notebook Markdown {spec.path}")
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



def admit_notebook(spec: NotebookSpec, source_root: Path) -> AdmittedNotebook:
    return AdmittedNotebook(spec,source_root,_validate_source(spec,source_root/spec.path,source_root))
