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
from tools.site_assembly.contracts import load_locks

ROOT = Path(__file__).resolve().parents[1]


def euvics_manifest(path: str = "docs/overview.md") -> dict:
    return {
        "$schema": "public-content-v1.schema.json",
        "schema_version": "1.0",
        "contract_id": "euvics-public-content-v1",
        "repository": {
            "url": "https://github.com/chongshikpark/euvics",
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
            "url": "https://github.com/chongshikpark/pyEUVICS",
            "source_commit_policy": "locked-by-consuming-website",
        },
        "package": {
            "name": "pyEUVICS",
            "version": "0.0-fixture",
            "license": "MIT",
            "citation": "CITATION.cff",
            "documentation_status": "released-with-package",
            "known_scientific_limitations": ["Synthetic test content only."],
        },
        "default_policy": "excluded",
        "unpublished_link_policy": "rewrite-to-locked-source",
        "allowlist": ["docs/index.md", "docs/guide.md"],
        "candidate_sets": [],
        "excluded_prefixes": ["private/"],
    }


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
            "docs/index.md": "# Generic package\n\n[Guide](guide.md)\n\n[Source note](../notes/note.md)\n",
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


def write_locks(path: Path, commits: dict[str, str]) -> Path:
    data = {
        "schema_version": 1,
        "sources": {
            "euvics": {
                "repository": "https://github.com/chongshikpark/euvics",
                "commit": commits["euvics"],
                "lock_status": "locked",
                "publication_manifest": "publication/public-content-v1.json",
            },
            "pyeuvics": {
                "repository": "https://github.com/chongshikpark/pyEUVICS",
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
    assert f"/blob/{commits['pyeuvics']}/notes/note.md" in package_text
    assert "## Provenance" in package_text
    assert (first.site / "imported/euvics/docs/overview/index.html").is_file()
    assert (first.site / "imported/staged-content-inventory.json").is_file()


def test_production_locks_are_resolved() -> None:
    locks = load_locks(ROOT / "sources.lock.yml")
    assert set(locks) == {"euvics", "pyeuvics"}
    assert all(len(lock.commit) == 40 for lock in locks.values())


def test_commit_mismatch_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    euvics, pyeuvics, commits = create_sources(tmp_path)
    commits["euvics"] = "0" * 40
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(AssemblyError, match="commit mismatch"):
        assemble_site(ROOT, lock, euvics, pyeuvics, tmp_path / "output")


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
