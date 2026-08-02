from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "mkdocs.yml"
CANONICAL_CSS = ROOT / "docs/stylesheets/readthedocs.css"
SERVED_CSS = ROOT / "content/stylesheets/readthedocs.css"


@pytest.fixture(scope="module")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("readthedocs-site")
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return output


def css_text() -> str:
    return CANONICAL_CSS.read_text(encoding="utf-8")


def test_mkdocs_registers_the_repository_owned_stylesheet() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["extra_css"] == ["stylesheets/readthedocs.css"]
    assert CANONICAL_CSS.is_file()
    assert SERVED_CSS.resolve() == CANONICAL_CSS.resolve()


def test_required_design_tokens_and_layout_contract_exist() -> None:
    css = css_text()
    expected = {
        "--euvics-sidebar-width": "300px",
        "--euvics-sidebar-bg": "#343131",
        "--euvics-sidebar-muted": "#9b9b9b",
        "--euvics-accent": "#2980b9",
        "--euvics-page-bg": "#fcfcfc",
        "--euvics-text": "#404040",
        "--euvics-content-max": "800px",
    }
    for name, value in expected.items():
        assert re.search(rf"{re.escape(name)}\s*:\s*{re.escape(value)}\s*;", css)

    desktop = css[css.index("@media screen and (min-width: 76.25em)") :]
    assert "width: var(--euvics-sidebar-width)" in desktop
    assert "margin-left: var(--euvics-sidebar-width)" in desktop
    assert "max-width: var(--euvics-content-max)" in desktop


def test_responsive_accessibility_print_and_overflow_rules_exist() -> None:
    css = css_text()
    for rule in (
        "@media screen and (max-width: 76.24em)",
        "@media screen and (max-width: 44rem)",
        "@media (prefers-reduced-motion: reduce)",
        "@media print",
        ":focus-visible",
        "overflow-x: hidden",
        "overflow-x: auto",
        "max-width: 100%",
    ):
        assert rule in css


def test_stylesheet_has_no_root_relative_assets_or_personal_paths() -> None:
    css = css_text()
    assert re.search(r"url\(\s*['\"]?/", css) is None
    assert re.search(r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\\\)", css) is None


def test_generated_site_has_base_path_safe_css_and_accessible_drawer(built_site: Path) -> None:
    home = (built_site / "index.html").read_text(encoding="utf-8")
    nested = (built_site / "software/science/index.html").read_text(encoding="utf-8")

    assert 'href="stylesheets/readthedocs.css"' in home
    assert 'href="../../stylesheets/readthedocs.css"' in nested
    assert 'id="__drawer"' in home
    assert re.search(r'<label[^>]+for="__drawer"', home)
    assert 'class="md-overlay"' in home
    assert 'for="__drawer"' in home
    assert 'src="javascripts/navigation.js"' in home
    navigation_script = (built_site / "javascripts/navigation.js").read_text(encoding="utf-8")
    assert 'setAttribute("tabindex", "0")' in navigation_script
    assert 'setAttribute("aria-expanded"' in navigation_script
    assert 'event.key === "Escape"' in navigation_script
    assert 'class="md-path"' in nested
    assert (built_site / "stylesheets/readthedocs.css").is_file()


def test_generated_local_asset_urls_are_not_root_relative(built_site: Path) -> None:
    attribute = re.compile(r'''(?:href|src)=["'](/(?!/)[^"']*)["']''')
    for html_path in built_site.rglob("*.html"):
        if html_path.name == "404.html":
            continue  # MkDocs correctly anchors this special page below site_url.
        html = html_path.read_text(encoding="utf-8")
        assert not attribute.findall(html), html_path
