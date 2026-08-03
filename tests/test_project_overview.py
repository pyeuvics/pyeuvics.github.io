from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "content/project/overview.md"
CONFIG = ROOT / "mkdocs.yml"


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"project overview is missing required section: {heading}"
    body = match.group("body").strip()
    assert len(body.split()) >= 20, f"project overview section is not meaningful: {heading}"
    return body


def test_project_overview_replaces_placeholder_with_required_science() -> None:
    assert OVERVIEW.is_file(), "content/project/overview.md must exist"
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
        _section(text, heading)
    forbidden = {
        "former placeholder": r"Awaiting approved material",
        "dummy equation": r"(?<![A-Za-z])x\s*=\s*x(?![A-Za-z])",
        "author marker": r"\b(?:TODO|TBD|FIXME)\b",
        "template token": r"(?:\{\{[^{}]+\}\}|\$\{[^{}]+\}|<[A-Z][A-Z0-9_-]*>)",
        "local filesystem path": r"(?:/Users/|/home/[^/\s]+/|[A-Za-z]:\\)",
    }
    for label, pattern in forbidden.items():
        flags = 0 if label == "template token" else re.IGNORECASE
        assert re.search(pattern, text, flags=flags) is None, (
            f"project overview contains forbidden {label}"
        )
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


def test_project_overview_scientific_conventions_are_qualified() -> None:
    text = OVERVIEW.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\b\d+(?:\.\d+)?\s*(?:keV|MeV|GeV)\b", line, re.IGNORECASE):
            assert re.search(r"\b(?:kinetic|total)\b", line, re.IGNORECASE), (
                f"numerical electron energy on overview line {line_number} must say "
                "whether it is kinetic or total"
            )

    normalized = re.sub(r"[\\(){}]", "", text.lower())
    assert re.search(r"0\^?circ.{0,80}co-propagating", normalized, re.DOTALL), (
        "collision-angle convention must define 0 degrees as co-propagating"
    )
    assert re.search(r"180\^?circ.{0,80}head-on", normalized, re.DOTALL), (
        "collision-angle convention must define 180 degrees as head-on"
    )
    assert re.search(
        r"observation angle.{0,160}(?:the\s+)?electron\s+(?:propagation|forward)\s+direction",
        normalized,
        flags=re.DOTALL,
    ), "observation angle must be defined from the electron direction"

    scaling = text.index("E_s\\simeq4\\gamma^2E_L")
    qualification = text[max(0, scaling - 300) : scaling].lower()
    for assumption in ("weak-field", "recoil-free", "head-on", "on-axis", "limit"):
        assert assumption in qualification, (
            f"4-gamma-squared scaling must retain its {assumption} qualification"
        )

    if "nonlinear" in text.lower():
        limitation_paragraphs = [
            paragraph.lower()
            for paragraph in text.split("\n\n")
            if "harmonic" in paragraph.lower() and "relative" in paragraph.lower()
        ]
        assert any("not" in paragraph for paragraph in limitation_paragraphs), (
            "nonlinear ICS discussion must not imply calculated relative harmonic yields"
        )


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


def test_overview_navigation_mathjax_and_project_base_path() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    site_url = urlparse(config["site_url"])
    assert site_url.path == "/euvics.github.io/", (
        "site_url must retain the GitHub project-site base path"
    )
    nav_text = yaml.safe_dump(config["nav"], sort_keys=False)
    assert nav_text.count("project/overview.md") == 1, (
        "project overview must appear exactly once in navigation"
    )
    assert any(
        isinstance(extension, dict) and "pymdownx.arithmatex" in extension
        for extension in config["markdown_extensions"]
    ), "MathJax-compatible arithmatex processing must remain enabled"
    assert "javascripts/mathjax.js" in config["extra_javascript"], (
        "the local MathJax configuration must remain loaded"
    )
