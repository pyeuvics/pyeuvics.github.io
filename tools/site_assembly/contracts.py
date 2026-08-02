"""Strict source-lock and publication-manifest adapters."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .models import PublishedFile, SourceContract, SourceLock

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
GLOB_CHARS = set("*?[]{}")
SUPPORTED_SUFFIXES = {
    "", ".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js",
    ".json", ".csv", ".yaml", ".yml", ".txt", ".cff",
}
KIND_SUFFIXES = {
    "markdown": {".md"},
    "latex-source": {".tex"},
    "bibliography": {".bib"},
    "metadata": {"", ".json", ".csv", ".yaml", ".yml", ".cff"},
    "pdf": {".pdf"},
    "image": {".png", ".jpg", ".jpeg", ".gif", ".svg"},
    "data": {".csv", ".json", ".yaml", ".yml", ".txt"},
}
EUVICS_ROOT_FIELDS = {
    "$schema", "schema_version", "contract_id", "repository", "default_policy",
    "allowlist", "exclusions", "publication_decisions",
}
PYEUVICS_ROOT_FIELDS = {
    "$schema", "schema_version", "contract_id", "repository", "package",
    "default_policy", "unpublished_link_policy", "allowlist", "candidate_sets",
    "excluded_prefixes",
}
EUVICS_ENTRY_FIELDS = {
    "path", "kind", "title", "version", "publication_status", "approval",
    "license", "attribution", "known_limitations", "document_date",
}


class ContractError(ValueError):
    """A lock, repository, or publication contract is unsafe or inconsistent."""


def _safe_path(value: object, label: str, *, directory: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a non-empty string")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or "\\" in value
        or any(char in value for char in GLOB_CHARS)
        or directory != value.endswith("/")
    ):
        raise ContractError(f"{label} is not an exact safe repository-relative path: {value}")
    return value


def _strict_object(
    value: object,
    label: str,
    fields: set[str],
    required: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    unknown = set(value) - fields
    missing = (fields if required is None else required) - set(value)
    if unknown or missing:
        raise ContractError(
            f"{label} fields invalid; unknown={sorted(unknown)}, missing={sorted(missing)}"
        )
    return value


def load_locks(path: Path) -> dict[str, SourceLock]:
    """Load exactly two resolved source locks from YAML."""

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ContractError(f"cannot read source lock file: {exc}") from exc
    root = _strict_object(raw, "source lock", {"schema_version", "sources"})
    if root["schema_version"] != 1 or not isinstance(root["sources"], dict):
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
        if not isinstance(repository, str) or repository != f"https://github.com/chongshikpark/{'pyEUVICS' if name == 'pyeuvics' else 'euvics'}":
            raise ContractError(f"unexpected repository URL for {name}")
        manifest_path = _safe_path(item["publication_manifest"], f"sources.{name}.publication_manifest")
        locks[name] = SourceLock(name, repository, commit, manifest_path)
    return locks


def _git(root: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *arguments], cwd=root, text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise ContractError(f"git check failed in {root}: {exc.output.strip()}") from exc


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


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read publication manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("publication manifest must be an object")
    return value


def _validate_file(root: Path, relative: str) -> None:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"allowlisted source file is missing, non-regular, or a symlink: {relative}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ContractError(f"unexpected allowlisted file type: {relative}")


def load_contract(lock: SourceLock, root: Path) -> SourceContract:
    """Adapt and strictly validate one supported v1 source publication contract."""

    verify_checkout(lock, root)
    manifest = _load_json(root / lock.manifest_path)
    contract_id = manifest.get("contract_id")
    files: list[PublishedFile] = []
    rewrite_unpublished = False
    if lock.name == "euvics":
        _strict_object(manifest, "EUVICS manifest", EUVICS_ROOT_FIELDS)
        if contract_id != "euvics-public-content-v1" or manifest.get("default_policy") != "excluded":
            raise ContractError("invalid EUVICS publication contract identity or policy")
        allowlist = manifest["allowlist"]
        if not isinstance(allowlist, list):
            raise ContractError("EUVICS allowlist must be an array")
        exclusions = manifest["exclusions"]
        if not isinstance(exclusions, list):
            raise ContractError("EUVICS exclusions must be an array")
        excluded_prefixes: list[str] = []
        for index, raw_exclusion in enumerate(exclusions):
            exclusion = _strict_object(
                raw_exclusion,
                f"EUVICS exclusions[{index}]",
                {"path_prefix", "category", "reason"},
            )
            prefix_value = exclusion["path_prefix"]
            directory = isinstance(prefix_value, str) and prefix_value.endswith("/")
            excluded_prefixes.append(
                _safe_path(prefix_value, f"EUVICS exclusions[{index}].path_prefix", directory=directory)
            )
        for index, raw in enumerate(allowlist):
            entry = _strict_object(
                raw,
                f"EUVICS allowlist[{index}]",
                EUVICS_ENTRY_FIELDS,
                EUVICS_ENTRY_FIELDS - {"document_date"},
            )
            relative = _safe_path(entry["path"], f"EUVICS allowlist[{index}].path")
            if any(
                relative == prefix.rstrip("/") or relative.startswith(prefix.rstrip("/") + "/")
                for prefix in excluded_prefixes
            ):
                raise ContractError(f"allowlisted file leaks from EUVICS exclusions: {relative}")
            kind = entry["kind"]
            if not isinstance(kind, str) or kind not in KIND_SUFFIXES or Path(relative).suffix.lower() not in KIND_SUFFIXES[kind]:
                raise ContractError(f"kind and file extension disagree: {relative}")
            approval = _strict_object(
                entry["approval"],
                f"EUVICS allowlist[{index}].approval",
                {"status", "approved_by", "approved_on"},
            )
            if approval["status"] != "approved":
                raise ContractError(f"missing explicit publication approval: {relative}")
            limitations = entry["known_limitations"]
            if not isinstance(limitations, list) or any(not isinstance(v, str) or not v for v in limitations):
                raise ContractError(f"invalid known limitations: {relative}")
            files.append(
                PublishedFile(
                    lock.name,
                    relative,
                    str(entry["publication_status"]),
                    tuple(limitations),
                )
            )
    elif lock.name == "pyeuvics":
        _strict_object(manifest, "pyEUVICS manifest", PYEUVICS_ROOT_FIELDS)
        if contract_id != "pyeuvics-public-content-v1" or manifest.get("default_policy") != "excluded":
            raise ContractError("invalid pyEUVICS publication contract identity or policy")
        package = _strict_object(
            manifest["package"],
            "pyEUVICS package metadata",
            {"name", "version", "license", "citation", "documentation_status", "known_scientific_limitations"},
        )
        limitations = package["known_scientific_limitations"]
        if not isinstance(limitations, list) or any(not isinstance(v, str) or not v for v in limitations):
            raise ContractError("pyEUVICS scientific limitations are missing")
        allowlist = manifest["allowlist"]
        if not isinstance(allowlist, list):
            raise ContractError("pyEUVICS allowlist must be an array")
        excluded_values = manifest["excluded_prefixes"]
        if not isinstance(excluded_values, list):
            raise ContractError("pyEUVICS excluded_prefixes must be an array")
        excluded_prefixes = [
            _safe_path(value, f"pyEUVICS excluded_prefixes[{index}]", directory=True)
            for index, value in enumerate(excluded_values)
        ]
        rewrite_unpublished = manifest.get("unpublished_link_policy") == "rewrite-to-locked-source"
        for index, value in enumerate(allowlist):
            relative = _safe_path(value, f"pyEUVICS allowlist[{index}]")
            if any(relative.startswith(prefix) for prefix in excluded_prefixes):
                raise ContractError(f"allowlisted file leaks from pyEUVICS exclusions: {relative}")
            files.append(
                PublishedFile(
                    lock.name,
                    relative,
                    str(package["documentation_status"]),
                    tuple(str(item) for item in limitations),
                )
            )
    else:
        raise ContractError(f"unsupported source name: {lock.name}")
    if len({item.path for item in files}) != len(files):
        raise ContractError(f"duplicate allowlist paths in {lock.name}")
    for item in files:
        _validate_file(root, item.path)
    return SourceContract(lock, root, tuple(sorted(files, key=lambda item: item.path)), rewrite_unpublished)
