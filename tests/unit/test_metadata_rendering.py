"""Metadata remains literal across typed generated pages; source prose is untouched."""
from dataclasses import replace
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import pytest

from tools.site_assembly.documents import _overview_markdown
from tools.site_assembly.models import PublishedFile, SourceContract, SourceLock, NotebookSpec
from tools.site_assembly.notebooks import _page_header
from tools.site_assembly.pipeline import _rewrite_markdown
from tools.site_assembly.rendering import load_renderer

TIME='2026-10-10T00:00:00Z'
PAYLOADS=['A | B', '[link](javascript:alert(1))', '<img src=x onerror=alert(1)>', 'two\n\n## Injected\n| cell |', 'quote" & apostrophe\'', '$a_0$ \\(x\\) *bold* _math_', '한글 γ '+('long '*400)]


def views() -> tuple[PublishedFile, NotebookSpec, SourceContract]:
    entry=PublishedFile('euvics','build/proposal/main.pdf','pdf','EUVICS Proposal','fixture-1','released','2026-10-10','MIT','Synthetic fixture',('Synthetic content only.',))
    spec=NotebookSpec('notebooks/fixture.ipynb','Synthetic notebook','0.0-fixture','released','MIT','Synthetic fixture','execute-during-build','17',('configs/fixture.yaml',),(),'synthetic-workflow-check-only',('Python environment.',),('Synthetic content only.',),100000,100000)
    lock=SourceLock('euvics','https://github.com/pyeuvics/euvics','a'*40,'manifest.json')
    return entry,spec,SourceContract(lock,Path('.'),(entry,))


