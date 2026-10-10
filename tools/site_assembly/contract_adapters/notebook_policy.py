"""Validated notebook execution-policy record, independent of publication approval."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ..contract_values import ContractError, _safe_path

@dataclass(frozen=True)
class NotebookPolicy:
    configurations: tuple[str, ...]
    seed: int
    maximum: int
    rendered_maximum: int


def parse_notebook_policy(publication_set: dict[str, Any], safe_dependencies: tuple[str, ...]) -> NotebookPolicy:
    configurations = publication_set.get("configurations")
    if not isinstance(configurations, list) or not configurations or any(
        not isinstance(item, str) or not item for item in configurations
    ):
        raise ContractError("notebook configurations are invalid")
    configuration_paths = tuple(
        _safe_path(
            value,
            "notebook configurations",
        )
        for value in configurations
    )
    if len(set(configuration_paths)) != len(configuration_paths):
        raise ContractError("notebook configurations must be unique")
    if not set(configuration_paths).issubset(safe_dependencies):
        raise ContractError(
            "notebook configurations must be explicitly approved dependencies"
        )
    if publication_set.get("execution_policy") != "execute-during-build":
        raise ContractError("notebooks must execute during the build")
    if publication_set.get("output_policy") != "source-notebooks-must-have-no-outputs":
        raise ContractError("notebooks must have no source outputs")
    seed = publication_set.get("random_seed")
    if type(seed) is not int or seed < 0:
        raise ContractError("notebook random_seed must be a non-negative integer")
    maximum = publication_set.get("max_bytes_per_notebook")
    rendered_maximum = publication_set.get("max_rendered_bytes")
    if (
        type(maximum) is not int
        or maximum < 1
        or type(rendered_maximum) is not int
        or rendered_maximum < 1
    ):
        raise ContractError("notebook size limits are invalid")
    return NotebookPolicy(configuration_paths, seed, maximum, rendered_maximum)
