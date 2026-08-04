"""Validate and integrate approved pyEUVICS overview figures."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from itertools import pairwise
from pathlib import Path

from .models import SourceContract

FIGURE_ROOT = "docs/generated/overview-figures"
SVG_PATH = f"{FIGURE_ROOT}/kinetic-energy-scan.svg"
CSV_PATH = f"{FIGURE_ROOT}/kinetic-energy-scan.csv"
JSON_PATH = f"{FIGURE_ROOT}/kinetic-energy-scan.json"
EXPECTED_PATHS = {SVG_PATH, CSV_PATH, JSON_PATH}
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SVG_NS = "{http://www.w3.org/2000/svg}"


class OverviewFigureError(ValueError):
    """An approved overview figure set is incomplete or inconsistent."""


def _validate_set(contract: SourceContract) -> tuple[dict[str, object], int]:
    approved = {item.path: item for item in contract.files if item.path in EXPECTED_PATHS}
    if not approved:
        raise OverviewFigureError("approved pyEUVICS overview figure set is absent")
    if set(approved) != EXPECTED_PATHS:
        raise OverviewFigureError("approved pyEUVICS overview figure set is incomplete")
    if {item.validation_status for item in approved.values()} != {"calculated-unvalidated"}:
        raise OverviewFigureError("overview figure validation status is inconsistent")

    metadata = json.loads((contract.root / JSON_PATH).read_text(encoding="utf-8"))
    package = metadata.get("package")
    model = metadata.get("model")
    if not isinstance(package, dict) or not isinstance(model, dict):
        raise OverviewFigureError("overview figure metadata lacks package or model settings")
    generator_commit = package.get("source_commit")
    if not isinstance(generator_commit, str) or not COMMIT.fullmatch(generator_commit):
        raise OverviewFigureError("overview figure generator commit is invalid")
    expected_model = {
        "electron_energy_convention": "kinetic",
        "laser_wavelength_nm": 800.0,
        "collision_angle_deg": 180.0,
        "observation_angle_mrad": 0.0,
        "linear_model": "exact",
        "recoil_included": True,
        "nonlinear_setting": "disabled",
        "harmonic": 1,
    }
    if any(model.get(key) != value for key, value in expected_model.items()):
        raise OverviewFigureError("overview figure model settings differ from the approved case")
    limitations = metadata.get("limitations")
    if not isinstance(limitations, list) or len(limitations) < 3:
        raise OverviewFigureError("overview figure limitations are incomplete")

    with (contract.root / CSV_PATH).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 61:
        raise OverviewFigureError("overview figure data must contain 61 scan points")
    try:
        energies = [float(row["electron_kinetic_energy_MeV"]) for row in rows]
        wavelengths = [float(row["scattered_wavelength_nm"]) for row in rows]
    except (KeyError, ValueError) as exc:
        raise OverviewFigureError("overview figure CSV is malformed") from exc
    if energies[0] != 1.5 or energies[-1] != 4.5 or any(
        later <= earlier for earlier, later in pairwise(energies)
    ):
        raise OverviewFigureError("overview figure kinetic-energy scan is invalid")
    if any(later >= earlier for earlier, later in pairwise(wavelengths)):
        raise OverviewFigureError("overview figure wavelength trend is not monotonically decreasing")

    svg_root = ET.parse(contract.root / SVG_PATH).getroot()
    if svg_root.tag != f"{SVG_NS}svg" or svg_root.attrib.get("role") != "img":
        raise OverviewFigureError("overview figure SVG lacks accessible image semantics")
    labelled = set(svg_root.attrib.get("aria-labelledby", "").split())
    identifiers = {item.attrib["id"] for item in svg_root.iter() if "id" in item.attrib}
    if not labelled or not labelled.issubset(identifiers):
        raise OverviewFigureError("overview figure SVG accessible labels are unresolved")
    return metadata, len(rows)


def stage_overview_figure(contract: SourceContract, staged_content: Path) -> None:
    """Append the approved figure and provenance to the project overview."""
    approved_paths = {item.path for item in contract.files}
    if not EXPECTED_PATHS.intersection(approved_paths):
        return
    metadata, point_count = _validate_set(contract)
    package = metadata["package"]
    assert isinstance(package, dict)
    generator_commit = str(package["source_commit"])
    overview = staged_content / "project/overview.md"
    text = overview.read_text(encoding="utf-8")
    insertion = f'''## Calculated kinetic-energy trend

<figure class="pyeuvics-overview-figure" markdown="1">

![Calculated scattered wavelength decreases monotonically as electron kinetic energy rises from 1.5 to 4.5 MeV for the approved exact-linear reference geometry.](../imported/pyeuvics/{SVG_PATH}){{ aria-describedby="pyeuvics-energy-scan-caption" loading="lazy" }}

<figcaption id="pyeuvics-energy-scan-caption">
  <strong>Calculated — Unvalidated.</strong> pyEUVICS exact linear Compton model
  calculation for an 800 nm laser, 180° head-on collision, 0 mrad forward
  observation, recoil included, harmonic 1, and no nonlinear correction. The
  {point_count}-point scan uses electron <strong>kinetic</strong> energy. It predicts
  central wavelength locations only—not photon yield, bandwidth, brilliance,
  detected signal, a measurement, experimental validation, or CAIN validation.
</figcaption>

</figure>

??? info "Reproduce and inspect the calculation"
    Download the [machine-readable scan data](../imported/pyeuvics/{CSV_PATH})
    and [complete settings and limitations](../imported/pyeuvics/{JSON_PATH}).
    The generator is
    [`examples/generate_overview_energy_scan.py`]({contract.lock.repository}/blob/{generator_commit}/examples/generate_overview_energy_scan.py)
    from pyEUVICS {package['version']}; the published artifacts are locked by
    this site to pyEUVICS commit `{contract.lock.commit}`.

'''
    marker = "## Design and validation status"
    if marker not in text:
        raise OverviewFigureError("project overview lacks the figure insertion point")
    overview.write_text(text.replace(marker, insertion + marker, 1), encoding="utf-8")
