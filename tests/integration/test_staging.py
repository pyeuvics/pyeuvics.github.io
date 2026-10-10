from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tools.site_assembly import AssemblyError, assemble_site
from tools.site_assembly.contracts import (
    ContractError,
    load_contract,
    load_locks,
)

from tests.support.publication import (
    pyeuvics_manifest,
    create_sources,
    add_approved_campaign_set,
    write_locks,
    snapshot,
)

from tests.support.paths import ROOT


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


def test_pyeuvics_exclusion_leakage_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = pyeuvics_manifest()
    manifest["excluded_prefixes"].append("docs/")
    euvics, pyeuvics, commits = create_sources(tmp_path, pyeuvics=manifest)
    lock = write_locks(tmp_path / "sources.lock.yml", commits)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    with pytest.raises(ContractError, match="leaks from pyEUVICS exclusions"):
        load_contract(load_locks(lock)["pyeuvics"], pyeuvics)


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
