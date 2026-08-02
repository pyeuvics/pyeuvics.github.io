"""Build and stage manifest-approved EUVICS Proposal/CDR PDFs."""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import tarfile
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader

from .models import InventoryEntry, PublishedFile, SourceContract

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


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _archive_checkout(contract: SourceContract, destination: Path) -> None:
    try:
        archive = subprocess.check_output(
            ["git", "archive", "--format=tar", contract.lock.commit],
            cwd=contract.root,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise DocumentError(f"cannot archive locked EUVICS source: {exc.output.decode(errors='replace')}") from exc
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
        for member in stream.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise DocumentError(f"unsafe member in locked source archive: {member.name}")
        stream.extractall(destination, filter="data")


def _run_make(source_build: Path, target: str) -> str:
    try:
        result = subprocess.run(
            ["make", target],
            cwd=source_build,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise DocumentError("make is required to build approved EUVICS documents") from exc
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        raise DocumentError(f"EUVICS make {target} failed:\n{output[-4000:]}") from exc
    return result.stdout + result.stderr


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
    if entry.document_date is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry.document_date):
        raise DocumentError(f"document date is missing or invalid: {entry.path}")
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
    limitations = "\n".join(f"- {item}" for item in entry.known_limitations)
    source_url = (
        f"{contract.lock.repository}/blob/{contract.lock.commit}/{quote(entry.path)}"
    )
    return f"""# {entry.title}

<span class="status-badge">{entry.publication_status.title()}</span>

[Download the approved {entry.title} PDF]({filename}){{ .md-button }}

## Publication metadata

| Field | Value |
| --- | --- |
| Revision or version | {entry.version} |
| Document date | {entry.document_date} |
| Publication status | {entry.publication_status.title()} |
| Source commit | `{contract.lock.commit}` |
| SHA-256 | `{checksum}` |
| License | {entry.license} |
| Attribution | {entry.attribution} |
| Website build timestamp | {timestamp} |

## Known limitations and review status

{limitations}

## Provenance

- **Approved source artifact:** [{entry.path} at the locked commit]({source_url})
- **Source repository:** [{contract.lock.repository}]({contract.lock.repository})
"""


def build_approved_documents(
    contract: SourceContract,
    output_root: Path,
    staged_content: Path,
    timestamp: str,
) -> tuple[tuple[InventoryEntry, ...], dict[str, Path]]:
    """Rebuild, verify, stage, and describe exact approved EUVICS PDFs."""

    documents = tuple(item for item in contract.files if item.kind == "pdf")
    if not documents:
        return (), {}
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
    command_log = _run_make(source_build, "verify-archive")
    command_log += _run_make(source_build, "check")
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
