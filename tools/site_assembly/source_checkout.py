"""Git checkout and consumed-byte identity checks, independent of manifest schemas."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
from .contract_policy import SUPPORTED_SUFFIXES
from .contract_values import ContractError
from .models import SourceContract, SourceLock
from .primitives import FileOperationError, run_text

def _git(root: Path, *arguments: str) -> str:
    try:
        return run_text(["git", *arguments], root, "source Git check").strip()
    except FileOperationError as exc:
        raise ContractError(str(exc)) from exc



def verify_checkout(lock: SourceLock, root: Path) -> None:
    """Require a clean checkout at exactly the locked commit and tracked manifest."""

    if not (root / ".git").exists():
        raise ContractError(f"source is not a Git checkout: {root}")
    actual = _git(root, "rev-parse", "HEAD")
    if actual != lock.commit:
        raise ContractError(f"commit mismatch for {lock.name}: expected {lock.commit}, got {actual}")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ContractError(f"source checkout is dirty: {lock.name}")
    tracked = _git(root, "ls-tree", "-r", "--name-only", "HEAD", "--", lock.manifest_path)
    if tracked != lock.manifest_path:
        raise ContractError(f"publication manifest is not tracked at locked commit: {lock.name}")
    _validate_file(root, lock.manifest_path, lock.commit)



def _validate_file(root: Path, relative: str, commit: str) -> None:
    path = root / relative
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(f"allowlisted source path contains a symlink: {relative}")
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"allowlisted source file is missing, non-regular, or a symlink: {relative}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ContractError(f"unexpected allowlisted file type: {relative}")

    record = _git(root, "--literal-pathspecs", "ls-tree", "-z", commit, "--", relative)
    entries = record.rstrip("\0").split("\0")
    if len(entries) != 1 or "\t" not in entries[0]:
        raise ContractError(f"source file is absent from locked Git tree: {relative}")
    metadata, stored_path = entries[0].split("\t", 1)
    mode, kind, object_id = metadata.split()
    if stored_path != relative or kind != "blob" or mode not in {"100644", "100755"}:
        raise ContractError(f"source file is not regular in locked Git tree: {relative}")
    actual = _git(root, "hash-object", "--no-filters", "--", relative)
    if actual != object_id:
        raise ContractError(f"source bytes differ from locked Git tree: {relative}")



def verify_contract_inputs(contract: SourceContract) -> None:
    """Recheck admitted live files before/after consumption; not a hostile-host sandbox."""
    verify_checkout(contract.lock, contract.root)
    paths = {entry.path for entry in contract.files}
    for notebook in contract.notebooks:
        paths.update((notebook.path, *notebook.dependencies, *notebook.configurations))
    if contract.lock.name == "pyeuvics":
        paths.add("CITATION.cff")
    for relative in sorted(paths):
        _validate_file(contract.root, relative, contract.lock.commit)
