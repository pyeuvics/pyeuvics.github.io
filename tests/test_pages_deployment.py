from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pages.yml"
CHECKLIST = ROOT / "docs/pages-deployment.md"


def load_workflow() -> dict:
    value = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(value, dict)
    return value


def test_deployment_triggers_are_main_and_manual_only() -> None:
    workflow = load_workflow()
    assert set(workflow["on"]) == {"push", "workflow_dispatch"}
    assert workflow["on"]["push"]["branches"] == ["main"]
    assert "pull_request" not in workflow["on"]
    assert workflow["permissions"] == {}
    assert workflow["concurrency"] == {
        "group": "github-pages",
        "cancel-in-progress": "false",
    }


def test_build_is_read_only_locked_and_uploads_only_validated_site() -> None:
    workflow = load_workflow()
    build = workflow["jobs"]["build"]
    assert build["permissions"] == {"contents": "read", "pages": "read"}
    actions = [step["uses"] for step in build["steps"] if "uses" in step]
    assert actions.count("actions/checkout@v6") == 3
    assert "actions/configure-pages@v5" in actions
    assert "actions/upload-pages-artifact@v4" in actions

    upload = next(
        step for step in build["steps"] if step.get("uses") == "actions/upload-pages-artifact@v4"
    )
    assert upload["with"] == {"path": ".staging/pages/site", "retention-days": "1"}

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--output .staging/pages" in text
    assert "steps.locks.outputs.euvics_commit" in text
    assert "steps.locks.outputs.pyeuvics_commit" in text
    assert text.count("persist-credentials: false") == 3
    assert text.count("secrets.EUVICS_SOURCE_DEPLOY_KEY") == 1
    assert text.count("secrets.PYEUVICS_SOURCE_DEPLOY_KEY") == 1
    assert "gh-pages" not in text
    names = [step["name"] for step in build["steps"]]
    scrub = names.index("Verify checkout credentials were removed")
    assert scrub > names.index("Check out locked pyEUVICS source")
    assert scrub < names.index("Inspect approved document requirements")
    assert "tools.verify_runner_credentials" in build["steps"][scrub]["run"]


def test_deployment_has_only_required_write_permissions_and_environment() -> None:
    deploy = load_workflow()["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    assert deploy["environment"] == {
        "name": "github-pages",
        "url": "${{ steps.deployment.outputs.page_url }}",
    }
    assert deploy["steps"] == [
        {
            "name": "Deploy to GitHub Pages",
            "id": "deployment",
            "uses": "actions/deploy-pages@v4",
        }
    ]


def test_manual_checklist_covers_required_external_controls_and_rollback() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    for required in (
        "Source** to\n      **GitHub Actions**",
        "github-pages` environment",
        "Protect `main`",
        "first workflow's validated Pages artifact",
        "signed-out browser session",
        "https://chongshikpark.github.io/euvics.github.io/",
        "preceding approved deployment",
        "read-only deploy key",
    ):
        assert required in text
