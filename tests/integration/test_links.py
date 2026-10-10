from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.site_assembly import AssemblyError, assemble_site

from tests.support.publication import (
    pyeuvics_manifest,
    create_sources,
    write_locks,
)

from tests.support.paths import ROOT


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("# Broken\n\n[Missing](missing.md)\n", "broken or unpublished link"),
        ("# Local\n\nUse /Users/example/private/input.csv\n", "local absolute path"),
        ("# Secret\n\nghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n", "credential-like"),
        ("# Active\n\n<script>alert('unsafe')</script>\n", "unsafe active content"),
        ("# Active\n\n[unsafe](javascript:alert(1))\n", "unsupported link scheme"),
    ],
)
def test_unsafe_source_markdown_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    message: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (euvics / "docs/overview.md").write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=euvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Unsafe fixture variant"], cwd=euvics, check=True)
    commits["euvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=euvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


def test_arithmatex_math_script_is_not_rejected_as_unsafe_active_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reviewed math markup remains valid with the site's generic renderer."""
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (euvics / "docs/overview.md").write_text(
        "# Math\n\nInline \\(a_0\\) and display:\n\n\\[\n\\gamma = 1+\\frac{K_e}{m_ec^2}\n\\]\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=euvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Math fixture"], cwd=euvics, check=True)
    commits["euvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=euvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


def test_pyeuvics_unpublished_link_policy_and_targets_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = pyeuvics_manifest()
    manifest["unpublished_link_policy"] = "rewrite-to-locked-source"
    euvics, pyeuvics, commits = create_sources(tmp_path, pyeuvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="unpublished-link policy"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "policy-output")

    manifest["unpublished_link_policy"] = "reject"
    (tmp_path / "target-case").mkdir()
    euvics, pyeuvics, commits = create_sources(
        tmp_path / "target-case", pyeuvics=manifest
    )
    (pyeuvics / "docs/index.md").write_text(
        "# Generic package\n\n[Private](../notes/note.md)\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=pyeuvics, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Add unpublished fixture link"],
        cwd=pyeuvics,
        check=True,
    )
    commits["pyeuvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=pyeuvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "target-case/sources.lock.yml", commits)
    with pytest.raises(AssemblyError, match="broken or unpublished link"):
        assemble_site(
            ROOT, lock, euvics, pyeuvics, tmp_path / "target-case/target-output"
        )


@pytest.mark.parametrize(
    "source",
    [
        "[Private][note]\n\n[note]: ../notes/note.md\n",
        '<a href="../notes/note.md">Private</a>\n',
        '<img src="../notes/private.png" alt="Private">\n',
        '<video poster="../notes/private.png"></video>\n',
        '<source srcset="../notes/private.png 1x">\n',
        '<form action="../notes/submit"></form>\n',
        '<div style="background-image: url(../notes/private.png)"></div>\n',
        '<div markdown="1">\n[Private](../notes/note.md)\n</div>\n',
    ],
)
def test_rendered_markdown_link_forms_cannot_bypass_publication_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (pyeuvics / "docs/index.md").write_text(source, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=pyeuvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add link form"], cwd=pyeuvics, check=True)
    commits["pyeuvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=pyeuvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="broken or unpublished link"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


@pytest.mark.parametrize("example", [
    "```markdown\n[Private][note]\n\n[note]: ../notes/note.md\n```\n",
    "```markdown\n[Private](../notes/note.md)\n```\n",
    "Example: `[Private](../notes/note.md)`\n",
    "```markdown\n[Example](javascript:example)\n```\n",
])
def test_rendered_markdown_ignores_link_examples_in_fenced_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    example: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (pyeuvics / "docs/index.md").write_text(
        example,
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=pyeuvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add fenced example"], cwd=pyeuvics, check=True)
    commits["pyeuvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=pyeuvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    result = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")
    assert (result.site / "imported/pyeuvics/docs/index.html").is_file()
    assert example in (result.staged_content / "imported/pyeuvics/docs/index.md").read_text()


@pytest.mark.parametrize(
    "source",
    [
        "<script>alert('unsafe')</script>\n",
        '<iframe src="https://example.org"></iframe>\n',
        '<object data="https://example.org/document.pdf"></object>\n',
        '<svg onload="alert(1)"></svg>\n',
        '[unsafe](javascript:alert(1))\n',
        '[Guide](guide.md){: onclick="alert(1)"}\n',
    ],
)
def test_rendered_markdown_rejects_active_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (pyeuvics / "docs/index.md").write_text(source, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=pyeuvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add active content"], cwd=pyeuvics, check=True)
    commits["pyeuvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=pyeuvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="unsafe active content|unsupported link scheme"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")
