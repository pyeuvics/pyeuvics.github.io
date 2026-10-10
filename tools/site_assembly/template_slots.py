"""Explicit replaceable slots preserve website prose and prevent duplicate inserts."""
from pathlib import Path

class TemplateSlotError(ValueError):
    """A website template does not declare one unambiguous slot."""


def fill_slot(path: Path,name: str,body: str) -> None:
    start=f'<!-- publication:{name}:start -->';end=f'<!-- publication:{name}:end -->'
    text=path.read_text(encoding='utf-8')
    if text.count(start)!=1 or text.count(end)!=1 or text.index(start)>text.index(end):
        raise TemplateSlotError(f'missing or ambiguous publication slot: {name}')
    before,rest=text.split(start);_,after=rest.split(end)
    path.write_text(before+start+'\n'+body.rstrip()+'\n'+end+after,encoding='utf-8')
