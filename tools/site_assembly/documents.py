"""Build and stage manifest-approved EUVICS Proposal/CDR PDFs."""

from __future__ import annotations

import re
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from pypdf import PdfReader

from .primitives import FileOperationError, export_locked_tree, sha256_file, run_text

from .structured import StructuredInputError, iso_date

from .contracts import ContractError, verify_contract_inputs

from .presentation import Code, DocumentPage, Link, MetadataRow, render_document, source_url
from .models import InventoryEntry, PublishedFile, SourceContract

if TYPE_CHECKING:
    from .staging import StagingPlan

DOCUMENT_ROLES = {
    "build/proposal/main.pdf": ("proposal", "documents/proposal.md", "documents/proposal.pdf"),
    "build/cdr/main.pdf": ("cdr", "documents/cdr.md", "documents/cdr.pdf"),
}
LOG_FAILURE = re.compile(
    r"Citation .* undefined|Reference .* undefined|There were undefined references|"
    r"No file .*\.bbl|File .* not found",
    re.IGNORECASE,
)


class DocumentError(ValueError):
    """An approved document could not be rebuilt and verified safely."""


_sha256 = sha256_file


def _archive_checkout(contract: SourceContract, destination: Path) -> None:
    try:
        export_locked_tree(contract.root, contract.lock.commit, destination)
    except FileOperationError as exc:
        raise DocumentError(f"cannot archive locked EUVICS source: {exc}") from exc


def _run_make(source_build: Path, target: str, epoch: str | None = None) -> str:
    try:
        environment = dict(os.environ)
        if epoch is not None:
            environment["SOURCE_DATE_EPOCH"] = epoch
        return run_text(["make", target], source_build, f"EUVICS make {target}", environment=environment)
    except FileOperationError as exc:
        raise DocumentError(str(exc)) from exc


def _validate_pdf(path: Path) -> None:
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise DocumentError(f"invalid PDF artifact: {path}") from exc
    if reader.is_encrypted or len(reader.pages) == 0:
        raise DocumentError(f"PDF must be unencrypted and contain at least one page: {path}")
    for page in reader.pages:
        try:
            page.extract_text()
        except Exception as exc:
            raise DocumentError(f"PDF text/layout structure cannot be inspected: {path}") from exc


def _validate_document_entry(entry: PublishedFile) -> tuple[str, str, str]:
    if entry.source_name != "euvics" or entry.path not in DOCUMENT_ROLES:
        raise DocumentError(f"unrecognized approved document path: {entry.path}")
    if entry.kind != "pdf" or entry.publication_status != "released":
        raise DocumentError(f"document must be an explicitly released PDF: {entry.path}")
    try:
        iso_date(entry.document_date, "document date")
    except StructuredInputError as exc:
        raise DocumentError(f"document date is missing or invalid: {entry.path}") from exc
    if not all((entry.title.strip(), entry.version.strip(), entry.license.strip(), entry.attribution.strip())):
        raise DocumentError(f"document publication metadata is incomplete: {entry.path}")
    if not entry.known_limitations:
        raise DocumentError(f"document known limitations/review status is missing: {entry.path}")
    return DOCUMENT_ROLES[entry.path]


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
    contract: SourceContract,
    output_root: Path,
    staged_content: Path,
    timestamp: str,
    plan: StagingPlan | None = None,
    source_date_epoch: str | None = None,
) -> tuple[tuple[InventoryEntry, ...], dict[str, Path]]:
    """Rebuild, verify, stage, and describe exact approved EUVICS PDFs."""

    documents = tuple(item for item in contract.files if item.kind == "pdf")
    if not documents:
        return (), {}
    try:
        verify_contract_inputs(contract)
    except ContractError as exc:
        raise DocumentError(str(exc)) from exc
    roles = [_validate_document_entry(item)[0] for item in documents]
    if len(roles) != len(set(roles)):
        raise DocumentError("document publication contract contains duplicate roles")
    source_build = output_root / "source-build/euvics"
    _archive_checkout(contract, source_build)
    # The tracked release is the approved checksum baseline, not build output.
    # Remove it only from this disposable archive so the build must recreate it.
    for entry in documents:
        archived_release = source_build / entry.path
        if archived_release.exists():
            archived_release.unlink()
    command_log = _run_make(source_build, "verify-archive", source_date_epoch)
    command_log += _run_make(source_build, "check", source_date_epoch)
    (output_root / "source-build/euvics-build.log").write_text(command_log, encoding="utf-8")
    for log in (source_build / "build").rglob("*.log"):
        text = log.read_text(encoding="utf-8", errors="replace")
        if LOG_FAILURE.search(text):
            raise DocumentError(f"unresolved citation/reference/missing-file marker in {log}")
    inventory: list[InventoryEntry] = []
    destinations: dict[str, Path] = {}
    for entry in documents:
        _, overview_relative, pdf_relative = _validate_document_entry(entry)
        approved_source = contract.root / entry.path
        rebuilt = source_build / entry.path
        if not rebuilt.is_file() or rebuilt.is_symlink():
            raise DocumentError(f"approved document build output is missing: {entry.path}")
        approved_checksum = _sha256(approved_source)
        rebuilt_checksum = _sha256(rebuilt)
        if rebuilt_checksum != approved_checksum:
            raise DocumentError(
                f"rebuilt document checksum does not match approved locked artifact: {entry.path}"
            )
        _validate_pdf(rebuilt)
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
