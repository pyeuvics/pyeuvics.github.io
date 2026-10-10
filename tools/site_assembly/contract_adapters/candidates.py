"""Candidate declarations, approval gates and reviewed subset admission."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from ..contract_values import ContractError, _text, _safe_path, _strict_object, _iso_date
from ..models import SourceLock, PublishedFile, NotebookSpec
from ..source_checkout import _validate_file
from ..contract_policy import (PYEUVICS_SET_APPROVAL_FIELDS, PYEUVICS_SET_BASE_FIELDS,
    PYEUVICS_SET_APPROVAL_REQUIRED, INITIAL_NOTEBOOK_PATHS, INITIAL_CAMPAIGN_PATHS,
    INITIAL_OVERVIEW_FIGURE_PATHS)
from .package import PackageMetadata
from .notebook_policy import parse_notebook_policy


def parse_candidates(candidate_sets: object, package: PackageMetadata, lock: SourceLock,
                     root: Path, excluded_prefixes: list[str], allowlisted_paths: set[str]
                     ) -> tuple[list[PublishedFile], list[NotebookSpec]]:
    files: list[PublishedFile] = []
    notebooks: list[NotebookSpec] = []
    if not isinstance(candidate_sets, list):
        raise ContractError("pyEUVICS candidate_sets must be an array")
    candidate_paths: set[str] = set()
    candidate_names: set[str] = set()
    for set_index, raw_set in enumerate(candidate_sets):
        if not isinstance(raw_set, dict):
            raise ContractError(f"pyEUVICS candidate_sets[{set_index}] must be an object")
        status = _text(raw_set.get("status"), "pyEUVICS candidate status")
        fields = PYEUVICS_SET_APPROVAL_FIELDS if status == "approved" else PYEUVICS_SET_BASE_FIELDS
        required = (
            PYEUVICS_SET_APPROVAL_REQUIRED
            if status == "approved"
            else {"name", "status", "owner", "reason", "files", "dependencies"}
        )
        publication_set = _strict_object(
            raw_set,
            f"pyEUVICS candidate_sets[{set_index}]",
            fields,
            required,
        )
        if status not in {"approval-pending", "blocked-source-approval", "approved"}:
            raise ContractError(f"invalid pyEUVICS publication-set status: {status}")
        name = _text(
            publication_set["name"],
            f"pyEUVICS candidate_sets[{set_index}].name",
        )
        for field in ("owner", "reason"):
            _text(
                publication_set[field],
                f"pyEUVICS candidate_sets[{set_index}].{field}",
            )
        if name in candidate_names:
            raise ContractError(f"duplicate pyEUVICS candidate name: {name}")
        candidate_names.add(name)
        set_files = publication_set["files"]
        dependencies = publication_set["dependencies"]
        if not isinstance(set_files, list) or not isinstance(dependencies, list):
            raise ContractError("pyEUVICS publication-set files/dependencies must be arrays")
        safe_files = tuple(
            _safe_path(value, f"pyEUVICS candidate_sets[{set_index}].files[{file_index}]")
            for file_index, value in enumerate(set_files)
        )
        if not safe_files:
            raise ContractError("pyEUVICS candidate files must be a non-empty array")
        if (
            len(set(safe_files)) != len(safe_files)
            or candidate_paths.intersection(safe_files)
            or allowlisted_paths.intersection(safe_files)
        ):
            raise ContractError("duplicate pyEUVICS candidate path")
        candidate_paths.update(safe_files)
        safe_dependencies = tuple(
            _safe_path(value, f"pyEUVICS candidate_sets[{set_index}].dependencies[{dep_index}]")
            for dep_index, value in enumerate(dependencies)
        )
        if len(set(safe_dependencies)) != len(safe_dependencies):
            raise ContractError("duplicate pyEUVICS candidate dependency")
        for relative in (*safe_files, *safe_dependencies):
            _validate_file(root, relative, lock.commit)
        notebook_paths = tuple(path for path in safe_files if path.endswith(".ipynb"))
        campaign_paths = tuple(path for path in safe_files if not path.endswith(".ipynb"))
        if notebook_paths and campaign_paths:
            raise ContractError("pyEUVICS set must not mix notebooks and static files")
        configuration_paths: tuple[str, ...] = ()
        seed: int | None = None
        maximum: int | None = None
        rendered_maximum: int | None = None
        if notebook_paths:
            policy = parse_notebook_policy(publication_set, safe_dependencies)
            configuration_paths = policy.configurations
            seed, maximum, rendered_maximum = policy.seed, policy.maximum, policy.rendered_maximum
        elif any(
            field in publication_set
            for field in (
                "execution_policy", "random_seed", "configurations",
                "max_rendered_bytes", "max_bytes_per_notebook", "output_policy",
            )
        ):
            raise ContractError("static set contains notebook execution fields")
        if status != "approved":
            continue
        for relative in safe_files:
            if any(relative.startswith(prefix) for prefix in excluded_prefixes):
                raise ContractError(f"approved pyEUVICS set leaks from excluded prefix: {relative}")
        approval = _strict_object(
            publication_set["approval"],
            f"pyEUVICS candidate_sets[{set_index}].approval",
            {"status", "approved_by", "approved_on"},
        )
        if approval["status"] != "approved":
            raise ContractError("approved pyEUVICS set lacks explicit approval")
        _text(approval["approved_by"], "pyEUVICS approval.approved_by")
        _iso_date(approval["approved_on"], "pyEUVICS approved_on")
        for field in ("publication_status", "validation_status"):
            _text(
                publication_set[field],
                f"approved pyEUVICS set {field}",
            )
        set_limitations = publication_set["known_limitations"]
        local_requirements = publication_set["local_requirements"]
        for label, values in (
            ("known_limitations", set_limitations),
            ("local_requirements", local_requirements),
        ):
            if not isinstance(values, list) or not values or any(
                not isinstance(item, str) or not item.strip() for item in values
            ):
                raise ContractError(f"approved pyEUVICS set has invalid {label}")
        if notebook_paths:
            if not set(notebook_paths).issubset(INITIAL_NOTEBOOK_PATHS):
                raise ContractError("approved notebook is outside the initial reviewed subset")
            assert seed is not None
            assert maximum is not None
            assert rendered_maximum is not None
            for relative in notebook_paths:
                notebooks.append(
                    NotebookSpec(
                        relative,
                        Path(relative).stem.replace("_", " ").title(),
                        package.version,
                        _text(publication_set["publication_status"], "set publication_status"),
                        package.license,
                        "See source citation and license metadata.",
                        "execute-during-build",
                        str(seed),
                        configuration_paths,
                        safe_dependencies,
                        _text(publication_set["validation_status"], "set validation_status"),
                        tuple(local_requirements),
                        package.limitations + tuple(set_limitations),
                        maximum,
                        rendered_maximum,
                    )
                )
        else:
            approved_static_paths = INITIAL_CAMPAIGN_PATHS | INITIAL_OVERVIEW_FIGURE_PATHS
            if not set(campaign_paths).issubset(approved_static_paths):
                raise ContractError("approved static file is outside the reviewed subsets")
            for wavelength in ("6p7nm", "13p5nm"):
                expected_campaign = {
                    path for path in INITIAL_CAMPAIGN_PATHS
                    if path.startswith(f"campaigns/reference_{wavelength}/")
                }
                present_campaign = set(campaign_paths).intersection(expected_campaign)
                if present_campaign and present_campaign != expected_campaign:
                    raise ContractError(f"approved {wavelength} campaign set is incomplete")
            for relative in campaign_paths:
                if Path(relative).suffix.lower() not in {
                    ".md", ".svg", ".png", ".jpg", ".jpeg", ".csv", ".json"
                }:
                    raise ContractError(f"unsupported approved static file: {relative}")
                files.append(
                    PublishedFile(
                        lock.name,
                        relative,
                        (
                            "markdown" if relative.endswith(".md")
                            else "asset" if Path(relative).suffix.lower() in {".svg", ".png", ".jpg", ".jpeg"}
                            else "data"
                        ),
                        Path(relative).stem.replace("_", " ").title(),
                        package.version,
                        _text(publication_set["publication_status"], "set publication_status"),
                        None,
                        package.license,
                        "See source citation and license metadata.",
                        package.limitations + tuple(set_limitations),
                        _text(publication_set["validation_status"], "set validation_status"),
                    )
                )
    return files, notebooks
