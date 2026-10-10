"""Golden source spans plus final MkDocs URLs for relocated approved content."""
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import pytest
import yaml

from tests.support.paths import ROOT
from tools.site_assembly.models import PublishedFile, SourceContract, SourceLock
from tools.site_assembly.pipeline import _rewrite_markdown, _RenderedLinkParser, AssemblyError


FORMS = [
    '[PDF](../paper.pdf?download=1#page=2)',
    '[PDF][report]\n\n[report]: ../paper.pdf?download=1#page=2',
    '<a href="../paper.pdf?download=1#page=2">PDF</a>',
    '<div markdown="1">\n[PDF](../paper.pdf?download=1#page=2)\n</div>',
    '<div style="background: url(../images/diagram%20one.svg)"></div>',
    '![Diagram](../images/diagram%20one.svg)',
    '<img src="../images/diagram%20one.svg" alt="Diagram">',
    '<img srcset="../images/diagram%20one.svg 1x, ../images/diagram%20two.svg 2x" alt="Diagram">',
    '[Notebook](../examples/example.ipynb#result)',
    '<a href="../examples/example.ipynb#result">Notebook</a>',
    '[Guide](guide.md#topic)',
    '<a href="guide.md#topic">Guide</a>',
    '<a href="../paper.pdf?download=1&amp;mode=view#page=2">PDF</a>',
    '<a href="../&#112;aper.pdf#page=2">PDF</a>',
    '[guide.md]\n\n[guide.md]: guide.md#topic',
]
EXAMPLES = '\n\n`[PDF](../paper.pdf?download=1#page=2)`\n\n```markdown\n[PDF](../paper.pdf?download=1#page=2)\n<a href="guide.md#topic">Guide</a>\n```\n'


def rewrite_fixture(text: str, docs: Path) -> str:
    page = PublishedFile('euvics', 'docs/overview.md', 'markdown', 'Overview', '1', 'released', None, 'MIT', 'Synthetic', ())
    lock = SourceLock('euvics', 'https://github.com/pyeuvics/euvics', 'a'*40, 'manifest.json')
    contract = SourceContract(lock, docs, (page,))
    mapping = {
        'docs/overview.md': docs/'imported/euvics/docs/overview.md',
        'docs/guide.md': docs/'imported/euvics/docs/guide.md',
        'paper.pdf': docs/'downloads/paper.pdf',
        'images/diagram one.svg': docs/'assets/diagram one.svg',
        'images/diagram two.svg': docs/'assets/diagram two.svg',
        'examples/example.ipynb': docs/'software/notebooks/example.md',
    }
    return _rewrite_markdown(text, page, contract, mapping, mapping[page.path], '2026-10-10T00:00:00Z', 'a'*64)


@pytest.mark.parametrize('source', FORMS)
def test_source_rewrite_preserves_identical_urls_in_code(source: str, tmp_path: Path) -> None:
    rewritten = rewrite_fixture(source+EXAMPLES, tmp_path)
    assert EXAMPLES in rewritten
    active = rewritten.split(EXAMPLES)[0]
    assert '../paper.pdf' not in active
    assert '../images/diagram%20' not in active
    assert '../examples/example.ipynb' not in active
    if 'paper.pdf' in source or '&#112;' in source:
        assert 'downloads/paper.pdf' in active
    if 'ipynb' in source:
        assert 'software/notebooks/example' in active


@pytest.mark.parametrize('target', ['../../outside.md', '../private.md', '/private.md'])
def test_rewrite_still_rejects_escaping_or_unpublished_targets(target: str, tmp_path: Path) -> None:
    with pytest.raises(AssemblyError, match='escapes|unpublished|unsafe root'):
        rewrite_fixture(f'[private][ref]\n\n[ref]: {target}\n',tmp_path)


def test_relocated_links_resolve_in_the_built_site(tmp_path: Path) -> None:
    docs=tmp_path/'docs';page=docs/'imported/euvics/docs/overview.md'
    page.parent.mkdir(parents=True)
    page.write_text('# Overview\n\n'+rewrite_fixture('\n\n'.join(FORMS)+EXAMPLES,docs),encoding='utf-8')
    (page.parent/'guide.md').write_text('# Topic\n',encoding='utf-8')
    for relative, content in {
        'index.md':'# Home\n',
        'downloads/paper.pdf':'synthetic resource used only to verify links',
        'software/notebooks/example.md':'# Result\n',
        'assets/diagram one.svg':'<svg xmlns="http://www.w3.org/2000/svg"/>',
        'assets/diagram two.svg':'<svg xmlns="http://www.w3.org/2000/svg"/>',
    }.items():
        path=docs/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
    configuration=yaml.safe_load((ROOT/'mkdocs.yml').read_text(encoding='utf-8'))
    config={'site_name':'Link conformance fixture','docs_dir':'docs','site_dir':'site','strict':True,'use_directory_urls':True,'markdown_extensions':configuration['markdown_extensions']}
    (tmp_path/'mkdocs.yml').write_text(yaml.safe_dump(config),encoding='utf-8')
    subprocess.run([sys.executable,'-m','mkdocs','build','--strict','-f',str(tmp_path/'mkdocs.yml')],check=True,capture_output=True,text=True)
    site_page=tmp_path/'site/imported/euvics/docs/overview/index.html'
    html=site_page.read_text(encoding='utf-8');parser=_RenderedLinkParser();parser.feed(html)
    approved=[target for target in parser.targets if any(part in target for part in ['paper.pdf','diagram%20','notebooks/example','guide/'])]
    assert len(approved)>=15
    for target in approved:
        parsed=urlsplit(target)
        path=(site_page.parent/unquote(parsed.path)).resolve()
        if path.is_dir():path=path/'index.html'
        assert path.is_file(), target
        if parsed.fragment and path.suffix=='.html':
            assert f'id="{parsed.fragment}"' in path.read_text(encoding='utf-8'), target
    assert any('download=1&mode=view#page=2' in target for target in approved)
