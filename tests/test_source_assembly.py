from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from reportlab.pdfgen import canvas

from tools.site_assembly import AssemblyError, assemble_site
from tools.site_assembly.contracts import ContractError, _safe_path, load_contract, load_locks
from tools.site_assembly.models import SourceLock
from tools.site_assembly.pipeline import (
    MARKDOWN_EXTENSIONS,
    _css_targets,
    _RenderedLinkParser,
    _srcset_targets,
    _scan_text,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text", [r"C:\Users\fixture\private.txt", r"C:\\Users\\fixture\\private.txt", "C:/Users/fixture/private.txt", "github_pat_" + "A" * 30])
def test_artifact_scan_rejects_windows_paths_and_fine_grained_tokens(text: str) -> None:
    with pytest.raises(AssemblyError, match="local absolute path|credential-like"):
        _scan_text(text, "fixture")


def test_artifact_scan_accepts_web_urls_and_drive_name_documentation() -> None:
    _scan_text("https://pyeuvics.github.io/ and device names (c:\\)", "fixture")


@pytest.mark.parametrize("path", [".", "./private/file.md", "docs//file.md", "docs/./file.md", "docs/file\n.md"])
def test_noncanonical_publication_paths_are_rejected(path: str) -> None:
    with pytest.raises(ContractError, match="safe repository-relative"):
        _safe_path(path, "fixture")


@pytest.mark.parametrize("digest", [None, "invalid", "0" * 64, "valid"])
def test_euvics_v11_requires_exact_approved_bytes(tmp_path: Path, digest: str | None) -> None:
    manifest = euvics_manifest()
    manifest["schema_version"] = "1.1"
    manifest["allowlist"] = manifest["allowlist"][:1]
    content = "# Approved content\n"
    if digest is not None:
        manifest["allowlist"][0]["approval"]["sha256"] = (
            hashlib.sha256(content.encode()).hexdigest() if digest == "valid" else digest
        )
    source = tmp_path / "source"
    commit = create_repo(source, manifest, {"docs/overview.md": content})
    lock = SourceLock("euvics", "https://github.com/pyeuvics/euvics", commit, "publication/public-content-v1.json")
    if digest == "valid":
        assert len(load_contract(lock, source).files) == 1
    else:
        with pytest.raises(ContractError, match="approval|SHA-256"):
            load_contract(lock, source)


def test_allowlist_rejects_symlinked_parent(tmp_path: Path) -> None:
    source = tmp_path / "source"
    manifest = euvics_manifest("docs/overview.md")
    manifest["allowlist"] = manifest["allowlist"][:1]
    create_repo(source, manifest, {"private/overview.md": "# Excluded\n"})
    (source / "docs").symlink_to("private", target_is_directory=True)
    subprocess.run(["git", "add", "docs"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "Symlink fixture"], cwd=source, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    lock = SourceLock("euvics", "https://github.com/pyeuvics/euvics", commit, "publication/public-content-v1.json")
    with pytest.raises(ContractError, match="symlink"):
        load_contract(lock, source)


def test_rendered_resource_lists_ignore_css_comments_and_preserve_data_urls() -> None:
    assert _css_targets(
        "/* background: url(../private.png); */ background: url(public.png)"
    ) == ["public.png"]
    assert _srcset_targets(
        "data:image/png;base64,AAAA 1x, public.png 2x"
    ) == ["data:image/png;base64,AAAA", "public.png"]


@pytest.mark.parametrize(
    ("html", "unsafe"),
    [
        ('<script type="math/tex">a_0</script>', False),
        ('<script type="math/tex; mode=display">a_0</script>', False),
        ("<script>alert(1)</script>", True),
        ('<script type="text/javascript">alert(1)</script>', True),
        ('<script type="math/tex" src="evil.js"></script>', True),
        ('<iframe src="https://example.org"></iframe>', True),
    ],
)
def test_rendered_link_parser_only_allows_inert_math_script_tags(
    html: str, unsafe: bool
) -> None:
    parser = _RenderedLinkParser()
    parser.feed(html)
    assert parser.unsafe_active_content is unsafe


def test_publication_validator_uses_the_mkdocs_markdown_extensions() -> None:
    configuration = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    configured = [
        item if isinstance(item, str) else next(iter(item))
        for item in configuration["markdown_extensions"]
    ]
    assert configured == MARKDOWN_EXTENSIONS


def euvics_manifest(path: str = "docs/overview.md") -> dict:
    return {
        "$schema": "public-content-v1.schema.json",
        "schema_version": "1.0",
        "contract_id": "euvics-public-content-v1",
        "repository": {
            "url": "https://github.com/pyeuvics/euvics",
            "source_commit_policy": "locked-by-consuming-website",
        },
        "default_policy": "excluded",
        "allowlist": [
            {
                "path": path,
                "kind": "markdown" if path.endswith(".md") else "metadata",
                "title": "Generic overview",
                "version": "fixture-1",
                "publication_status": "public-draft",
                "approval": {
                    "status": "approved",
                    "approved_by": "fixture-owner",
                    "approved_on": "2026-08-02",
                },
                "license": "MIT",
                "attribution": "Synthetic fixture",
                "known_limitations": ["Synthetic test content only."],
            },
            {
                "path": "assets/diagram.svg",
                "kind": "image",
                "title": "Generic diagram",
                "version": "fixture-1",
                "publication_status": "released",
                "approval": {
                    "status": "approved",
                    "approved_by": "fixture-owner",
                    "approved_on": "2026-08-02",
                },
                "license": "MIT",
                "attribution": "Synthetic fixture",
                "known_limitations": [],
            },
        ],
        "exclusions": [],
        "publication_decisions": [],
    }


def pyeuvics_manifest() -> dict:
    return {
        "$schema": "public-content-v1.schema.json",
        "schema_version": "1.0",
        "contract_id": "pyeuvics-public-content-v1",
        "repository": {
            "url": "https://github.com/pyeuvics/pyEUVICS",
            "website_repository_url": "https://github.com/pyeuvics/pyeuvics.github.io",
            "website_url": "https://pyeuvics.github.io",
            "source_commit_policy": "locked-by-consuming-website",
        },
        "package": {
            "name": "pyEUVICS",
            "version": "0.0-fixture",
            "license": "MIT",
            "citation": "CITATION.cff",
            "documentation_status": "released-with-package",
            "known_scientific_limitations": [
                "Synthetic test content only.",
                "No external scientific validation.",
                "No experimental measurement is represented.",
            ],
        },
        "default_policy": "excluded",
        "unpublished_link_policy": "reject",
        "allowlist": ["docs/index.md", "docs/guide.md"],
        "candidate_sets": [],
        "excluded_prefixes": ["private/"],
    }


def pending_pyeuvics_set(**overrides: object) -> dict:
    candidate = {
        "name": "pending-static-fixture",
        "status": "approval-pending",
        "owner": "fixture-owner",
        "reason": "Synthetic pending publication fixture.",
        "files": ["notes/note.md"],
        "dependencies": [],
    }
    candidate.update(overrides)
    return candidate


def write_files(root: Path, files: dict[str, str | bytes]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")


def create_repo(root: Path, manifest: dict, files: dict[str, str | bytes]) -> str:
    root.mkdir()
    write_files(root, files)
    manifest_path = root / "publication/public-content-v1.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture Author"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Synthetic publication fixture"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def create_sources(tmp_path: Path, euvics: dict | None = None, pyeuvics: dict | None = None) -> tuple[Path, Path, dict[str, str]]:
    euvics_root = tmp_path / "euvics"
    pyeuvics_root = tmp_path / "pyeuvics"
    euvics_commit = create_repo(
        euvics_root,
        euvics or euvics_manifest(),
        {
            "docs/overview.md": "# Generic overview\n\n![Generic diagram](../assets/diagram.svg)\n",
            "assets/diagram.svg": '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Generic fixture"></svg>\n',
        },
    )
    pyeuvics_commit = create_repo(
        pyeuvics_root,
        pyeuvics or pyeuvics_manifest(),
        {
            "docs/index.md": "# Generic package\n\n[Guide](guide.md)\n",
            "docs/guide.md": "# Generic guide\n",
            "notes/note.md": "# Unpublished source note\n",
            "CITATION.cff": "cff-version: 1.2.0\n",
        },
    )
    return euvics_root, pyeuvics_root, {"euvics": euvics_commit, "pyeuvics": pyeuvics_commit}


def generic_pdf(label: str) -> bytes:
    from io import BytesIO

    stream = BytesIO()
    document = canvas.Canvas(stream, invariant=1, pageCompression=0)
    document.setTitle(label)
    document.drawString(72, 760, label)
    document.drawString(72, 740, "Synthetic publication test fixture - no scientific content.")
    document.showPage()
    document.save()
    return stream.getvalue()


def add_proposal_release(
    root: Path,
    *,
    rebuilt_matches: bool = True,
    make_fails: bool = False,
    log_marker: str | None = None,
    publication_status: str = "released",
    limitations: list[str] | None = None,
    document_path: str = "build/proposal/main.pdf",
    omit_build_output: bool = False,
) -> str:
    approved = generic_pdf("Approved generic proposal")
    rebuilt = approved if rebuilt_matches else generic_pdf("Different generic proposal")
    write_files(
        root,
        {
            document_path: approved,
            "document_sources/proposal.pdf": rebuilt,
        },
    )
    manifest_path = root / "publication/public-content-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["allowlist"].append(
        {
            "path": document_path,
            "kind": "pdf",
            "title": "Generic Proposal",
            "version": "fixture-r1",
            "document_date": "2026-08-02",
            "publication_status": publication_status,
            "approval": {
                "status": "approved",
                "approved_by": "fixture-owner",
                "approved_on": "2026-08-02",
            },
            "license": "MIT",
            "attribution": "Synthetic fixture",
            "known_limitations": (
                ["Synthetic document for pipeline testing only."]
                if limitations is None
                else limitations
            ),
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    verify_recipe = "\t@false\n" if make_fails else "\t@test -f document_sources/proposal.pdf\n"
    build_recipe = "\t@true\n" if omit_build_output else (
        "\t@mkdir -p build/proposal\n"
        "\t@cp document_sources/proposal.pdf build/proposal/main.pdf\n"
    )
    marker_recipe = ""
    if log_marker is not None:
        marker_recipe = (
            "\t@mkdir -p build/proposal\n"
            f"\t@printf '%s\\n' '{log_marker}' > build/proposal/main.log\n"
        )
    (root / "Makefile").write_text(
        ".PHONY: verify-archive check\n"
        "verify-archive:\n"
        f"{verify_recipe}"
        "check: verify-archive\n"
        f"{build_recipe}{marker_recipe}",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-f", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add synthetic approved document"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def notebook_bytes(code: str, *, with_output: bool = False) -> bytes:
    output = (
        [{"name": "stdout", "output_type": "stream", "text": "precomputed\n"}]
        if with_output
        else []
    )
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "fixture-introduction",
                "metadata": {},
                "source": ["# Synthetic deterministic notebook\n"],
            },
            {
                "cell_type": "code",
                "execution_count": 1 if with_output else None,
                "id": "fixture-code",
                "metadata": {},
                "outputs": output,
                "source": [code],
            },
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return (json.dumps(notebook, sort_keys=True) + "\n").encode()


def add_approved_notebook_set(
    root: Path,
    code: str,
    *,
    with_output: bool = False,
    max_source_bytes: int = 500_000,
    max_rendered_bytes: int = 500_000,
    add_unapproved_data: bool = False,
) -> str:
    notebook_path = "notebooks/00_environment_check.ipynb"
    files: dict[str, str | bytes] = {
        notebook_path: notebook_bytes(code, with_output=with_output),
        "configs/fixture.yaml": "fixture: true\n",
    }
    if add_unapproved_data:
        files["secret.csv"] = "excluded,value\n"
    write_files(root, files)
    manifest_path = root / "publication/public-content-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_sets"] = [
        {
            "name": "approved-static-notebook-fixture",
            "status": "approved",
            "owner": "fixture-owner",
            "reason": "Synthetic pipeline verification.",
            "approval": {
                "status": "approved",
                "approved_by": "fixture-owner",
                "approved_on": "2026-08-02",
            },
            "publication_status": "released",
            "validation_status": "synthetic-workflow-check-only",
            "known_limitations": ["Synthetic notebook; no scientific result."],
            "local_requirements": ["Python and the pinned pyEUVICS environment."],
            "execution_policy": "execute-during-build",
            "random_seed": 17,
            "configurations": ["configs/fixture.yaml"],
            "max_bytes_per_notebook": max_source_bytes,
            "max_rendered_bytes": max_rendered_bytes,
            "output_policy": "source-notebooks-must-have-no-outputs",
            "files": [notebook_path],
            "dependencies": ["configs/fixture.yaml"],
        }
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Approve synthetic notebook"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def add_approved_campaign_set(root: Path) -> str:
    write_files(
        root,
        {
            "campaigns/reference_6p7nm/README.md": "# Synthetic 6.7 nm campaign\n\n![Spectrum](figures/spectrum.svg)\n",
            "campaigns/reference_6p7nm/figures/spectrum.svg": (
                '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
                'aria-label="Synthetic spectrum"></svg>\n'
            ),
            "campaigns/reference_6p7nm/reports/scientific_report.md": "# Synthetic scientific report\n",
            "campaigns/reference_6p7nm/reports/validation.md": "# Synthetic validation report\n",
        },
    )
    manifest_path = root / "publication/public-content-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_sets"] = [
        {
            "name": "approved-campaign-fixture",
            "status": "approved",
            "owner": "fixture-owner",
            "reason": "Synthetic pipeline verification.",
            "approval": {
                "status": "approved",
                "approved_by": "fixture-owner",
                "approved_on": "2026-08-02",
            },
            "publication_status": "released",
            "validation_status": "synthetic-workflow-check-only",
            "known_limitations": ["Synthetic campaign; no scientific result."],
            "local_requirements": ["No local execution; static approved source material."],
            "files": [
                "campaigns/reference_6p7nm/README.md",
                "campaigns/reference_6p7nm/figures/spectrum.svg",
                "campaigns/reference_6p7nm/reports/scientific_report.md",
                "campaigns/reference_6p7nm/reports/validation.md",
            ],
            "dependencies": [],
        }
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Approve synthetic campaign"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def write_locks(path: Path, commits: dict[str, str]) -> Path:
    data = {
        "schema_version": 1,
        "sources": {
            "euvics": {
                "repository": "https://github.com/pyeuvics/euvics",
                "commit": commits["euvics"],
                "lock_status": "locked",
                "publication_manifest": "publication/public-content-v1.json",
            },
            "pyeuvics": {
                "repository": "https://github.com/pyeuvics/pyEUVICS",
                "commit": commits["pyeuvics"],
                "lock_status": "locked",
                "publication_manifest": "publication/public-content-v1.json",
            },
        },
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def run_assembly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    output = tmp_path / "assembly"
    assemble_site(ROOT, lock, euvics, pyeuvics, output)
    return euvics, pyeuvics, output


def test_successful_assembly_is_deterministic_and_preserves_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    before = {"euvics": snapshot(euvics), "pyeuvics": snapshot(pyeuvics)}
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    first = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "assembly-a")
    second = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "assembly-b")
    assert snapshot(euvics) == before["euvics"]
    assert snapshot(pyeuvics) == before["pyeuvics"]
    first_inventory = (first.output_root / "staged-content-inventory.json").read_bytes()
    second_inventory = (second.output_root / "staged-content-inventory.json").read_bytes()
    assert first_inventory == second_inventory
    assert len(first.inventory) == 4
    overview = first.staged_content / "imported/euvics/docs/overview.md"
    assert "../assets/diagram.svg" in overview.read_text(encoding="utf-8")
    package_index = first.staged_content / "imported/pyeuvics/docs/index.md"
    package_text = package_index.read_text(encoding="utf-8")
    assert "guide.md" in package_text
    assert "notes/note.md" not in package_text
    assert "## Provenance" in package_text
    staged_home = (first.staged_content / "index.md").read_text(encoding="utf-8")
    assert "2 manifest-approved pyEUVICS files" in staged_home
    assert commits["pyeuvics"] in staged_home
    project_overview = (first.staged_content / "project/overview.md").read_text(
        encoding="utf-8"
    )
    assert "## Assembled build provenance" in project_overview
    assert commits["euvics"] in project_overview
    assert commits["pyeuvics"] in project_overview
    assert "../imported/euvics/docs/overview.md" in project_overview
    assert (
        f"https://github.com/pyeuvics/euvics/tree/{commits['euvics']}"
        in project_overview
    ), "overview provenance must link to the exact EUVICS commit"
    assert (
        f"https://github.com/pyeuvics/pyEUVICS/tree/{commits['pyeuvics']}"
        in project_overview
    ), "overview provenance must link to the exact pyEUVICS commit"
    assert "/tree/main" not in project_overview and "/tree/master" not in project_overview
    expected_paths = {
        "euvics": {"docs/overview.md", "assets/diagram.svg"},
        "pyeuvics": {"docs/index.md", "docs/guide.md"},
    }
    for source_name, paths in expected_paths.items():
        inventory_paths = {
            item.source_path for item in first.inventory if item.source == source_name
        }
        assert inventory_paths == paths, (
            f"assembled {source_name} inventory must exactly match its fixture allowlist"
        )
    assert not (first.staged_content / "imported/pyeuvics/notes/note.md").exists(), (
        "unlisted pyEUVICS paths must not enter staged content"
    )
    assert not (first.site / "imported/pyeuvics/notes/note/index.html").exists(), (
        "unlisted pyEUVICS paths must not enter the generated site"
    )
    installation = (first.staged_content / "software/installation.md").read_text(
        encoding="utf-8"
    )
    assert "../imported/pyeuvics/docs/index.md" in installation
    assert "0.0-fixture" in installation
    assert (first.site / "imported/euvics/docs/overview/index.html").is_file()
    assert (first.site / "imported/staged-content-inventory.json").is_file()
    imported_html = (first.site / "imported/pyeuvics/docs/index.html").read_text(
        encoding="utf-8"
    )
    assert "edit/main/content/imported/" not in imported_html
    assert f"pyEUVICS/edit/{commits['pyeuvics']}/docs/index.md" in imported_html
    website_html = (first.site / "software/installation/index.html").read_text(
        encoding="utf-8"
    )
    assert "edit/main/content/software/installation.md" in website_html
    overview_html = (first.site / "project/overview/index.html").read_text(
        encoding="utf-8"
    )
    assert (
        'href="https://pyeuvics.github.io/project/overview/"'
        in overview_html
    ), "overview canonical URL must use the organization-site root path"
    assert 'src="../../assets/images/ics-geometry-source-chain.svg"' in overview_html
    assert 'aria-describedby="ics-schematic-caption"' in overview_html
    assert 'alt="Schematic of an electron bunch traveling left to right' in overview_html
    assert (
        f'href="https://github.com/pyeuvics/euvics/tree/{commits["euvics"]}"'
        in overview_html
    )


def test_production_locks_are_resolved() -> None:
    locks = load_locks(ROOT / "sources.lock.yml")
    assert set(locks) == {"euvics", "pyeuvics"}
    assert all(len(lock.commit) == 40 for lock in locks.values())


def test_commit_mismatch_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    actual = commits["euvics"]
    commits["euvics"] = "0" * 40
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError) as caught:
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")
    message = str(caught.value)
    assert "commit mismatch for euvics" in message
    assert f"expected {'0' * 40}" in message
    assert f"got {actual}" in message


def test_dirty_source_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    (euvics / "untracked.txt").write_text("not committed\n", encoding="utf-8")
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="dirty"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda manifest: manifest["allowlist"][0].update(path="../outside.md"), "exact safe"),
        (
            lambda manifest: manifest["allowlist"][0]["approval"].update(status="pending"),
            "missing explicit publication approval",
        ),
        (lambda manifest: manifest.update(unknown=True), "fields invalid"),
        (
            lambda manifest: manifest["exclusions"].append(
                {"path_prefix": "docs/", "category": "internal", "reason": "fixture"}
            ),
            "leaks from EUVICS exclusions",
        ),
    ],
)
def test_invalid_euvics_contract_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    message: str,
) -> None:
    manifest = copy.deepcopy(euvics_manifest())
    mutation(manifest)
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


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
    """pymdownx.arithmatex renders every equation as an inert `<script
    type="math/tex">` data island for client-side MathJax; real pyEUVICS
    documentation is full of these and must not trip the active-content
    boundary."""
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


