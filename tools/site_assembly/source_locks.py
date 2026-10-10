"""Strict two-source lock decoding."""
from pathlib import Path
from .contract_policy import COMMIT_RE
from .contract_values import ContractError, _strict_object, _safe_path
from .models import SourceLock
from .structured import StructuredInputError, read_yaml

def load_locks(path: Path) -> dict[str, SourceLock]:
    """Load exactly two resolved source locks from YAML."""

    try:
        raw = read_yaml(path)
    except StructuredInputError as exc:
        raise ContractError(f"cannot read source lock file: {exc}") from exc
    root = _strict_object(raw, "source lock", {"schema_version", "sources"})
    if type(root["schema_version"]) is not int or root["schema_version"] != 1 or not isinstance(root["sources"], dict):
        raise ContractError("unsupported source lock schema")
    if set(root["sources"]) != {"euvics", "pyeuvics"}:
        raise ContractError("source lock must contain exactly euvics and pyeuvics")
    locks: dict[str, SourceLock] = {}
    fields = {"repository", "commit", "lock_status", "publication_manifest"}
    for name, value in root["sources"].items():
        item = _strict_object(value, f"sources.{name}", fields)
        commit = item["commit"]
        if item["lock_status"] != "locked" or not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            raise ContractError(f"source lock {name} is unresolved or has an invalid commit")
        repository = item["repository"]
        if not isinstance(repository, str) or repository != f"https://github.com/pyeuvics/{'pyEUVICS' if name == 'pyeuvics' else 'euvics'}":
            raise ContractError(f"unexpected repository URL for {name}")
        manifest_path = _safe_path(item["publication_manifest"], f"sources.{name}.publication_manifest")
        locks[name] = SourceLock(name, repository, commit, manifest_path)
    return locks
