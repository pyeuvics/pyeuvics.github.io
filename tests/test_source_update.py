from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.source_update import (
    SourceUpdateError,
    apply_candidates,
    discover,
    verify_ancestry,
    verify_lock_change,
    write_comparison,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/source-update.yml"


def write_lock(path: Path, euvics: str, pyeuvics: str) -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "sources": {
                    "euvics": {
                        "repository": "https://github.com/chongshikpark/euvics",
                        "commit": euvics,
                        "lock_status": "locked",
                        "publication_manifest": "publication/public-content-v1.json",
                    },
                    "pyeuvics": {
                        "repository": "https://github.com/chongshikpark/pyEUVICS",
                        "commit": pyeuvics,
                        "lock_status": "locked",
                        "publication_manifest": "publication/public-content-v1.json",
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def review_manifest(path: Path, files: list[tuple[str, str, int]]) -> Path:
    path.write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "files": [
                    {"path": name, "sha256": digest, "bytes": size}
                    for name, digest, size in files
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_discovery_resolves_exact_heads_and_reports_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock = write_lock(tmp_path / "current.yml", "1" * 40, "2" * 40)

    def fake_head(repository: str) -> str:
        return "3" * 40 if repository.endswith("/euvics") else "2" * 40

    monkeypatch.setattr("tools.source_update._remote_head", fake_head)
    assert discover(lock) == {
        "euvics": "3" * 40,
        "pyeuvics": "2" * 40,
        "has_updates": "true",
    }


def test_candidate_lock_changes_only_exact_commits(tmp_path: Path) -> None:
    current = write_lock(tmp_path / "current.yml", "1" * 40, "2" * 40)
    candidate = tmp_path / "candidate.yml"
    apply_candidates(current, candidate, {"euvics": "3" * 40, "pyeuvics": "2" * 40})
    assert verify_lock_change(current, candidate) == ("euvics",)
    with pytest.raises(SourceUpdateError, match="no commit update"):
        verify_lock_change(candidate, candidate)
    with pytest.raises(SourceUpdateError, match="invalid"):
        apply_candidates(current, tmp_path / "bad.yml", {"euvics": "tip", "pyeuvics": "2" * 40})


def test_candidate_must_descend_from_current_lock(tmp_path: Path) -> None:
    repository = tmp_path / "source"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)
    (repository / "file.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "one"], cwd=repository, check=True)
    first = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    (repository / "file.txt").write_text("two\n", encoding="utf-8")
    subprocess.run(["git", "commit", "-q", "-am", "two"], cwd=repository, check=True)
    second = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()

    current = write_lock(tmp_path / "current.yml", first, "2" * 40)
    candidate = write_lock(tmp_path / "candidate.yml", second, "2" * 40)
    verify_ancestry(current, candidate, {"euvics": repository, "pyeuvics": repository})
    with pytest.raises(SourceUpdateError, match="not a descendant"):
        verify_ancestry(candidate, current, {"euvics": repository, "pyeuvics": repository})


def test_comparison_records_provenance_diff_and_review_gate(tmp_path: Path) -> None:
    current = write_lock(tmp_path / "current.yml", "1" * 40, "2" * 40)
    candidate = write_lock(tmp_path / "candidate.yml", "3" * 40, "2" * 40)
    baseline = review_manifest(
        tmp_path / "baseline.json",
        [("site/index.html", "a" * 64, 10), ("site/old.html", "b" * 64, 20)],
    )
    proposed = review_manifest(
        tmp_path / "proposed.json",
        [("site/index.html", "c" * 64, 11), ("site/new.html", "d" * 64, 30)],
    )
    output = tmp_path / "pull-request.md"
    write_comparison(current, candidate, baseline, proposed, output)
    text = output.read_text(encoding="utf-8")
    assert "Added files: 1" in text
    assert "Removed files: 1" in text
    assert "Changed files: 1" in text
    assert "`site/new.html`" in text
    assert "`site/old.html`" in text
    assert "does not merge itself" in text
    assert "Confirm each source manifest approval" in text


def test_workflow_separates_untrusted_validation_from_pr_write_credentials() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {}
    assert workflow["concurrency"] == {
        "group": "source-lock-update",
        "cancel-in-progress": "false",
    }
    validate = workflow["jobs"]["validate"]
    propose = workflow["jobs"]["propose"]
    assert validate["permissions"] == {"contents": "read", "pull-requests": "read"}
    assert propose["permissions"] == {"contents": "write", "pull-requests": "write"}
    assert propose["needs"] == "validate"

    validate_text = yaml.safe_dump(validate, sort_keys=False)
    propose_text = yaml.safe_dump(propose, sort_keys=False)
    checkouts = [
        step for step in validate["steps"] if step.get("uses") == "actions/checkout@v6"
    ]
    assert len(checkouts) == 5
    assert all(step["with"]["persist-credentials"] == "false" for step in checkouts)
    assert ".sources/candidate-euvics" in validate_text
    assert "tools.validate_ci" in validate_text
    assert "actions/upload-artifact@v7" in validate_text
    assert ".sources/" not in propose_text
    assert "actions/download-artifact@v8" in propose_text
    assert "tools.source_update verify" in propose_text
    assert "gh pr create" in propose_text
    assert "deploy-pages" not in WORKFLOW.read_text(encoding="utf-8")
    assert "secrets." not in WORKFLOW.read_text(encoding="utf-8")
