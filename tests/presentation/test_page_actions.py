from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs,urlsplit
from mkdocs.config import load_config
import pytest
from tests.support.paths import ROOT
from tools.site_assembly.models import SourceLock
from tools.site_assembly.publication import PublicationSource
from tools.site_assembly.staging import StagingPlan,PlannedOutput,SourceDestination,OutputKind
from tools.site_assembly.page_actions import page_actions

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.append(dict(attrs))


def plan():
    locks=[SourceLock(name,'https://github.com/pyeuvics/'+repo,commit*40,'publication/manifest.json') for name,repo,commit in [('euvics','euvics','a'),('pyeuvics','pyEUVICS','b')]]
    outputs=(
        PlannedOutput('about/index.md','website','website-copy',OutputKind.WEBSITE),
        PlannedOutput('imported/pyeuvics/docs/index.md','pyeuvics','markdown-import',OutputKind.IMPORT),
        PlannedOutput('documents/proposal.md','website','document-overview',OutputKind.GENERATED,(),('documents/proposal.pdf',)),
        PlannedOutput('software/notebooks/example.md','pyeuvics','notebook-render',OutputKind.RENDERED),
        PlannedOutput('campaigns/6-7-nm.md','website','campaign-overview',OutputKind.GENERATED),
        PlannedOutput('software/installation.md','website','entry-page',OutputKind.GENERATED,('website:content/software/installation.md',)),
        PlannedOutput('documents/index.md','website','entry-page',OutputKind.GENERATED),
    )
    destinations=(SourceDestination('pyeuvics','docs/index.md',outputs[1].path),SourceDestination('euvics','build/proposal/main.pdf','documents/proposal.pdf'),SourceDestination('pyeuvics','notebooks/example.ipynb',outputs[3].path))
    return StagingPlan((),outputs,(),destinations,tuple(PublicationSource(lock,(),(),()) for lock in locks))


@pytest.mark.parametrize(('path','repository','source'),[
    ('imported/pyeuvics/docs/index.md','pyEUVICS','docs/index.md'),
    ('documents/proposal.md','euvics','build/proposal/main.pdf'),
    ('software/notebooks/example.md','pyEUVICS','notebooks/example.ipynb'),
    ('campaigns/6-7-nm.md','pyEUVICS','publication/manifest.json'),
    ('software/installation.md','pyeuvics.github.io','content/software/installation.md'),
    ('documents/index.md','pyeuvics.github.io','tools/site_assembly/publication_pages.py'),
    ('about/index.md','pyeuvics.github.io','content/about/index.md'),
])
def test_rendered_actions_follow_page_ownership(path,repository,source):
    actions=page_actions(plan(),'c'*40)
    environment=load_config(str(ROOT/'mkdocs.yml')).theme.get_env()
    page=SimpleNamespace(file=SimpleNamespace(src_uri=path),edit_url='https://github.com/pyeuvics/pyeuvics.github.io/edit/main/content/'+path)
    config=SimpleNamespace(extra={'publication_pages':actions},theme=SimpleNamespace(icon=SimpleNamespace(edit=None,view=None)))
    html=environment.get_template('partials/actions.html').render(page=page,config=config,features=['content.action.edit'],lang=SimpleNamespace(t=lambda value:value))
    parser=Links();parser.feed(html)
    if path=='about/index.md':
        assert len(parser.links)==1 and parser.links[0]['href'].endswith('/edit/main/'+source)
        return
    assert len(parser.links)==2
    reference,correction=[item['href'] for item in parser.links]
    commit={'euvics':'a','pyEUVICS':'b','pyeuvics.github.io':'c'}[repository]*40
    assert reference=='https://github.com/pyeuvics/'+repository+'/blob/'+commit+'/'+source
    assert urlsplit(correction).path=='/pyeuvics/'+repository+'/issues/new'
    assert reference in parse_qs(urlsplit(correction).query)['body'][0]
    assert all('/edit/' not in item['href'] for item in parser.links)
    assert all(item.get('aria-label') for item in parser.links)
