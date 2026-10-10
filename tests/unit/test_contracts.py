from __future__ import annotations

import copy
import hashlib
import subprocess
from pathlib import Path

import pytest

from tools.site_assembly.contracts import ContractError, _safe_path, load_contract, load_locks
from tools.site_assembly.models import SourceLock

from tests.support.publication import (
    euvics_manifest,
    pyeuvics_manifest,
    pending_pyeuvics_set,
    create_repo,
    create_sources,
    write_locks,
)

from tests.support.paths import ROOT


@pytest.mark.parametrize("path", [".", "./private/file.md", "docs//file.md", "docs/./file.md", "docs/file\n.md"])
def test_noncanonical_publication_paths_are_rejected(path: str) -> None:
    with pytest.raises(ContractError, match="safe repository-relative"):
        _safe_path(path, "fixture")


@pytest.mark.parametrize("digest", [None, "invalid", "0" * 64, "valid"])
def test_euvics_v11_requires_exact_approved_bytes(tmp_path: Path, digest: str | None) -> None:
    manifest = euvics_manifest()
    manifest["schema_version"] = "1.1"
    manifest["allowlist"] = manifest["allowlist"][:1]
    content = "# Approved content\n"
    if digest is not None:
        manifest["allowlist"][0]["approval"]["sha256"] = (
            hashlib.sha256(content.encode()).hexdigest() if digest == "valid" else digest
        )
    source = tmp_path / "source"
    commit = create_repo(source, manifest, {"docs/overview.md": content})
    lock = SourceLock("euvics", "https://github.com/pyeuvics/euvics", commit, "publication/public-content-v1.json")
    if digest == "valid":
        assert len(load_contract(lock, source).files) == 1
    else:
        with pytest.raises(ContractError, match="approval|SHA-256"):
            load_contract(lock, source)


def test_allowlist_rejects_symlinked_parent(tmp_path: Path) -> None:
    source = tmp_path / "source"
    manifest = euvics_manifest("docs/overview.md")
    manifest["allowlist"] = manifest["allowlist"][:1]
    create_repo(source, manifest, {"private/overview.md": "# Excluded\n"})
    (source / "docs").symlink_to("private", target_is_directory=True)
    subprocess.run(["git", "add", "docs"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "Symlink fixture"], cwd=source, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    lock = SourceLock("euvics", "https://github.com/pyeuvics/euvics", commit, "publication/public-content-v1.json")
    with pytest.raises(ContractError, match="symlink"):
        load_contract(lock, source)


def test_production_locks_are_resolved() -> None:
    locks = load_locks(ROOT / "sources.lock.yml")
    assert set(locks) == {"euvics", "pyeuvics"}
    assert all(len(lock.commit) == 40 for lock in locks.values())


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda manifest: manifest["allowlist"][0].update(path="../outside.md"), "exact safe"),
        (
            lambda manifest: manifest["allowlist"][0]["approval"].update(status="pending"),
            "missing explicit publication approval",
        ),
        (lambda manifest: manifest.update(unknown=True), "fields invalid"),
        (
            lambda manifest: manifest["exclusions"].append(
                {"path_prefix": "docs/", "category": "internal", "reason": "fixture"}
            ),
            "leaks from EUVICS exclusions",
        ),
    ],
)
def test_invalid_euvics_contract_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    message: str,
) -> None:
    manifest = copy.deepcopy(euvics_manifest())
    mutation(manifest)
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(ContractError, match=message):
        load_contract(load_locks(lock)["euvics"], euvics)


def test_unexpected_allowlisted_type_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = euvics_manifest("payload.exe")
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    (euvics / "payload.exe").write_bytes(b"fixture executable")
    subprocess.run(["git", "add", "."], cwd=euvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add unexpected type"], cwd=euvics, check=True)
    commits["euvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=euvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(ContractError, match="kind and file extension disagree"):
        load_contract(load_locks(lock)["euvics"], euvics)


def test_missing_allowlisted_path_reports_source_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = euvics_manifest("docs/missing-overview.md")
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(ContractError) as caught:
        load_contract(load_locks(lock)["euvics"], euvics)
    message = str(caught.value)
    assert "allowlisted source file is missing" in message
    assert "docs/missing-overview.md" in message


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda manifest: manifest.update(schema_version="2.0"), "identity or policy"),
        (
            lambda manifest: manifest["repository"].update(
                website_url="https://example.invalid"
            ),
            "repository identity",
        ),
        (
            lambda manifest: manifest["package"].update(
                known_scientific_limitations=[]
            ),
            "scientific limitations",
        ),
        (
            lambda manifest: manifest["candidate_sets"].append(
                pending_pyeuvics_set(files=[])
            ),
            "non-empty array",
        ),
        (
            lambda manifest: manifest["candidate_sets"].append(
                pending_pyeuvics_set(files=["notes/missing.md"])
            ),
            "source file is missing",
        ),
        (
            lambda manifest: manifest["candidate_sets"].extend(
                [pending_pyeuvics_set(), pending_pyeuvics_set(files=["CITATION.cff"])]
            ),
            "duplicate pyEUVICS candidate name",
        ),
    ],
)
def test_invalid_pyeuvics_contract_declarations_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    message: str,
) -> None:
    manifest = pyeuvics_manifest()
    mutation(manifest)
    euvics, pyeuvics, commits = create_sources(tmp_path, pyeuvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(ContractError, match=message):
        load_contract(load_locks(lock)["pyeuvics"], pyeuvics)
