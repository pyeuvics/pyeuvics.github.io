from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from tools.ci_source_locks import resolve
from tools.validate_ci import ValidationError, _source_date_epoch, write_review_manifest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/site-check.yml"


def load_workflow() -> dict:
    value = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(value, dict)
    return value


def test_workflow_is_read_only_non_deploying_and_uses_locked_refs() -> None:
    workflow = load_workflow()
    assert set(workflow["on"]) == {"pull_request", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {"validate"}
    job = workflow["jobs"]["validate"]
    assert job["runs-on"] == "ubuntu-24.04"
    steps = job["steps"]
    actions = [step["uses"] for step in steps if "uses" in step]
    assert actions.count("actions/checkout@v6") == 3
    assert "actions/setup-python@v6" in actions
    assert "actions/upload-artifact@v7" in actions
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target" not in text
    assert "pages: write" not in text
    assert "id-token: write" not in text
    assert "environment:" not in text
    assert text.count("secrets.EUVICS_SOURCE_DEPLOY_KEY") == 1
    assert text.count("secrets.PYEUVICS_SOURCE_DEPLOY_KEY") == 1
    assert "upload-pages-artifact" not in text
    assert "deploy-pages" not in text
    assert "persist-credentials: false" in text
    assert "steps.locks.outputs.euvics_commit" in text
    assert "steps.locks.outputs.pyeuvics_commit" in text
    assert "sources.lock.yml" in text
    source_checkouts = [
        step for step in steps if step.get("uses") == "actions/checkout@v6"
    ][1:]
    assert all("ssh-key" in step["with"] for step in source_checkouts)
    names = [step["name"] for step in steps]
    scrub = names.index("Verify checkout credentials were removed")
    assert scrub > names.index("Check out locked pyEUVICS source")
    assert scrub < names.index("Inspect approved document requirements")
    assert "tools.verify_runner_credentials" in steps[scrub]["run"]


def test_workflow_cache_and_review_artifact_are_bounded() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["validate"]["steps"]
    setup = next(step for step in steps if step.get("uses") == "actions/setup-python@v6")
    dependencies = setup["with"]["cache-dependency-path"]
    assert set(dependencies.splitlines()) == {
        "requirements-docs.txt",
        "requirements-notebooks.txt",
        "sources.lock.yml",
    }
    upload = next(step for step in steps if step.get("uses") == "actions/upload-artifact@v7")
    paths = set(upload["with"]["path"].splitlines())
    assert paths == {
        ".staging/ci-review/site",
        ".staging/ci-review/staged-content-inventory.json",
        ".staging/ci-review/review-artifact-manifest.json",
    }
    assert upload["with"]["retention-days"] == "7"


def test_ci_dependencies_are_exactly_pinned_and_python_matches_pyeuvics() -> None:
    workflow = load_workflow()
    steps = workflow["jobs"]["validate"]["steps"]
    setup = next(step for step in steps if step.get("uses") == "actions/setup-python@v6")
    assert setup["with"]["python-version"] == "3.13"
    for filename in ("requirements-docs.txt", "requirements-notebooks.txt"):
        requirements = [
            line.strip()
            for line in (ROOT / filename).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        assert requirements
        assert all("==" in requirement for requirement in requirements)


def test_source_lock_outputs_are_exact_and_safe() -> None:
    output = dict(line.split("=", 1) for line in resolve(ROOT / "sources.lock.yml"))
    assert output["euvics_repository"] == "chongshikpark/euvics"
    assert output["pyeuvics_repository"] == "chongshikpark/pyEUVICS"
    assert len(output["euvics_commit"]) == len(output["pyeuvics_commit"]) == 40
    assert all(value.isalnum() for key, value in output.items() if key.endswith("_commit"))


def test_review_manifest_hashes_only_review_artifact(tmp_path: Path) -> None:
    output = tmp_path / "review"
    site = output / "site"
    site.mkdir(parents=True)
    (site / "index.html").write_text("<h1>Fixture</h1>\n", encoding="utf-8")
    inventory = output / "staged-content-inventory.json"
    inventory.write_text('{"files": []}\n', encoding="utf-8")
    manifest_path = write_review_manifest(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [item["path"] for item in manifest["files"]] == [
        "site/index.html",
        "staged-content-inventory.json",
    ]
    assert manifest["files"][0]["sha256"] == hashlib.sha256(
        (site / "index.html").read_bytes()
    ).hexdigest()


def test_invalid_configured_source_date_epoch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-integer")
    with pytest.raises(ValidationError, match="non-negative integer"):
        _source_date_epoch(tmp_path)