def test_unexpected_allowlisted_type_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = euvics_manifest("payload.exe")
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    (euvics / "payload.exe").write_bytes(b"fixture executable")
    subprocess.run(["git", "add", "."], cwd=euvics, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add unexpected type"], cwd=euvics, check=True)
    commits["euvics"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=euvics, text=True
    ).strip()
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="kind and file extension disagree"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


def test_missing_allowlisted_path_reports_source_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = euvics_manifest("docs/missing-overview.md")
    euvics, pyeuvics, commits = create_sources(tmp_path, euvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError) as caught:
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")
    message = str(caught.value)
    assert "allowlisted source file is missing" in message
    assert "docs/missing-overview.md" in message


def test_pyeuvics_exclusion_leakage_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = pyeuvics_manifest()
    manifest["excluded_prefixes"].append("docs/")
    euvics, pyeuvics, commits = create_sources(tmp_path, pyeuvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="leaks from pyEUVICS exclusions"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda manifest: manifest.update(schema_version="2.0"), "identity or policy"),
        (
            lambda manifest: manifest["repository"].update(
                website_url="https://example.invalid"
            ),
            "repository identity",
        ),
        (
            lambda manifest: manifest["package"].update(
                known_scientific_limitations=[]
            ),
            "scientific limitations",
        ),
        (
            lambda manifest: manifest["candidate_sets"].append(
                pending_pyeuvics_set(files=[])
            ),
            "non-empty array",
        ),
        (
            lambda manifest: manifest["candidate_sets"].append(
                pending_pyeuvics_set(files=["notes/missing.md"])
            ),
            "source file is missing",
        ),
        (
            lambda manifest: manifest["candidate_sets"].extend(
                [pending_pyeuvics_set(), pending_pyeuvics_set(files=["CITATION.cff"])]
            ),
            "duplicate pyEUVICS candidate name",
        ),
    ],
)
def test_invalid_pyeuvics_contract_declarations_are_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
    message: str,
) -> None:
    manifest = pyeuvics_manifest()
    mutation(manifest)
    euvics, pyeuvics, commits = create_sources(tmp_path, pyeuvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
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


def test_existing_output_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="already exists"):
        assemble_site(ROOT, lock, euvics, pyeuvics, output)


