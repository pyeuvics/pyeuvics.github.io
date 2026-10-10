"""Benign and hostile source fragments for the explicit browser policy."""
from pathlib import Path

import pytest

from tools.site_assembly.models import PublishedFile
from tools.site_assembly.pipeline import AssemblyError, _validate_rendered_links

PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
HOSTILE = [
    '<base href="https://example.org/">',
    '<meta http-equiv="refresh" content="0;url=https://example.org/">',
    '<a href="data:text/html,unsafe">data navigation</a>',
    '<img src="data:image/svg+xml,%3Csvg%20onload=alert(1)%3E">',
    '<img src="data:image/png;base64,AAAA">',
    '<a href="java&#x09;script:alert(1)">encoded control</a>',
    '<a href="java%73cript:alert(1)">encoded scheme</a>',
    '<a href="javascript:alert(1)" href="guide.md">duplicate</a>',
    '<iframe srcdoc="&lt;script&gt;alert(1)&lt;/script&gt;"></iframe>',
    '<svg><foreignObject><div>HTML context</div></foreignObject></svg>',
    '<svg><set attributeName="href" to="javascript:alert(1)"/></svg>',
    '<a href="guide.md" ping="https://example.org/track">ping</a>',
    '<div style="width: expression(alert(1))">CSS</div>',
    r'<div style="width: e\78pression(alert(1))">CSS</div>',
    '<div style="behavior: url(guide.md)">CSS</div>',
    '<div style="background: image-set(url(guide.md) 1x)">CSS</div>',
    '<div style="background: var(--unreviewed)">CSS</div>',
    '<div style="@import url(guide.md)">CSS</div>',
    r'<div style="background: u\72l(javascript:alert)">CSS</div>',
    r'<div style="background: u\72l(private.png)">hidden excluded resource</div>',
    '<style>body { background: url(private.png) }</style>',
    '<img srcset="guide.md 0x" alt="invalid density">',
    '<svg><use xlink:href="data:text/html,unsafe"/></svg>',
    '<div style="background: url(guide.md">malformed</div>',
]
BENIGN = [
    '<a href="https://example.org/guide?x=1&amp;y=2">guide</a>',
    '<a href="mailto:reader@example.org">email</a>',
    '<img src="'+PNG+'" alt="synthetic pixel">',
    '<img srcset="'+PNG+' 1x, image.png 2x" alt="images">',
    '<div style="/* url(private.png) */ background-image: url(image.png); color: #333">CSS</div>',
    r'<div style="background-image: u\72l(image.png)">escaped function</div>',
    r'<div style="background-image: url(\69mage.png)">escaped path</div>',
    '<div style="width: calc(100% - 2px); color: rgb(1, 2, 3)">CSS</div>',
    '<svg viewBox="0 0 10 10"><defs><path id="shape" d="M0 0"/></defs><use href="#shape"/></svg>',
    '<svg><path fill="url(#gradient)" d="M0 0"/></svg>',
    '<script type="math/tex; mode=display">x^2</script>',
    '`<base href="https://example.org/">`',
]


def validate(source: str) -> None:
    page=PublishedFile('euvics','docs/index.md','markdown','fixture','1','released',None,'MIT','fixture',())
    _validate_rendered_links(source,page,{'docs/guide.md':Path('guide.md'),'docs/image.png':Path('image.png')})


@pytest.mark.parametrize('source', HOSTILE)
def test_hostile_browser_contexts_are_rejected(source: str) -> None:
    with pytest.raises(AssemblyError):
        validate(source)


@pytest.mark.parametrize('source', BENIGN)
def test_reviewed_scientific_markup_remains_supported(source: str) -> None:
    validate(source)


def test_css_escaped_path_uses_the_same_destination_mapping(tmp_path: Path) -> None:
    from tests.unit.test_link_rewriting import rewrite_fixture
    result=rewrite_fixture(r'<div style="background: u\72l(../images/di\61gram%20one.svg)"></div>',tmp_path)
    assert 'assets/diagram%20one.svg' in result


@pytest.mark.parametrize(('source','rejected'), [
    ('<base href="https://example.org">', True),
    ('[data](data:text/html,unsafe)', True),
    ('<div style="width: expression(alert(1))">CSS</div>', True),
    ('$a_0$ and **scientific context**.', False),
    ('`<base href="https://example.org">`', False),
])
def test_notebook_markdown_uses_the_browser_content_policy(source: str, rejected: bool, tmp_path: Path) -> None:
    import nbformat
    from tools.site_assembly.models import NotebookSpec
    from tools.site_assembly.notebooks import NotebookError, _validate_source
    spec=NotebookSpec('fixture.ipynb','fixture','1','released','MIT','synthetic','execute-during-build','17',(),(),'synthetic',(),(),100000,100000)
    notebook=nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(source)])
    path=tmp_path/spec.path
    path.write_text(nbformat.writes(notebook),encoding='utf-8')
    if rejected:
        with pytest.raises(NotebookError,match='unsafe active content'):
            _validate_source(spec,path,tmp_path)
    else:
        assert len(_validate_source(spec,path,tmp_path).cells)==1
