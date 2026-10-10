"""Validated immutable package identity and limitation metadata."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from ..contract_values import ContractError, _strict_object, _text
from ..models import SourceLock
from ..source_checkout import _validate_file

@dataclass(frozen=True)
class PackageMetadata:
    version: str
    license: str
    documentation_status: str
    limitations: tuple[str, ...]


def parse_package(manifest: dict[str, Any], lock: SourceLock, root: Path) -> PackageMetadata:
    package = _strict_object(
        manifest["package"],
        "pyEUVICS package metadata",
        {"name", "version", "license", "citation", "documentation_status", "known_scientific_limitations"},
    )
    if (
        package.get("name") != "pyEUVICS"
        or package.get("license") != "MIT"
        or package.get("citation") != "CITATION.cff"
        or package.get("documentation_status") != "released-with-package"
    ):
        raise ContractError("invalid pyEUVICS package identity or release metadata")
    _text(package["version"], "pyEUVICS package version")
    _validate_file(root, "CITATION.cff", lock.commit)
    limitations = package["known_scientific_limitations"]
    if (
        not isinstance(limitations, list)
        or len(limitations) < 3
        or any(not isinstance(value, str) or not value.strip() for value in limitations)
    ):
        raise ContractError("pyEUVICS scientific limitations are missing")
    return PackageMetadata(_text(package["version"], "package version"),
                           _text(package["license"], "package license"),
                           _text(package["documentation_status"], "documentation status"),
                           tuple(_text(value, "scientific limitation") for value in limitations))