class Inspection(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text=[];self.tags=[];self.attributes=[];self.cells=[];self.current=None;self.rows=[];self.row=None
    def handle_starttag(self,tag,attrs):
        self.tags.append(tag);self.attributes.extend(attrs)
        if tag=='tr':self.row=[]
        if tag=='td':self.current=[]
        if tag=='br':self.text.append('\n')
        if tag=='br' and self.current is not None:self.current.append('\n')
    def handle_data(self,data):
        self.text.append(data)
        if self.current is not None:self.current.append(data)
    def handle_endtag(self,tag):
        if tag=='td':
            self.cells.append(''.join(self.current));self.current=None
            self.row.append(self.cells[-1])
        if tag=='tr':self.rows.append(self.row);self.row=None


@pytest.mark.parametrize('value',PAYLOADS,ids=['pipe','link','html','linebreaks','quotes','math','unicode-long'])
@pytest.mark.parametrize('surface',['document','notebook','provenance'])
def test_metadata_is_literal_and_cannot_create_markup(value: str, surface: str, tmp_path: Path) -> None:
    entry,spec,contract=views()
    if surface=='document':
        entry=replace(entry,title=value,version=value,license=value,attribution=value,known_limitations=(value,))
        source=_overview_markdown(entry,contract,'proposal.pdf','b'*64,TIME)
    elif surface=='notebook':
        spec=replace(spec,title=value,package_version=value,license=value,attribution=value,known_limitations=(value,),local_requirements=(value,))
        source=_page_header(spec,contract,TIME)
    else:
        entry=replace(entry,path='docs/overview.md',kind='markdown',version=value,license=value,attribution=value,known_limitations=(value,))
        original='# Reviewed source\n\n$a_0$ and **approved prose**.\n'
        source=_rewrite_markdown(original,entry,contract,{},tmp_path/'overview.md',TIME,'b'*64)
        assert source.startswith(original)
    html=load_renderer().render(source);parsed=Inspection();parsed.feed(html)
    assert parsed.tags.count('h1')==1
    assert not {'img','script','iframe'}.intersection(parsed.tags)
    assert not any(name.startswith('on') or (name=='href' and val.startswith('javascript:')) for name,val in parsed.attributes)
    assert all(len(row)==2 for row in parsed.rows if row)
    if surface!='provenance':
        assert value in parsed.cells
    else:
        assert value in ''.join(parsed.text)


def normalize(html: str) -> str:
    return re.sub(r'>\s+<','><',html).strip()


def test_ordinary_document_rendering_matches_recorded_snapshot() -> None:
    entry,_,contract=views()
    expected=json.loads((Path(__file__).parents[1]/'fixtures/presentation-v1.json').read_text(encoding='utf-8'))
    actual=load_renderer().render(_overview_markdown(entry,contract,'proposal.pdf','b'*64,TIME))
    assert normalize(actual)==normalize(expected['document'])


def test_ordinary_notebook_preserves_snapshot_and_adds_license_attribution() -> None:
    _,spec,contract=views()
    expected=json.loads((Path(__file__).parents[1]/'fixtures/presentation-v1.json').read_text(encoding='utf-8'))
    actual=load_renderer().render(_page_header(spec,contract,TIME))
    parsed=Inspection();parsed.feed(actual)
    assert ['License','MIT'] in parsed.rows
    assert ['Attribution','Synthetic fixture'] in parsed.rows
    old_rows=re.sub(r'<tr>\s*<td>(?:License|Attribution)</td>.*?</tr>','',actual,flags=re.S)
    assert normalize(old_rows)==normalize(expected['notebook'])


@pytest.mark.parametrize('value',PAYLOADS,ids=['pipe','link','html','linebreaks','quotes','math','unicode-long'])
def test_html_attribute_escaping_retains_the_exact_value(value: str) -> None:
    from tools.site_assembly.presentation import attribute_text
    parsed=Inspection();parsed.feed('<span data-caption="'+attribute_text(value)+'">text</span>')
    assert parsed.attributes==[('data-caption',value)]


def test_url_rendering_encodes_delimiters_without_creating_attributes() -> None:
    from tools.site_assembly.presentation import Link, render_link
    source=render_link(Link('approved [PDF]','paper (final).pdf?title="ok"&page=1'))
    parsed=Inspection();parsed.feed(load_renderer().render(source))
    assert parsed.attributes==[('href','paper%20%28final%29.pdf?title=%22ok%22&page=1')]


def test_entry_and_campaign_pages_keep_metadata_literal(tmp_path: Path) -> None:
    import shutil
    from tests.support.paths import ROOT
    from tools.site_assembly.entry_pages import stage_source_entry_pages
    from tools.site_assembly.publication import publication_sources
    from tools.site_assembly.notebooks import stage_campaign_overviews
    entry,_,contract=views()
    payload='<script>alert(1)</script> | [bad](javascript:evil)'
    entry=replace(entry,path='docs/overview.md',kind='markdown',title=payload,version=payload,known_limitations=(payload,))
    euvics=replace(contract,files=(entry,))
    package_entry=replace(entry,source_name='pyeuvics',path='docs/index.md')
    campaign=replace(package_entry,path='campaigns/reference_6p7nm/README.md',validation_status='synthetic')
    pyeuvics=SourceContract(replace(contract.lock,name='pyeuvics',repository='https://github.com/pyeuvics/pyEUVICS'),tmp_path,(package_entry,campaign))
    content=tmp_path/'content';shutil.copytree(ROOT/'content',content)
    stage_source_entry_pages(publication_sources((euvics,pyeuvics),tuple((source.lock.name,item.path,"imported/"+source.lock.name+"/"+item.path) for source in (euvics,pyeuvics) for item in source.files)),content,content/'imported',TIME)
    stage_campaign_overviews(pyeuvics,content,TIME)
    for relative in ['project/overview.md','software/installation.md','campaigns/6-7-nm.md']:
        parsed=Inspection();parsed.feed(load_renderer().render((content/relative).read_text(encoding='utf-8')))
        assert 'script' not in parsed.tags
        assert not any(name=='href' and value.startswith('javascript:') for name,value in parsed.attributes)
        assert payload in ''.join(parsed.text)
