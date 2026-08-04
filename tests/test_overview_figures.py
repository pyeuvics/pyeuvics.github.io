from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tools.site_assembly.models import PublishedFile, SourceContract, SourceLock
from tools.site_assembly.overview_figures import (
    CSV_PATH,
    JSON_PATH,
    SVG_PATH,
    OverviewFigureError,
    stage_overview_figure,
)

ROOT = Path(__file__).resolve().parents[1]


def _contract(root: Path, paths: tuple[str, ...] = (SVG_PATH, CSV_PATH, JSON_PATH)) -> SourceContract:
    lock = SourceLock(
        "pyeuvics",
        "https://github.com/chongshikpark/pyEUVICS",
        "2" * 40,
        "publication/public-content-v1.json",
    )
    files = tuple(
        PublishedFile(
            "pyeuvics",
            path,
            "asset" if path.endswith(".svg") else "data",
            Path(path).stem,
            "0.5.0",
            "approved-public-model-calculation",
            None,
            "MIT",
            "See source citation and license metadata.",
            ("Calculated central locations only.",),
            "calculated-unvalidated",
        )
        for path in paths
    )
    return SourceContract(lock, root, files, True)


def _write_candidate(root: Path) -> None:
    for relative in (SVG_PATH, CSV_PATH, JSON_PATH):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
    energies = [1.5 + index * 0.05 for index in range(61)]
    with (root / CSV_PATH).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["electron_kinetic_energy_MeV", "scattered_wavelength_nm"])
        writer.writerows((energy, 20.0 - index * 0.1) for index, energy in enumerate(energies))
    (root / SVG_PATH).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">'
        '<title id="title">Trend</title><desc id="desc">Decreasing trend</desc></svg>',
        encoding="utf-8",
    )
    metadata = {
        "package": {"version": "0.5.0", "source_commit": "1" * 40},
        "model": {
            "electron_energy_convention": "kinetic",
            "laser_wavelength_nm": 800.0,
            "collision_angle_deg": 180.0,
            "observation_angle_mrad": 0.0,
            "linear_model": "exact",
            "recoil_included": True,
            "nonlinear_setting": "disabled",
            "harmonic": 1,
        },
        "limitations": ["one", "two", "three"],
    }
    (root / JSON_PATH).write_text(json.dumps(metadata), encoding="utf-8")


def test_stage_overview_figure_adds_accessible_provenance_block(tmp_path: Path) -> None:
    _write_candidate(tmp_path)
    staged = tmp_path / "staged"
    overview = staged / "project/overview.md"
    overview.parent.mkdir(parents=True)
    overview.write_text("# Overview\n\n## Design and validation status\n", encoding="utf-8")
    stage_overview_figure(_contract(tmp_path), staged)
    text = overview.read_text(encoding="utf-8")
    assert "## Calculated kinetic-energy trend" in text
    assert "Calculated — Unvalidated" in text
    assert "electron **kinetic** energy" not in text
    assert "electron <strong>kinetic</strong> energy" in text
    assert f"../imported/pyeuvics/{SVG_PATH}" in text
    assert f"../imported/pyeuvics/{CSV_PATH}" in text
    assert f"../imported/pyeuvics/{JSON_PATH}" in text
    assert "/blob/" + "1" * 40 + "/examples/generate_overview_energy_scan.py" in text
    assert text.index("Calculated kinetic-energy trend") < text.index("Design and validation status")


def test_stage_overview_figure_rejects_incomplete_approved_set(tmp_path: Path) -> None:
    _write_candidate(tmp_path)
    staged = tmp_path / "staged"
    (staged / "project").mkdir(parents=True)
    (staged / "project/overview.md").write_text(
        "# Overview\n\n## Design and validation status\n", encoding="utf-8"
    )
    with pytest.raises(OverviewFigureError, match="incomplete"):
        stage_overview_figure(_contract(tmp_path, (SVG_PATH, CSV_PATH)), staged)


def test_overview_figure_has_responsive_and_print_styles() -> None:
    stylesheet = (ROOT / "content/stylesheets/readthedocs.css").read_text(encoding="utf-8")
    assert ".pyeuvics-overview-figure img" in stylesheet
    assert ".pyeuvics-overview-figure figcaption" in stylesheet
    print_block = stylesheet.split("@media print", 1)[1]
    assert ".pyeuvics-overview-figure img" in print_block
