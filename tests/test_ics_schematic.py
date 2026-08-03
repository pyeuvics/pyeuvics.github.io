from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "content/assets/images/ics-geometry-source-chain.svg"
OVERVIEW = ROOT / "content/project/overview.md"
STYLESHEET = ROOT / "content/stylesheets/readthedocs.css"
SVG_NS = "{http://www.w3.org/2000/svg}"


def test_schematic_is_accessible_readable_svg() -> None:
    root = ET.parse(SVG).getroot()
    assert root.tag == f"{SVG_NS}svg"
    assert root.attrib["viewBox"] == "0 0 1200 900"
    assert root.attrib["role"] == "img"
    labelled_by = root.attrib["aria-labelledby"].split()
    ids = {element.attrib["id"] for element in root.iter() if "id" in element.attrib}
    assert set(labelled_by) <= ids
    title = root.find(f"{SVG_NS}title")
    description = root.find(f"{SVG_NS}desc")
    assert title is not None and title.text and "Inverse Compton" in title.text
    assert description is not None and description.text
    assert "not to scale" in description.text.lower()
    assert "alpha equals 180 degrees" in description.text.lower()


def test_schematic_contains_required_geometry_and_noncolor_labels() -> None:
    text = " ".join(fragment.strip() for fragment in SVG.read_text().splitlines())
    for label in (
        "electron bunch",
        "incident laser pulse",
        "interaction point",
        "forward EUV emission",
        "collection acceptance",
        "electron dump",
        "head-on limit: α = 180°",
        "observation angle θ is measured from",
        "SCHEMATIC — NOT TO SCALE",
        "Original EUVICS website schematic",
    ):
        assert label in text
    assert "dashed propagation line" in text
    assert "dash-dot boundaries" in text
    assert "physical angular distribution (stylized)" in text


def test_schematic_has_no_active_or_external_content() -> None:
    text = SVG.read_text(encoding="utf-8")
    assert "<script" not in text.lower()
    assert "<!doctype" not in text.lower()
    assert "<!entity" not in text.lower()
    assert "data:" not in text.lower()
    assert "http://" not in text.replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in text
    assert not re.search(r"(?:href|src)\s*=", text, flags=re.IGNORECASE)
    assert not re.search(r"(?:inkscape|sodipodi|adobe|generator)", text, flags=re.IGNORECASE)


def test_overview_integrates_schematic_with_alt_text_and_caption() -> None:
    text = OVERVIEW.read_text(encoding="utf-8")
    assert "../assets/images/ics-geometry-source-chain.svg" in text
    assert "Schematic of an electron bunch traveling left to right" in text
    assert 'aria-describedby="ics-schematic-caption"' in text
    assert '<figcaption id="ics-schematic-caption">' in text
    assert "do not assert that the two angular extents are equal" in text
    assert text.index("ics-geometry-source-chain.svg") < text.index(
        "This physical picture is broader"
    )
    resolved = (OVERVIEW.parent / "../assets/images/ics-geometry-source-chain.svg").resolve()
    assert resolved == SVG.resolve(), "overview must use the website-owned schematic"
    assert ROOT / "content/assets" in resolved.parents
    assert not {"archive", "imported", "downloads"}.intersection(resolved.parts), (
        "overview schematic must not come from an archive, imported source, or download copy"
    )


def test_schematic_has_bounded_mobile_and_print_presentation() -> None:
    overview = OVERVIEW.read_text(encoding="utf-8")
    stylesheet = STYLESHEET.read_text(encoding="utf-8")
    assert '<figure class="ics-schematic" markdown="1">' in overview
    assert ".ics-schematic > p" in stylesheet
    assert "overflow-x: auto" in stylesheet
    assert ".ics-schematic img" in stylesheet
    assert "width: 52rem" in stylesheet
    assert "@media print" in stylesheet