def test_command_line_assembly(tmp_path: Path) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    output = tmp_path / "cli-output"
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = "1785628800"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/assemble_site.py"),
            "--website-root",
            str(ROOT),
            "--lock",
            str(lock),
            "--euvics-source",
            str(euvics),
            "--pyeuvics-source",
            str(pyeuvics),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "assembled 4 approved files" in result.stdout
    assert (output / "site/index.html").is_file()


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


def test_approved_notebook_is_executed_deterministically_and_source_is_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    code = (
        "from pathlib import Path\n"
        "from IPython.display import Image, display\n"
        "import base64\n"
        "print('seed=17', Path('configs/fixture.yaml').read_text().strip())\n"
        "display(Image(data=base64.b64decode("
        "'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='"
        "), format='png'))\n"
    )
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code)
    before = snapshot(pyeuvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    first = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-a")
    second = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-b")
    assert snapshot(pyeuvics) == before
    page = first.staged_content / "software/notebooks/00_environment_check.md"
    text = page.read_text(encoding="utf-8")
    assert "Static notebook rendering" in text
    assert "Executed during this website build" in text
    assert "synthetic-workflow-check-only" in text
    assert commits["pyeuvics"] in text
    assert "seed=17 fixture: true" in text
    assets = list(
        (first.staged_content / "software/notebooks/00_environment_check_files").glob("*.png")
    )
    assert len(assets) == 1
    assert (first.site / "software/notebooks/00_environment_check/index.html").is_file()
    assert (first.output_root / "staged-content-inventory.json").read_bytes() == (
        second.output_root / "staged-content-inventory.json"
    ).read_bytes()


def test_approved_notebook_writes_only_to_isolated_runtime_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    code = (
        "import os\n"
        "from pathlib import Path\n"
        "output = Path(os.environ['PYEUVICS_NOTEBOOK_OUTPUT'])\n"
        "output.mkdir(parents=True, exist_ok=True)\n"
        "(output / 'status.txt').write_text('ok\\n', encoding='utf-8')\n"
        "print(output.as_posix(), (output / 'status.txt').read_text().strip())\n"
        "print('token=' + os.environ.get('GITHUB_TOKEN', 'absent'))\n"
    )
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code)
    before = snapshot(pyeuvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    result = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "runtime-output")
    assert snapshot(pyeuvics) == before
    rendered = (
        result.staged_content / "software/notebooks/00_environment_check.md"
    ).read_text(encoding="utf-8")
    assert "../notebook-runtime-output/00_environment_check ok" in rendered
    assert "token=absent" in rendered
    assert "ghp_" not in rendered


