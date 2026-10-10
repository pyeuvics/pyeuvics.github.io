"""Synthetic builders with explicit mutation knobs for invalid publication cases.

Any is intentional at the fixture boundary: tests construct malformed values.
Production parsers never manufacture expected fixture data.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.site_assembly.models import NotebookSpec

import yaml
from reportlab.pdfgen import canvas  # type: ignore[import-untyped]  # ReportLab has no bundled types.


def init_repo(root: Path) -> None:
    """Initialize a synthetic repo with explicit local identity and no hooks/signing."""
    subprocess.run(["git", "init", "-q", "--initial-branch=main", "--template="], cwd=root, check=True)
    for key, value in {
        "user.name": "Fixture Author",
        "user.email": "fixture@example.invalid",
        "commit.gpgsign": "false",
        "core.hooksPath": "/dev/null",
    }.items():
        subprocess.run(["git", "config", key, value], cwd=root, check=True)


def euvics_manifest(path: str = "docs/overview.md") -> dict[str, Any]:
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



def pyeuvics_manifest() -> dict[str, Any]:
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



def pending_pyeuvics_set(**overrides: object) -> dict[str, Any]:
    candidate: dict[str, Any] = {
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



def create_repo(root: Path, manifest: dict[str, Any], files: dict[str, str | bytes]) -> str:
    root.mkdir()
    write_files(root, files)
    manifest_path = root / "publication/public-content-v1.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    init_repo(root)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Synthetic publication fixture"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()



def create_sources(tmp_path: Path, euvics: dict[str, Any] | None = None, pyeuvics: dict[str, Any] | None = None) -> tuple[Path, Path, dict[str, str]]:
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


def notebook_spec() -> "NotebookSpec":
    from tools.site_assembly.models import NotebookSpec
    return NotebookSpec('fixture.ipynb','Fixture','0-fixture','released','MIT','Synthetic','execute-during-build','17',(),(),'synthetic',(),(),100000,100000)
