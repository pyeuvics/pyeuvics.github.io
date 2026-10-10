"""Only the two reviewed repository aliases can enter bound quality evidence."""

import subprocess
from pathlib import Path

import pytest

from tests.support.publication import init_repo
from tools.validation_evidence import EvidenceError, website_identity


def commit_fixture(root: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "Synthetic website aliases"], cwd=root, check=True
    )


@pytest.mark.parametrize(
    ("name", "target", "link"),
    [
        ("CLAUDE.md", "AGENTS.md", "AGENTS.md"),
        (
            "content/stylesheets/readthedocs.css",
            "docs/stylesheets/readthedocs.css",
            "../../docs/stylesheets/readthedocs.css",
        ),
    ],
)
def test_reviewed_alias_and_target_are_bound(
    tmp_path: Path, name: str, target: str, link: str
) -> None:
    init_repo(tmp_path)
    destination = tmp_path / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("original", encoding="utf-8")
    alias = tmp_path / name
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(link)
    commit_fixture(tmp_path)
    assert website_identity(tmp_path).commit
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", target], cwd=tmp_path, check=True
    )
    destination.write_text("changed", encoding="utf-8")
    with pytest.raises(EvidenceError, match="bytes differ"):
        website_identity(tmp_path)


@pytest.mark.parametrize(
    "damage", ["unknown-alias", "wrong-target", "external-target", "untracked-target"]
)
def test_other_aliases_remain_rejected(tmp_path: Path, damage: str) -> None:
    root = tmp_path / "website"
    root.mkdir()
    init_repo(root)
    (root / "AGENTS.md").write_text("governance", encoding="utf-8")
    name, target = "CLAUDE.md", "AGENTS.md"
    if damage == "unknown-alias":
        name = "EXTRA.md"
    elif damage == "wrong-target":
        target = "README.md"
        (root / target).write_text("other", encoding="utf-8")
    elif damage == "external-target":
        target = "../AGENTS.md"
        (tmp_path / "AGENTS.md").write_text("external", encoding="utf-8")
    elif damage == "untracked-target":
        (root / ".gitignore").write_text("/AGENTS.md\n", encoding="utf-8")
    (root / name).symlink_to(target)
    commit_fixture(root)
    with pytest.raises(EvidenceError, match="unapproved website input alias"):
        website_identity(root)
