"""Disposable source-owned document build and bounded verification evidence."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re

from .assets import AssetError, validate_asset
from .contracts import ContractError, verify_contract_inputs
from .document_policy import DocumentError, DocumentRequirements
from .models import PublishedFile, SourceContract
from .primitives import FileOperationError, atomic_write_text, export_locked_tree, sha256_file, run_text

LOG_FAILURE = re.compile(
    r"Citation .* undefined|Reference .* undefined|There were undefined references|"
    r"No file .*\.bbl|File .* not found",
    re.IGNORECASE,
)


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
        validate_asset(path)
    except AssetError as exc:
        raise DocumentError("invalid or unsafe PDF artifact") from exc


@dataclass(frozen=True)
class LogEvidence:
    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class VerifiedDocument:
    entry: PublishedFile
    rebuilt: Path
    sha256: str


@dataclass(frozen=True)
class DocumentBuildResult:
    documents: tuple[VerifiedDocument, ...]
    logs: tuple[LogEvidence, ...]
    command_sha256: str
    make_executable: str


def inspect_logs(source_build: Path) -> tuple[LogEvidence, ...]:
    logs: list[LogEvidence] = []
    total = 0
    build_root = source_build / 'build'
    if build_root.is_symlink() or any(path.is_symlink() for path in build_root.rglob('*')):
        raise DocumentError('document build contains aliased output')
    for path in sorted(build_root.rglob('*.log')):
        if path.is_symlink() or not path.is_file():
            raise DocumentError('document log is missing or aliased')
        with path.open('rb') as stream: data = stream.read(8_388_609)
        total += len(data)
        if len(data) > 8_388_608 or total > 33_554_432 or len(logs) >= 256:
            raise DocumentError('document log evidence exceeds limits')
        try: text = data.decode('utf-8')
        except UnicodeError as exc: raise DocumentError('document log cannot be decoded') from exc
        if LOG_FAILURE.search(text):
            raise DocumentError('unresolved citation/reference/missing-file marker in document log')
        logs.append(LogEvidence(path.relative_to(source_build).as_posix(),len(data),sha256_file(path)))
    return tuple(logs)


def build_documents(contract: SourceContract, requirements: DocumentRequirements, output_root: Path,
                    epoch: str | None, run_make: Callable[[Path, str, str | None], str] = _run_make) -> DocumentBuildResult:
    if not requirements.documents: return DocumentBuildResult((), (), '', '')
    try: verify_contract_inputs(contract)
    except ContractError as exc: raise DocumentError(str(exc)) from exc
    source_build = output_root / 'source-build/euvics'
    _archive_checkout(contract,source_build)
    for entry in requirements.documents:
        (source_build / entry.path).unlink(missing_ok=True)
    command_log = run_make(source_build,'verify-archive',epoch)
    command_log += run_make(source_build,'check',epoch)
    if len(command_log.encode('utf-8')) > 16_777_216:
        raise DocumentError('document command evidence exceeds limits')
    if LOG_FAILURE.search(command_log):
        raise DocumentError('unresolved citation/reference/missing-file marker in command log')
    command_path=output_root/'source-build/euvics-build.log'
    atomic_write_text(command_path,command_log)
    logs=inspect_logs(source_build)
    documents: list[VerifiedDocument] = []
    for entry in requirements.documents:
        rebuilt=source_build/entry.path
        if not rebuilt.is_file() or rebuilt.is_symlink():
            raise DocumentError(f'approved document build output is missing: {entry.path}')
        checksum=sha256_file(rebuilt)
        if checksum != sha256_file(contract.root/entry.path):
            raise DocumentError(f'rebuilt document checksum does not match approved locked artifact: {entry.path}')
        _validate_pdf(rebuilt)
        documents.append(VerifiedDocument(entry,rebuilt,checksum))
    try: verify_contract_inputs(contract)
    except ContractError as exc: raise DocumentError(str(exc)) from exc
    result=DocumentBuildResult(tuple(documents),logs,sha256_file(command_path),requirements.make_executable or '')
    evidence={'document_build_version':1,'make_executable':result.make_executable,'source_commit':contract.lock.commit,
              'commands':['verify-archive','check'],'command_sha256':result.command_sha256,
              'logs':[asdict(log) for log in result.logs],
              'documents':[{'path':item.entry.path,'sha256':item.sha256} for item in result.documents]}
    atomic_write_text(output_root/'source-build/document-build-evidence.json',json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    return result
