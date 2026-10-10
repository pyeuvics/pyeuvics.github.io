"""Derive rendered source/correction actions from the immutable output plan."""
from __future__ import annotations
from dataclasses import asdict,dataclass
from urllib.parse import urlencode
from .models import SourceLock
from .presentation import source_url
from .staging import StagingPlan,OutputKind

WEBSITE='https://github.com/pyeuvics/pyeuvics.github.io'

@dataclass(frozen=True)
class PageActions:
    kind: str
    source: str
    correction: str
    correction_label: str


def correction_url(repository: str,reference: str) -> str:
    return repository+'/issues/new?'+urlencode({'body':'Correction concerning this published source: '+reference+'\n\nDescribe the correction and supporting evidence:\n'})


def page_actions(plan: StagingPlan,website_commit: str) -> dict[str,dict[str,str]]:
    result={}
    bindings={(item.source,item.output_path):item.source_path for item in plan.destinations}
    sources={item.lock.name:item for item in plan.publication}
    for output in plan.outputs:
        if not output.path.endswith('.md'):continue
        if output.kind==OutputKind.WEBSITE:
            continue  # Real tracked website source uses the configured branch edit link.
        source_name=output.owner if output.owner!='website' else None
        source_path=bindings.get((output.owner,output.path))
        if output.producer=='document-overview':
            related=output.related_outputs[0]
            source_name=next(item.source for item in plan.destinations if item.output_path==related)
            source_path=bindings[(source_name,related)]
        elif output.producer=='campaign-overview':
            source_name='pyeuvics';source_path=sources[source_name].lock.manifest_path
        if source_name is not None and source_path is not None:
            lock=sources[source_name].lock;reference=source_url(lock,source_path)
            action=PageActions('source-imported' if output.kind==OutputKind.IMPORT else 'source-generated',reference,correction_url(lock.repository,reference),'Propose a source correction')
        else:
            website_inputs=[item.removeprefix('website:') for item in output.inputs if item.startswith('website:content/')]
            producer='tools/site_assembly/publication_pages.py' if output.path.endswith('/index.md') else 'tools/site_assembly/entry_pages.py'
            source_path=website_inputs[0] if website_inputs else producer
            lock=SourceLock('website',WEBSITE,website_commit,'')
            reference=source_url(lock,source_path)
            action=PageActions('website-generated',reference,correction_url(WEBSITE,reference),'Propose a website correction')
        result[output.path]=asdict(action)
    return result
