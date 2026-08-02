"""Typed data models for locked source publication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceLock:
    """One exact source repository revision required by the website."""

    name: str
    repository: str
    commit: str
    manifest_path: str


@dataclass(frozen=True)
class PublishedFile:
    """One manifest-approved source file and its publication metadata."""

    source_name: str
    path: str
    kind: str
    title: str
    version: str
    publication_status: str
    document_date: str | None
    license: str
    attribution: str
    known_limitations: tuple[str, ...]
    validation_status: str | None = None


@dataclass(frozen=True)
class NotebookSpec:
    """One explicitly approved notebook and its bounded render policy."""

    path: str
    title: str
    package_version: str
    publication_status: str
    license: str
    attribution: str
    execution_policy: str
    random_seed: str
    configurations: tuple[str, ...]
    dependencies: tuple[str, ...]
    validation_status: str
    local_requirements: tuple[str, ...]
    known_limitations: tuple[str, ...]
    max_source_bytes: int
    max_rendered_bytes: int


@dataclass(frozen=True)
class SourceContract:
    """Validated allowlist and link behavior for one locked source."""

    lock: SourceLock
    root: Path
    files: tuple[PublishedFile, ...]
    rewrite_unpublished_links: bool
    notebooks: tuple[NotebookSpec, ...] = ()


@dataclass(frozen=True)
class InventoryEntry:
    """A staged file with exact source and checksum provenance."""

    source: str
    source_path: str
    staged_path: str
    source_sha256: str
    staged_sha256: str
    publication_status: str
    known_limitations: tuple[str, ...]


@dataclass(frozen=True)
class AssemblyResult:
    """Paths and inventory produced by a successful assembly."""

    output_root: Path
    staged_content: Path
    site: Path
    inventory: tuple[InventoryEntry, ...]
