"""Shift actual rendered headings while preserving source prose and code spans."""
from __future__ import annotations

import re
from html.parser import HTMLParser

from .notebook_policy import NotebookError
from .rendering import load_renderer


class _Headings(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: list[tuple[int,str]] = []
        self.active: int | None = None

    def handle_starttag(self,tag: str,attrs: list[tuple[str,str | None]]) -> None:
        if re.fullmatch('h[1-6]',tag):
            self.values.append((int(tag[1]),''));self.active=len(self.values)-1

    def handle_endtag(self,tag: str) -> None:
        if re.fullmatch('h[1-6]',tag):self.active=None

    def handle_data(self,data: str) -> None:
        if self.active is not None:
            level,text=self.values[self.active]
            self.values[self.active]=(level,text+data)


def normalize_headings(text: str) -> str:
    renderer=load_renderer()
    def headings(value: str) -> list[tuple[int,str]]:
        parser=_Headings();parser.feed(renderer.render(value));parser.close()
        return parser.values
    original=headings(text)
    marker='WEB18HEADINGPROBE'
    while marker in text:marker+='X'
    edits: list[tuple[int,int,str]]=[]
    probes=0
    def is_heading(start: int,end: int,probe: str,level: int) -> bool:
        nonlocal probes
        probes+=1
        if probes>512:raise NotebookError('notebook heading inspection exceeds limit')
        return (level,marker) in headings(text[:start]+probe+text[end:])
    for match in re.finditer(r'(?m)^(.*?)(#{1,6})([ \t]+)([^\n]*)$',text):
        level=len(match[2])
        if level==6:continue
        start,end=match.span()
        if is_heading(start,end,match[1]+match[2]+' '+marker,level) and not is_heading(start,end,match[1]+marker,level):
            edits.append((*match.span(2),'#'*(level+1)))
    for match in re.finditer(r'(?m)^([^\n]+)\n([ \t]*)(=+|-+)[ \t]*$',text):
        level=1 if match[3][0]=='=' else 2
        start,end=match.span()
        if is_heading(start,end,marker+'\n'+match[2]+match[3],level) and not is_heading(start,end,marker,level):
            edits.append((start,end,match[2]+'#'*(level+1)+' '+match[1].lstrip()))
    for match in re.finditer(r'<h([1-6])(\s[^>]*|)>([\s\S]*?)</h\1\s*>',text,re.I):
        level=int(match[1]);start,end=match.span(3)
        if level<6 and is_heading(start,end,marker,level):
            edits.append((*match.span(1),str(level+1)))
            close=text.rfind('</',match.start(),match.end())
            edits.append((close+3,close+4,str(level+1)))
    ordered=sorted(edits)
    if any(right[0]<left[1] for left,right in zip(ordered,ordered[1:])):
        raise NotebookError('ambiguous notebook heading syntax')
    for start,end,replacement in reversed(ordered):text=text[:start]+replacement+text[end:]
    if headings(text)!=[(min(level+1,6),value) for level,value in original]:
        raise NotebookError('unsupported notebook heading syntax')
    return text
