"""Behavioral parity with the engine/settings used by MkDocs pages."""
import copy
from pathlib import Path

import markdown
from mkdocs.config import load_config
import pytest
import yaml

from tests.support.paths import ROOT
from tools.site_assembly.rendering import RenderingError, load_renderer

CASES = [
    '$a_0$\n\n$$\nx^2\n$$',
    '# Heading {#stable-id .scientific}\n\nText **strong**.',
    '<div markdown="1">\n**Nested** [link](https://example.org)\n</div>',
    '<span title="approved">raw &amp; HTML</span>',
    '`[example](private.md)`\n\n```python\nprint("<script>")\n```',
    '| Quantity | Value |\n| --- | --- |\n| Energy | 1 |',
    '!!! note\n    Nested **admonition**.\n\n??? details\n    More text.',
]


@pytest.mark.parametrize('source', CASES)
def test_renderer_matches_actual_mkdocs_engine_settings(source: str) -> None:
    config = load_config(str(ROOT/'mkdocs.yml'))
    expected = markdown.Markdown(extensions=config.markdown_extensions, extension_configs=config.mdx_configs or {}).convert(source)
    assert load_renderer(ROOT).render(source) == expected


def test_renderer_preserves_generic_math_and_default_heading_anchors() -> None:
    rendered = load_renderer(ROOT).render('# Heading\n\n$a_0$')
    assert 'id="heading"' in rendered
    assert 'class="arithmatex"' in rendered
    assert '<script' not in rendered


@pytest.mark.parametrize('change', ['order', 'options', 'option-type', 'addition', 'removal'])
def test_unreviewed_configuration_changes_fail_before_rendering(tmp_path: Path, change: str) -> None:
    config = yaml.safe_load((ROOT/'mkdocs.yml').read_text(encoding='utf-8'))
    extensions = copy.deepcopy(config['markdown_extensions'])
    if change == 'order':
        extensions[0], extensions[1] = extensions[1], extensions[0]
    elif change == 'options':
        extensions[4]['pymdownx.arithmatex']['generic'] = False
    elif change == 'option-type':
        extensions[4]['pymdownx.arithmatex']['generic'] = 1
    elif change == 'addition':
        extensions.append('unknown.extension')
    else:
        extensions.pop()
    config['markdown_extensions'] = extensions
    (tmp_path/'mkdocs.yml').write_text(yaml.safe_dump(config), encoding='utf-8')
    with pytest.raises(RenderingError, match='compatibility review'):
        load_renderer(tmp_path)


def test_renderer_does_not_leak_state_between_pages() -> None:
    renderer = load_renderer(ROOT)
    renderer.render('[ref]: https://example.org\n\n[ref]')
    assert 'href=' not in renderer.render('[ref]')
