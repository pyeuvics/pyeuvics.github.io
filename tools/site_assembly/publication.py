"""Immutable, root-free approved content shared by publication presenters."""
from __future__ import annotations
from dataclasses import dataclass
from .models import SourceLock, PublishedFile, NotebookSpec, SourceContract

@dataclass(frozen=True)
class PublicationSource:
    lock: SourceLock
    files: tuple[PublishedFile,...]
    notebooks: tuple[NotebookSpec,...]
    destinations: tuple[tuple[str,str],...]

    def destination(self,path: str) -> str:
        return dict(self.destinations)[path]

    def markdown(self,prefixes: tuple[str,...]) -> tuple[PublishedFile,...]:
        return tuple(item for item in self.files if item.path.endswith('.md') and any(item.path==prefix or item.path.startswith(prefix) for prefix in prefixes))

    @property
    def downloads(self) -> tuple[PublishedFile,...]:
        # Reviewed policy: document release PDFs only; never every approved asset.
        return tuple(item for item in self.files if item.kind=='pdf')


def publication_sources(contracts: tuple[SourceContract,...], destinations: tuple[tuple[str,str,str],...]) -> tuple[PublicationSource,...]:
    return tuple(PublicationSource(contract.lock,tuple(sorted(contract.files,key=lambda item:item.path)),tuple(sorted(contract.notebooks,key=lambda item:item.path)),tuple(sorted((path,target) for source,path,target in destinations if source==contract.lock.name))) for contract in sorted(contracts,key=lambda item:item.lock.name))
