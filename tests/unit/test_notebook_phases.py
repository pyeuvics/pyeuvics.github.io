"""Notebook phase contracts preserve prose while constraining rendered output."""
from pathlib import Path
import nbformat
import pytest
from tools.site_assembly.models import NotebookSpec
from tools.site_assembly.notebook_policy import ExecutedNotebook,NotebookError
from tools.site_assembly.notebook_admission import admit_notebook
from tools.site_assembly.notebook_rendering import render_executed
from tools.site_assembly.notebook_headings import normalize_headings
from tools.site_assembly.rendering import load_renderer


def spec() -> NotebookSpec:
    return NotebookSpec('fixture.ipynb','Fixture','0-fixture','released','MIT','Synthetic','execute-during-build','17',(),(),'synthetic',(),(),100000,100000)


def test_heading_normalization_preserves_scientific_prose_code_and_destinations() -> None:
    source='# Kinetic energy $E_k$\n\n## [Reference](guide.md)\n\nSetext **title**\n=====\n\n<h2 id="raw">Raw title</h2>\n\n```markdown\n# Literal heading\n```\n\n`<h1>literal</h1>`\n'
    normalized=normalize_headings(source)
    assert '## Kinetic energy $E_k$' in normalized
    assert '### [Reference](guide.md)' in normalized
    assert '## Setext **title**' in normalized
    assert '<h3 id="raw">Raw title</h3>' in normalized
    assert '```markdown\n# Literal heading\n```' in normalized
    assert '`<h1>literal</h1>`' in normalized
    assert '<h1' not in load_renderer().render(normalized)


@pytest.mark.parametrize('source',['> # Quoted title\n','- # List title\n','<h1>\n# Literal mark\n</h1>\n'])
def test_heading_context_is_checked_with_actual_renderer(source: str) -> None:
    assert '<h1' not in load_renderer().render(normalize_headings(source))


def test_admission_is_bounded_and_does_not_execute(tmp_path: Path) -> None:
    notebook=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell('raise AssertionError("must not execute")')])
    path=tmp_path/'fixture.ipynb';path.write_text(nbformat.writes(notebook),encoding='utf-8');before=path.read_bytes()
    admitted=admit_notebook(spec(),tmp_path)
    assert admitted.spec==spec() and not admitted.notebook.cells[0].outputs
    assert path.read_bytes()==before


@pytest.mark.parametrize('mime',['text/html','image/svg+xml','application/javascript'])
def test_rendering_rejects_unapproved_mime_without_execution(mime: str) -> None:
    notebook=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell('pass',outputs=[nbformat.v4.new_output('display_data',data={mime:'unsafe'})])])
    with pytest.raises(NotebookError,match='MIME'):
        render_executed(ExecutedNotebook(spec(),notebook))


@pytest.mark.parametrize('name,value',[('../escape.png',b'x'),('fixture_files/../escape.png',b'x'),('other/output.png',b'x'),('fixture_files//output.png',b'x'),('fixture_files/output.png','not bytes'),('fixture_files/output.svg',b'<svg/>'),('fixture_files/output.png',b'invalid PNG')])
def test_exporter_resources_are_validated_before_staging(monkeypatch,name,value) -> None:
    monkeypatch.setattr('tools.site_assembly.notebook_rendering.MarkdownExporter.from_notebook_node',lambda *a,**k:('public',{'outputs':{name:value}}))
    notebook=nbformat.v4.new_notebook()
    with pytest.raises(NotebookError,match='resource|asset'):
        render_executed(ExecutedNotebook(spec(),notebook))


def test_normalized_presentation_respects_rendered_byte_limit(monkeypatch) -> None:
    from dataclasses import replace
    monkeypatch.setattr('tools.site_assembly.notebook_rendering.MarkdownExporter.from_notebook_node',lambda *a,**k:('# Title',{'outputs':{}}))
    notebook=nbformat.v4.new_notebook()
    with pytest.raises(NotebookError,match='rendered notebook exceeds'):
        render_executed(ExecutedNotebook(replace(spec(),max_rendered_bytes=len('# Title')),notebook))
