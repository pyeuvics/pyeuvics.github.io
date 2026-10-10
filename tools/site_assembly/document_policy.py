"""Website admission of source-owned document release metadata."""
from __future__ import annotations

from dataclasses import dataclass
import shutil
from .models import PublishedFile, SourceContract
from .structured import StructuredInputError, iso_date

DOCUMENT_ROLES = {
    "build/proposal/main.pdf": ("proposal", "documents/proposal.md", "documents/proposal.pdf"),
    "build/cdr/main.pdf": ("cdr", "documents/cdr.md", "documents/cdr.pdf"),
}
class DocumentError(ValueError):
    """An approved document could not be rebuilt and verified safely."""


def validate_document_entry(entry: PublishedFile) -> tuple[str, str, str]:
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


@dataclass(frozen=True)
class DocumentRequirements:
    documents: tuple[PublishedFile, ...]
    roles: tuple[str, ...]
    make_executable: str | None


def document_requirements(contract: SourceContract) -> DocumentRequirements:
    documents = tuple(item for item in contract.files if item.kind == 'pdf')
    roles = tuple(validate_document_entry(item)[0] for item in documents)
    if len(roles) != len(set(roles)):
        raise DocumentError('document publication contract contains duplicate roles')
    if not documents: return DocumentRequirements((), (), None)
    makefile = contract.root / 'Makefile'
    executable = shutil.which('make')
    if not makefile.is_file() or makefile.is_symlink() or executable is None:
        raise DocumentError('document toolchain requires Make and a regular source Makefile')
    return DocumentRequirements(documents, roles, executable)
