from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "mkdocs.yml"
CONTENT = ROOT / "content"


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def nav_paths(items: list) -> list[str]:
    paths: list[str] = []
    for item in items:
        value = next(iter(item.values()))
        paths.extend(nav_paths(value) if isinstance(value, list) else [value])
    return paths


def test_project_site_configuration_and_generator() -> None:
    config = load_config()
    assert config["site_url"] == "https://chongshikpark.github.io/euvics.github.io/"
    assert config["docs_dir"] == "content"
    assert config["site_dir"] == "site"
    assert config["strict"] is True
    assert config["theme"]["name"] == "material"


def test_explicit_navigation_targets_exist() -> None:
    paths = nav_paths(load_config()["nav"])
    assert len(paths) == len(set(paths)) == 15
    assert all((CONTENT / path).is_file() for path in paths)


def test_mathjax_search_status_labels_and_404_are_configured() -> None:
    config = load_config()
    assert "search" in config["plugins"]
    assert any(isinstance(item, dict) and "pymdownx.arithmatex" in item for item in config["markdown_extensions"])
    assert "javascripts/mathjax.js" in config["extra_javascript"]
    assert (ROOT / "overrides/404.html").is_file()
    status_page = (CONTENT / "project/design-status.md").read_text(encoding="utf-8")
    for term in ("Draft", "Approval Pending", "Design Target", "Calculated", "Simulated", "Reference", "Validated", "Unvalidated", "Superseded", "Released"):
        assert f'>{term}<' in status_page


def test_all_content_has_one_level_one_heading_and_no_local_paths() -> None:
    local_path = re.compile(r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\\\)")
    for path in CONTENT.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".css", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert local_path.search(text) is None, path
        if path.suffix == ".md":
            assert len(re.findall(r"^# ", text, flags=re.MULTILINE)) == 1, path


def test_source_locks_are_exact_and_resolved() -> None:
    lock = yaml.safe_load((ROOT / "sources.lock.yml").read_text(encoding="utf-8"))
    assert set(lock["sources"]) == {"euvics", "pyeuvics"}
    for source in lock["sources"].values():
        assert re.fullmatch(r"[0-9a-f]{40}", source["commit"])
        assert source["lock_status"] == "locked"


def test_generated_site_is_ignored() -> None:
    result = subprocess.run(["git", "check-ignore", "-q", "site/index.html"], cwd=ROOT, check=False)
    assert result.returncode == 0
