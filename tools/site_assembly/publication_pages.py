"""Consistent section indexes and explicitly eligible download metadata."""
from __future__ import annotations
import os
from pathlib import Path
from .models import InventoryEntry
from .publication import PublicationSource
from .presentation import Code, Link, MetadataRow, render_link, render_table, render_limitations
from .primitives import sha256_file


def _link(title: str,target: str,page: Path,root: Path) -> str:
    return render_link(Link(title,os.path.relpath(root/target,page.parent).replace(os.sep,'/')))


def stage_publication_indexes(sources: tuple[PublicationSource,...],inventory: tuple[InventoryEntry,...],root: Path,timestamp: str) -> None:
    receipts={(item.source,item.source_path):item for item in inventory}
    if len(receipts)!=len(inventory):raise ValueError('duplicate publication receipt')
    documents=[];notebooks=[];campaigns=[];downloads=[]
    for source in sources:
        for item in source.downloads:
            target=source.destination(item.path)
            receipt=receipts.get((source.lock.name,item.path))
            path=root/target
            if receipt is None or receipt.staged_path!=target or receipt.source_sha256!=receipt.staged_sha256 or sha256_file(path)!=receipt.staged_sha256:
                raise ValueError('download lacks an exact verified document receipt')
            documents.append('- '+_link(item.title,str(Path(target).with_suffix('.md')),root/'documents/index.md',root))
            download_link=Link(item.title+' (PDF)',os.path.relpath(path,(root/'downloads')).replace(os.sep,'/'))
            downloads.append(render_table((
                MetadataRow('Download',download_link), MetadataRow('Artifact type','PDF'),
                MetadataRow('Version or revision',item.version),MetadataRow('Document date',item.document_date or 'Not supplied'),
                MetadataRow('Publication status',item.publication_status),MetadataRow('Scientific validation status',item.validation_status or 'Not supplied'),
                MetadataRow('Source commit',Code(source.lock.commit)),MetadataRow('Source artifact',Link(item.path,source.lock.repository+'/blob/'+source.lock.commit+'/'+item.path)),
                MetadataRow('SHA-256',Code(receipt.staged_sha256)),MetadataRow('Bytes',str(path.stat().st_size)),
                MetadataRow('License',item.license),MetadataRow('Attribution',item.attribution),
            ))+'\n\nKnown limitations:\n\n'+render_limitations(item.known_limitations))
        for spec in source.notebooks:
            notebooks.append('- '+_link(spec.title,source.destination(spec.path),root/'software/notebooks/index.md',root)+'\n\n'+render_table((MetadataRow('Publication status',spec.publication_status),MetadataRow('Scientific validation status',spec.validation_status),MetadataRow('Package version',spec.package_version)))+'\n\n'+render_limitations(spec.known_limitations))
        for prefix,slug,title in [('reference_6p7nm','6-7-nm','6.7 nm reference campaign'),('reference_13p5nm','13-5-nm','13.5 nm reference campaign')]:
            selected=tuple(item for item in source.files if item.path.startswith('campaigns/'+prefix+'/'))
            if selected:
                campaigns.append('- '+_link(title,'campaigns/'+slug+'.md',root/'campaigns/index.md',root)+'\n\n'+render_table((MetadataRow('Publication status',selected[0].publication_status),MetadataRow('Scientific validation status',selected[0].validation_status or 'Not supplied'))))
    for relative,title,items,description in [
        ('documents/index.md','Approved documents',documents,'Only verified document releases appear here.'),
        ('campaigns/index.md','Approved reference campaigns',campaigns,'Campaign labels do not imply achieved performance or validation.'),
        ('software/notebooks/index.md','Static pyEUVICS notebooks',notebooks,'These pages are deterministic static renderings, not an interactive Jupyter environment.'),
        ('downloads/index.md','Downloads',downloads,'Only verified manifest-approved PDF document releases are eligible for this listing. Other approved material remains linked from its reviewed context.'),
    ]:
        path=root/relative;path.parent.mkdir(parents=True,exist_ok=True)
        content='\n\n'.join(items) if items else 'No approved items in this category are available in this assembled build.'
        path.write_text(f'# {title}\n\n{description}\n\nApproved items: {len(items)}.\n\n{content}\n\nBuild timestamp: {timestamp}\n',encoding='utf-8')
