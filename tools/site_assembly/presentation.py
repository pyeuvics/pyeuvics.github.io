"""Typed website page views; source metadata is always plain text."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
from urllib.parse import quote

from .content_policy import URLUse, validate_url
from .models import SourceLock


def plain_text(value: str) -> str:
    """Escape HTML text without altering its Unicode content."""
    return escape(value, quote=False)


def attribute_text(value: str) -> str:
    return escape(value, quote=True).replace('\r', '&#13;').replace('\n', '&#10;').replace('\t', '&#9;')


def markdown_text(value: str) -> str:
    """Literal metadata: protect Markdown syntax and retain explicit line breaks."""
    text = plain_text(value)
    text = ''.join(f'&#{ord(char)};' if char in '\\`*_[]{}|$#+' else char for char in text)
    text = re.sub(r'^(\s*)(-)(?=\s)', r'\1&#45;', text)
    text = re.sub(r'^(\s*\d+)[.)](?=\s)', r'\1&#46;', text)
    text = text.replace('\r\n','\n').replace('\r','\n').replace('\n','<br>').replace('\t', '&#9;')
    return re.sub(r'^ +| +$', lambda match: '&#32;' * len(match.group()), text)


def table_cell(value: str) -> str:
    return markdown_text(value)


def url_target(value: str) -> str:
    validate_url(value, URLUse.NAVIGATION)
    return quote(value, safe='/:#?&=%@+,-._~!')


@dataclass(frozen=True)
class Link:
    label: str
    target: str
    commit: str | None = None


@dataclass(frozen=True)
class Code:
    value: str


@dataclass(frozen=True)
class MetadataRow:
    label: str
    value: str | Link | Code


def render_link(link: Link) -> str:
    label = markdown_text(link.label)
    if link.commit is not None:
        label += ' at ' + render_value(Code(link.commit))
    return f'[{label}]({url_target(link.target)})'


def render_value(value: str | Link | Code) -> str:
    if isinstance(value, Link):
        return render_link(value)
    if isinstance(value, Code):
        return '<code>' + markdown_text(value.value) + '</code>'
    return table_cell(value)


def render_table(rows: tuple[MetadataRow, ...]) -> str:
    return '| Field | Value |\n| --- | --- |\n' + '\n'.join(
        f'| {table_cell(row.label)} | {render_value(row.value)} |' for row in rows
    )


def render_fields(rows: tuple[MetadataRow, ...]) -> str:
    return '\n'.join(f'- **{markdown_text(row.label)}:** {render_value(row.value)}' for row in rows)


def render_limitations(values: tuple[str, ...], empty: str = 'None recorded by the source contract.') -> str:
    return '\n'.join('- ' + markdown_text(value) for value in values or (empty,))


def source_url(lock: SourceLock, path: str, *, edit: bool = False, directory: bool = False) -> str:
    action = 'edit' if edit else ('tree' if directory else 'blob')
    return f'{lock.repository}/{action}/{lock.commit}/{quote(path, safe="/")}'


@dataclass(frozen=True)
class DocumentPage:
    title: str
    status: str
    download: Link
    fields: tuple[MetadataRow, ...]
    limitations: tuple[str, ...]
    provenance: tuple[MetadataRow, ...]


def render_document(page: DocumentPage) -> str:
    return f'''# {markdown_text(page.title)}

<span class="status-badge">{markdown_text(page.status)}</span>

{render_link(page.download)}{{ .md-button }}

## Publication metadata

{render_table(page.fields)}

## Known limitations and review status

{render_limitations(page.limitations)}

## Provenance

{render_fields(page.provenance)}
'''


@dataclass(frozen=True)
class NotebookPage:
    title: str
    fields: tuple[MetadataRow, ...]
    requirements: tuple[str, ...]
    limitations: tuple[str, ...]


def render_notebook(page: NotebookPage) -> str:
    return f'''# {markdown_text(page.title)}

!!! info "Static notebook rendering"
    This page is a static build artifact. It is not a running Python or Jupyter environment.

{render_table(page.fields)}

## Expected local execution requirements

{render_limitations(page.requirements)}

## Known limitations

{render_limitations(page.limitations)}

## Rendered notebook

'''
