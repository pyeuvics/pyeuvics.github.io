from __future__ import annotations

import re
from pathlib import Path

import yaml

from tests.support.paths import ROOT
CONFIG = ROOT / "mkdocs.yml"
CANONICAL_CSS = ROOT / "docs/stylesheets/readthedocs.css"
SERVED_CSS = ROOT / "content/stylesheets/readthedocs.css"


def css_text() -> str:
    return CANONICAL_CSS.read_text(encoding="utf-8")


def test_mkdocs_registers_the_repository_owned_stylesheet() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["extra_css"] == ["stylesheets/readthedocs.css"]
    assert CANONICAL_CSS.is_file()
    assert SERVED_CSS.resolve() == CANONICAL_CSS.resolve()



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
    assert 'class="md-path"' in nested
    assert (built_site / "stylesheets/readthedocs.css").is_file()


def test_generated_local_asset_urls_are_not_root_relative(built_site: Path) -> None:
    attribute = re.compile(r'''(?:href|src)=["'](/(?!/)[^"']*)["']''')
    for html_path in built_site.rglob("*.html"):
        if html_path.name == "404.html":
            continue  # MkDocs correctly anchors this special page below site_url.
        html = html_path.read_text(encoding="utf-8")
        assert not attribute.findall(html), html_path
