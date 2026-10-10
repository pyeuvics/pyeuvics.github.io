from __future__ import annotations

from pathlib import Path

import pytest

from tools.site_assembly.overview_figures import (
    CSV_PATH,
    JSON_PATH,
    SVG_PATH,
    OverviewFigureError,
    stage_overview_figure,
)

from tests.support.overview import overview_contract as _contract, write_overview_candidate as _write_candidate

from tests.support.paths import ROOT


def test_stage_overview_figure_adds_accessible_provenance_block(tmp_path: Path) -> None:
    _write_candidate(tmp_path)
    staged = tmp_path / "staged"
    overview = staged / "project/overview.md"
    overview.parent.mkdir(parents=True)
    overview.write_text("# Overview\n\n<!-- publication:figure:start -->\n<!-- publication:figure:end -->\n\n## Design and validation status\n", encoding="utf-8")
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
        "# Overview\n\n<!-- publication:figure:start -->\n<!-- publication:figure:end -->\n\n## Design and validation status\n", encoding="utf-8"
    )
    with pytest.raises(OverviewFigureError, match="incomplete"):
        stage_overview_figure(_contract(tmp_path, (SVG_PATH, CSV_PATH)), staged)


def test_overview_figure_has_responsive_and_print_styles() -> None:
    stylesheet = (ROOT / "content/stylesheets/readthedocs.css").read_text(encoding="utf-8")
    assert ".pyeuvics-overview-figure img" in stylesheet
    assert ".pyeuvics-overview-figure figcaption" in stylesheet
    print_block = stylesheet.split("@media print", 1)[1]
    assert ".pyeuvics-overview-figure img" in print_block
