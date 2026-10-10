"""Domain errors and validated scalar/container boundaries for source adapters."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
from typing import Any
from .contract_policy import GLOB_CHARS
from .structured import StructuredInputError, iso_date, read_json

class ContractError(ValueError):
    """A lock, repository, or publication contract is unsafe or inconsistent."""



def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value



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
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or pure.as_posix() == "."
        or value != pure.as_posix() + ("/" if directory else "")
    ):
        raise ContractError(f"{label} is not an exact safe repository-relative path: {value}")
    return value



def _strict_object(
    value: object,
    label: str,
    fields: set[str],
    required: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ContractError(f"{label} must be an object with string keys")
    unknown = set(value) - fields
    missing = (fields if required is None else required) - set(value)
    if unknown or missing:
        raise ContractError(
            f"{label} fields invalid; unknown={sorted(unknown)}, missing={sorted(missing)}"
        )
    return value



def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = read_json(path)
    except StructuredInputError as exc:
        raise ContractError(f"cannot read publication manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("publication manifest must be an object")
    return value



def _iso_date(value: object, label: str) -> str:
    try:
        return iso_date(value, label)
    except StructuredInputError as exc:
        raise ContractError(str(exc)) from exc
