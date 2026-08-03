from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "content/project/overview.md"


def test_project_overview_replaces_placeholder_with_required_science() -> None:
    text = OVERVIEW.read_text(encoding="utf-8")
    for heading in (
        "## EUVICS at a glance",
        "## How inverse Compton scattering works",
        "## The kinematic idea",
        "## How EUV radiation is produced",
        "## What sets wavelength, spectrum, and signal",
        "## What pyEUVICS calculates",
        "## Design and validation status",
        "## Sources and further reading",
    ):
        assert heading in text
    assert "Awaiting approved material" not in text
    assert "\\gamma = 1 + \\frac{K_e}{m_ec^2}" in text
    assert "1-\\cos(\\alpha-\\theta)" in text
    assert "\\(\\theta=0\\)" in text
    assert "\\(\\lambda_L\\)" in text and "\\(\\lambda_s\\)" in text
    assert "\\(0^\\circ\\)" in text and "\\(180^\\circ\\)" in text
    assert "\t" not in text


def test_project_overview_preserves_validation_boundaries() -> None:
    text = OVERVIEW.read_text(encoding="utf-8")
    for statement in (
        "Known disagreement",
        "no empirical correction is justified",
        "Provisional",
        "not measured detector calibration",
        "not relative harmonic yields",
        "does not establish sufficient photon yield",
    ):
        assert statement in text


def test_project_overview_links_are_descriptive_and_relative() -> None:
    text = OVERVIEW.read_text(encoding="utf-8")
    assert "click here" not in text.lower()
    local_targets = re.findall(r"\[[^]]+\]\((?!https?://)([^)#]+)(?:#[^)]+)?\)", text)
    assert local_targets
    for target in local_targets:
        assert not target.startswith(("/", "file:"))
        assert (OVERVIEW.parent / target).resolve().is_file()


def test_euvics_lock_uses_the_approved_task_2_commit() -> None:
    lock = yaml.safe_load((ROOT / "sources.lock.yml").read_text(encoding="utf-8"))
    assert (
        lock["sources"]["euvics"]["commit"]
        == "f142bd188892f9518a956989ebaf7a42b6930f33"
    )
