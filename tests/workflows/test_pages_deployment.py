from __future__ import annotations

from pathlib import Path

import yaml

from tests.support.paths import ROOT
from tests.support.workflows import CHECKOUT, APP_TOKEN, CONFIGURE_PAGES, UPLOAD_PAGES, DEPLOY_PAGES
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
    assert build["if"] == "github.ref == 'refs/heads/main'"
    assert build["environment"] == "source-read"
    assert build["permissions"] == {"contents": "read", "pages": "read"}
    actions = [step["uses"] for step in build["steps"] if "uses" in step]
    assert actions.count(CHECKOUT) == 3
    assert actions.count(APP_TOKEN) == 1
    assert CONFIGURE_PAGES in actions
    assert UPLOAD_PAGES in actions

    upload = next(
        step for step in build["steps"] if step.get("uses") == UPLOAD_PAGES
    )
    assert upload["with"] == {"path": ".staging/pages/site", "retention-days": "1"}

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--output .staging/pages" in text
    assert "steps.locks.outputs.euvics_commit" in text
    assert "steps.locks.outputs.pyeuvics_commit" in text
    assert text.count("persist-credentials: false") == 3
    assert text.count("vars.EUVICS_DOCS_APP_CLIENT_ID") == 1
    assert text.count("secrets.EUVICS_DOCS_APP_PRIVATE_KEY") == 1
    source_checkouts = [
        step for step in build["steps"] if step.get("uses") == CHECKOUT
    ][1:]
    assert all(
        step["with"]["token"] == "${{ steps.source_token.outputs.token }}"
        and "ssh-key" not in step["with"]
        for step in source_checkouts
    )
    assert "gh-pages" not in text
    names = [step["name"] for step in build["steps"]]
    scrub = names.index("Verify checkout credentials were removed")
    assert scrub > names.index("Check out locked pyEUVICS source")
    assert scrub < names.index("Inspect document toolchain candidates")
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
            "uses": DEPLOY_PAGES,
        }
    ]


def test_manual_checklist_covers_required_external_controls_and_rollback() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    for required in (
        "Source** to\n      **GitHub Actions**",
        "github-pages` environment",
        "Protect `main`",
        "first workflow's validated Pages artifact",
        "Validate website source",
        "signed-out browser session",
        "https://pyeuvics.github.io/",
        "preceding approved deployment",
        "read-only GitHub App",
    ):
        assert required in text