@pytest.mark.parametrize(
    ("code", "options", "message"),
    [
        ("print('precomputed')\n", {"with_output": True}, "contains outputs"),
        ("raise RuntimeError('fixture failure')\n", {}, "execution failed"),
        ("import random\nprint(random.random())\n", {}, "nondeterministic"),
        (
            "from pathlib import Path\nprint(Path('secret.csv').read_text())\n",
            {"add_unapproved_data": True},
            "unapproved data dependency",
        ),
        ("print('oversized source')\n", {"max_source_bytes": 10}, "source size limit"),
        ("print('oversized render')\n", {"max_rendered_bytes": 10}, "rendered notebook exceeds"),
    ],
)
def test_notebook_publication_failure_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    code: str,
    options: dict,
    message: str,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["pyeuvics"] = add_approved_notebook_set(pyeuvics, code, **options)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match=message):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "notebook-output")


def test_approved_campaign_material_replaces_placeholder_and_preserves_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["pyeuvics"] = add_approved_campaign_set(pyeuvics)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    result = assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "campaign-output")
    overview = (result.staged_content / "campaigns/6-7-nm.md").read_text(encoding="utf-8")
    assert "synthetic-workflow-check-only" in overview
    assert "../imported/pyeuvics/campaigns/reference_6p7nm/README.md" in overview
    campaign = result.staged_content / "imported/pyeuvics/campaigns/reference_6p7nm/README.md"
    assert "figures/spectrum.svg" in campaign.read_text(encoding="utf-8")
    assert (result.site / "campaigns/6-7-nm/index.html").is_file()
