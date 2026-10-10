"""EUVICS 1.0/1.1 identity, approval and exact-byte admission."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..contract_policy import (
    EUVICS_ENTRY_FIELDS,
    EUVICS_ROOT_FIELDS,
    KIND_SUFFIXES,
    SHA256_RE,
)
from ..contract_values import (
    ContractError,
    _iso_date,
    _safe_path,
    _strict_object,
    _text,
)
from ..models import NotebookSpec, PublishedFile, SourceLock
from ..primitives import sha256_file
from ..source_checkout import _validate_file


def parse_euvics(manifest: dict[str, Any], lock: SourceLock, root: Path) -> tuple[list[PublishedFile], list[NotebookSpec]]:
    contract_id = manifest.get("contract_id")
    files: list[PublishedFile] = []
    _strict_object(manifest, "EUVICS manifest", EUVICS_ROOT_FIELDS)
    if (
        contract_id != "euvics-public-content-v1"
        or manifest.get("default_policy") != "excluded"
        or manifest.get("$schema") != "public-content-v1.schema.json"
        or manifest.get("schema_version") not in ("1.0", "1.1")
        or manifest.get("repository") != {
            "url": lock.repository,
            "source_commit_policy": "locked-by-consuming-website",
        }
    ):
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
            {"status", "approved_by", "approved_on"}
            | ({"sha256"} if manifest["schema_version"] == "1.1" else set()),
        )
        if approval["status"] != "approved":
            raise ContractError(f"missing explicit publication approval: {relative}")
        _text(approval["approved_by"], "EUVICS approval.approved_by")
        _iso_date(approval["approved_on"], "EUVICS approved_on")
        if "document_date" in entry:
            _iso_date(entry["document_date"], "EUVICS document_date")
        for field in ("title", "version", "license", "attribution"):
            _text(entry[field], f"EUVICS {relative}.{field}")
        if entry["publication_status"] not in ("public-draft", "released"):
            raise ContractError(f"ambiguous EUVICS publication status: {relative}")
        if manifest["schema_version"] == "1.1":
            _validate_file(root, relative, lock.commit)
            expected = approval["sha256"]
            if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
                raise ContractError(f"invalid EUVICS approval.sha256: {relative}")
            actual = sha256_file(root / relative)
            if actual != expected:
                raise ContractError(f"approved SHA-256 mismatch; repeat publication review: {relative}")
        limitations = entry["known_limitations"]
        if not isinstance(limitations, list) or any(not isinstance(v, str) or not v.strip() for v in limitations):
            raise ContractError(f"invalid known limitations: {relative}")
        files.append(
            PublishedFile(
                lock.name,
                relative,
                kind,
                _text(entry["title"], "EUVICS title"),
                _text(entry["version"], "EUVICS version"),
                _text(entry["publication_status"], "EUVICS publication_status"),
                _iso_date(entry["document_date"], "EUVICS document_date") if "document_date" in entry else None,
                _text(entry["license"], "EUVICS license"),
                _text(entry["attribution"], "EUVICS attribution"),
                tuple(limitations),
            )
        )
    return files, []
