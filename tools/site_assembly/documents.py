"""Render and stage source-owned, independently rebuilt document releases."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .document_build import _archive_checkout as _archive_checkout
from .document_build import _run_make as _build_run_make
from .document_build import _validate_pdf as _validate_pdf
from .document_build import build_documents
from .document_policy import DOCUMENT_ROLES as DOCUMENT_ROLES
from .document_policy import DocumentError as DocumentError
from .document_policy import document_requirements
from .document_policy import validate_document_entry as _validate_document_entry
from .models import InventoryEntry, PublishedFile, SourceContract
from .presentation import (
    Code,
    DocumentPage,
    Link,
    MetadataRow,
    render_document,
    source_url,
)
from .primitives import sha256_file as _sha256

if TYPE_CHECKING:
    from .staging import StagingPlan


def _run_make(source_build: Path, target: str, epoch: str | None = None) -> str:
    return _build_run_make(source_build,target,epoch)


def _overview_markdown(
    entry: PublishedFile,
    contract: SourceContract,
    filename: str,
    checksum: str,
    timestamp: str,
) -> str:
    page = DocumentPage(
        entry.title, entry.publication_status.title(),
        Link(f"Download the approved {entry.title} PDF", filename),
        (
            MetadataRow("Revision or version", entry.version),
            MetadataRow("Document date", entry.document_date or ""),
            MetadataRow("Publication status", entry.publication_status.title()),
            MetadataRow("Source commit", Code(contract.lock.commit)),
            MetadataRow("SHA-256", Code(checksum)),
            MetadataRow("License", entry.license),
            MetadataRow("Attribution", entry.attribution),
            MetadataRow("Website build timestamp", timestamp),
        ),
        entry.known_limitations,
        (
            MetadataRow("Approved source artifact", Link(entry.path + " at the locked commit", source_url(contract.lock, entry.path))),
            MetadataRow("Source repository", Link(contract.lock.repository, contract.lock.repository)),
        ),
    )
    return render_document(page)


def build_approved_documents(
    contract: SourceContract, output_root: Path, staged_content: Path, timestamp: str,
    plan: StagingPlan | None = None, source_date_epoch: str | None = None,
) -> tuple[tuple[InventoryEntry, ...], dict[str, Path]]:
    requirements = document_requirements(contract)
    result = build_documents(contract,requirements,output_root,source_date_epoch,_run_make)
    inventory: list[InventoryEntry] = []
    destinations: dict[str, Path] = {}
    for verified in result.documents:
        entry = verified.entry
        _, overview_relative, pdf_relative = _validate_document_entry(entry)
        rebuilt = verified.rebuilt
        approved_checksum = rebuilt_checksum = verified.sha256
        if plan is not None:
            planned_pdf = plan.source_destinations(contract.lock.name, staged_content)[entry.path]
            pdf_relative = planned_pdf.relative_to(staged_content).as_posix()
            overview_relative = plan.output(pdf_relative).related_outputs[0]
        staged_pdf = staged_content / pdf_relative
        staged_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rebuilt, staged_pdf)
        if _sha256(staged_pdf) != rebuilt_checksum:
            raise DocumentError(f"staged PDF checksum mismatch: {entry.path}")
        overview = staged_content / overview_relative
        overview.write_text(
            _overview_markdown(
                entry,
                contract,
                staged_pdf.name,
                rebuilt_checksum,
                timestamp,
            ),
            encoding="utf-8",
        )
        destinations[entry.path] = staged_pdf
        inventory.append(
            InventoryEntry(
                contract.lock.name,
                entry.path,
                staged_pdf.relative_to(staged_content).as_posix(),
                approved_checksum,
                rebuilt_checksum,
                entry.publication_status,
                entry.known_limitations,
            )
        )
    return tuple(inventory), destinations
