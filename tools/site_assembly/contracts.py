"""Strict source-lock and publication-manifest adapters."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .models import NotebookSpec, PublishedFile, SourceContract, SourceLock

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
GLOB_CHARS = set("*?[]{}")
SUPPORTED_SUFFIXES = {
    "", ".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js",
    ".json", ".csv", ".yaml", ".yml", ".txt", ".cff", ".pdf", ".ipynb",
    ".tex", ".bib", ".py",
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
PYEUVICS_REPOSITORY_FIELDS = {
    "url", "website_repository_url", "website_url", "source_commit_policy",
}
EUVICS_ENTRY_FIELDS = {
    "path", "kind", "title", "version", "publication_status", "approval",
    "license", "attribution", "known_limitations", "document_date",
}
PYEUVICS_SET_BASE_FIELDS = {
    "name", "status", "owner", "reason", "files", "dependencies",
    "max_bytes_per_notebook", "output_policy", "execution_policy", "random_seed",
    "configurations", "max_rendered_bytes",
}
PYEUVICS_SET_APPROVAL_FIELDS = PYEUVICS_SET_BASE_FIELDS | {
    "approval", "publication_status", "validation_status", "known_limitations",
    "local_requirements", "execution_policy", "random_seed", "configurations",
    "max_rendered_bytes",
}
PYEUVICS_SET_APPROVAL_REQUIRED = {
    "name", "status", "owner", "reason", "files", "dependencies", "approval",
    "publication_status", "validation_status", "known_limitations", "local_requirements",
}
INITIAL_NOTEBOOK_PATHS = {
    "notebooks/00_environment_check.ipynb",
    "notebooks/01_linear_ics_kinematics.ipynb",
    "notebooks/02_nonlinear_ics_and_harmonics.ipynb",
    "notebooks/03_parameter_scans.ipynb",
    "notebooks/04_end_to_end_digital_twin.ipynb",
    "notebooks/05_validation_and_cain_comparison.ipynb",
    "notebooks/12_reference_campaign_6p7nm.ipynb",
    "notebooks/13_reference_campaign_13p5nm.ipynb",
}
INITIAL_CAMPAIGN_PATHS = {
    f"campaigns/reference_{wavelength}/{relative}"
    for wavelength in ("6p7nm", "13p5nm")
    for relative in (
        "README.md",
        "figures/spectrum.svg",
        "reports/scientific_report.md",
        "reports/validation.md",
    )
}
INITIAL_OVERVIEW_FIGURE_PATHS = {
    "docs/generated/overview-figures/kinetic-energy-scan.svg",
    "docs/generated/overview-figures/kinetic-energy-scan.csv",
    "docs/generated/overview-figures/kinetic-energy-scan.json",
}


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
        if not isinstance(repository, str) or repository != f"https://github.com/pyeuvics/{'pyEUVICS' if name == 'pyeuvics' else 'euvics'}":
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
    notebooks: list[NotebookSpec] = []
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
                    kind,
                    str(entry["title"]),
                    str(entry["version"]),
                    str(entry["publication_status"]),
                    str(entry["document_date"]) if "document_date" in entry else None,
                    str(entry["license"]),
                    str(entry["attribution"]),
                    tuple(limitations),
                )
            )
    elif lock.name == "pyeuvics":
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
        _validate_file(root, "CITATION.cff")
        limitations = package["known_scientific_limitations"]
        if (
            not isinstance(limitations, list)
            or len(limitations) < 3
            or any(not isinstance(value, str) or not value.strip() for value in limitations)
        ):
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
                    str(package["version"]),
                    str(package["documentation_status"]),
                    None,
                    str(package["license"]),
                    "See source citation and license metadata.",
                    tuple(str(item) for item in limitations),
                )
            )
        candidate_sets = manifest["candidate_sets"]
        if not isinstance(candidate_sets, list):
            raise ContractError("pyEUVICS candidate_sets must be an array")
        candidate_paths: set[str] = set()
        candidate_names: set[str] = set()
        allowlisted_paths = {item.path for item in files}
        for set_index, raw_set in enumerate(candidate_sets):
            if not isinstance(raw_set, dict):
                raise ContractError(f"pyEUVICS candidate_sets[{set_index}] must be an object")
            status = raw_set.get("status")
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
                _validate_file(root, relative)
            notebook_paths = tuple(path for path in safe_files if path.endswith(".ipynb"))
            campaign_paths = tuple(path for path in safe_files if not path.endswith(".ipynb"))
            if notebook_paths and campaign_paths:
                raise ContractError("pyEUVICS set must not mix notebooks and static files")
            configuration_paths: tuple[str, ...] = ()
            seed: int | None = None
            maximum: int | None = None
            rendered_maximum: int | None = None
            if notebook_paths:
                configurations = publication_set.get("configurations")
                if not isinstance(configurations, list) or not configurations or any(
                    not isinstance(item, str) or not item for item in configurations
                ):
                    raise ContractError("notebook configurations are invalid")
                configuration_paths = tuple(
                    _safe_path(
                        value,
                        f"pyEUVICS candidate_sets[{set_index}].configurations",
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
            approved_on = _text(
                approval["approved_on"], "pyEUVICS approval.approved_on"
            )
            try:
                dt.date.fromisoformat(approved_on)
            except ValueError as exc:
                raise ContractError("pyEUVICS approved_on must be a valid ISO date") from exc
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
                            str(package["version"]),
                            str(publication_set["publication_status"]),
                            str(package["license"]),
                            "See source citation and license metadata.",
                            "execute-during-build",
                            str(seed),
                            configuration_paths,
                            safe_dependencies,
                            str(publication_set["validation_status"]),
                            tuple(local_requirements),
                            tuple(str(item) for item in limitations) + tuple(set_limitations),
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
                            str(package["version"]),
                            str(publication_set["publication_status"]),
                            None,
                            str(package["license"]),
                            "See source citation and license metadata.",
                            tuple(str(item) for item in limitations) + tuple(set_limitations),
                            str(publication_set["validation_status"]),
                        )
                    )
    else:
        raise ContractError(f"unsupported source name: {lock.name}")
    if len({item.path for item in files}) != len(files):
        raise ContractError(f"duplicate allowlist paths in {lock.name}")
    for item in files:
        _validate_file(root, item.path)
    return SourceContract(
        lock,
        root,
        tuple(sorted(files, key=lambda item: item.path)),
        tuple(sorted(notebooks, key=lambda item: item.path)),
    )
