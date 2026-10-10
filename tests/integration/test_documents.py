from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.site_assembly import AssemblyError, assemble_site

from tests.support.publication import (
    create_sources,
    add_proposal_release,
    write_locks,
    snapshot,
)

from tests.support.paths import ROOT


def test_approved_proposal_is_rebuilt_staged_and_described(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["euvics"] = add_proposal_release(euvics)
    before = snapshot(euvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    result = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "document-output")
    assert snapshot(euvics) == before
    staged_pdf = result.staged_content / "documents/proposal.pdf"
    assert staged_pdf.read_bytes() == (euvics / "build/proposal/main.pdf").read_bytes()
    overview = (result.staged_content / "documents/proposal.md").read_text(encoding="utf-8")
    checksum = hashlib.sha256(staged_pdf.read_bytes()).hexdigest()
    assert "# Generic Proposal" in overview
    assert "fixture-r1" in overview
    assert "2026-08-02" in overview
    assert checksum in overview
    assert commits["euvics"] in overview
    assert (result.site / "documents/proposal.pdf").is_file()
    assert (result.site / "documents/proposal/index.html").is_file()
    html=(result.site / "documents/proposal/index.html").read_text(encoding="utf-8")
    assert 'data-page-ownership="source-generated"' in html
    assert 'euvics/issues/new?' in html
    assert 'edit/main/content/documents/proposal.md' not in html
    pdf_entry = next(
        item for item in result.inventory if item.source_path == "build/proposal/main.pdf"
    )
    assert pdf_entry.source_sha256 == checksum
    assert pdf_entry.staged_sha256 == checksum


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"rebuilt_matches": False}, "checksum does not match"),
        ({"make_fails": True}, "make verify-archive failed"),
        ({"log_marker": "There were undefined references"}, "unresolved citation"),
        ({"publication_status": "public-draft"}, "explicitly released PDF"),
        ({"limitations": []}, "known limitations"),
        ({"document_path": "archive/proposal.pdf"}, "unrecognized approved document path"),
        ({"omit_build_output": True}, "build output is missing"),
    ],
)
def test_document_publication_failure_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options: dict,
    message: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["euvics"] = add_proposal_release(euvics, **options)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "document-output")
