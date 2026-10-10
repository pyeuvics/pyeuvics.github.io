"""pyEUVICS 1.0 identity, allowlist and candidate adapters."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from ..contract_values import ContractError, _text, _safe_path, _strict_object, _iso_date
from ..models import SourceLock, PublishedFile, NotebookSpec
from ..source_checkout import _validate_file
from ..contract_policy import PYEUVICS_ROOT_FIELDS, PYEUVICS_REPOSITORY_FIELDS
from .package import parse_package
from .candidates import parse_candidates


def parse_pyeuvics(manifest: dict[str, Any], lock: SourceLock, root: Path) -> tuple[list[PublishedFile], list[NotebookSpec]]:
    contract_id = manifest.get("contract_id")
    files: list[PublishedFile] = []
    _strict_object(manifest, "pyEUVICS manifest", PYEUVICS_ROOT_FIELDS)
    if (
        manifest.get("$schema") != "public-content-v1.schema.json"
        or manifest.get("schema_version") != "1.0"
        or contract_id != "pyeuvics-public-content-v1"
        or manifest.get("default_policy") != "excluded"
    ):
        raise ContractError("invalid pyEUVICS publication contract identity or policy")
    repository = _strict_object(
        manifest["repository"],
        "pyEUVICS repository metadata",
        PYEUVICS_REPOSITORY_FIELDS,
    )
    if repository != {
        "url": "https://github.com/pyeuvics/pyEUVICS",
        "website_repository_url": "https://github.com/pyeuvics/pyeuvics.github.io",
        "website_url": "https://pyeuvics.github.io",
        "source_commit_policy": "locked-by-consuming-website",
    }:
        raise ContractError("invalid pyEUVICS repository identity or commit policy")
    package = parse_package(manifest, lock, root)
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
    if manifest.get("unpublished_link_policy") != "reject":
        raise ContractError("invalid pyEUVICS unpublished-link policy")
    for index, value in enumerate(allowlist):
        relative = _safe_path(value, f"pyEUVICS allowlist[{index}]")
        if any(relative.startswith(prefix) for prefix in excluded_prefixes):
            raise ContractError(f"allowlisted file leaks from pyEUVICS exclusions: {relative}")
        files.append(
            PublishedFile(
                lock.name,
                relative,
                "markdown" if relative.endswith(".md") else "asset",
                relative,
                package.version,
                package.documentation_status,
                None,
                package.license,
                "See source citation and license metadata.",
                package.limitations,
            )
        )
    candidates, notebooks = parse_candidates(manifest["candidate_sets"], package, lock, root,
                                             excluded_prefixes, {item.path for item in files})
    return files + candidates, notebooks
