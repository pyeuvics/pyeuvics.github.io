"""Strict JSON/YAML decoding and reusable scalar checks for external inputs."""
from __future__ import annotations

from collections.abc import Hashable
import datetime as dt
import json
import math
from pathlib import Path
import re
from typing import Any, NoReturn

import yaml
from yaml.nodes import MappingNode


class StructuredInputError(ValueError):
    """An external document has ambiguous syntax or invalid scalar values."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if not isinstance(key, str) or key in result:
            raise StructuredInputError("duplicate or non-string mapping key")
        result[key] = value
    return result


def _nonfinite(value: str) -> NoReturn:
    raise StructuredInputError("non-finite JSON number")


class UniqueSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        self.flatten_mapping(node)
        pairs = [(self.construct_object(key, deep=deep), self.construct_object(value, deep=deep))
                 for key, value in node.value]
        result: dict[Hashable, Any] = {key: value for key, value in _pairs(pairs).items()}
        return result


def _finite_tree(value: Any, active: set[int] | None = None) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise StructuredInputError("non-finite number")
    if isinstance(value, (dict, list)):
        active = set() if active is None else active
        identity = id(value)
        if identity in active:
            raise StructuredInputError("recursive document alias")
        active.add(identity)
        for item in value.values() if isinstance(value, dict) else value:
            _finite_tree(item, active)
        active.remove(identity)


def read_json(path: Path) -> Any:
    try:
        result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs, parse_constant=_nonfinite)
        _finite_tree(result)
        return result
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise StructuredInputError(f"invalid JSON document: {path.name}") from exc


def read_yaml(path: Path) -> Any:
    try:
        result = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueSafeLoader)
        _finite_tree(result)
        return result
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError) as exc:
        raise StructuredInputError(f"invalid YAML document: {path.name}") from exc


def iso_date(value: object, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise StructuredInputError(f"{label} must be a valid ISO date")
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise StructuredInputError(f"{label} must be a valid ISO date") from exc
    return value


def finite_number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        raise StructuredInputError(f"{label} must be a finite number")
    number = float(value)  # type: ignore[arg-type]
    if not math.isfinite(number) or (positive and number <= 0):
        raise StructuredInputError(f"{label} must be a finite{' positive' if positive else ''} number")
    return number
