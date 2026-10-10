"""Present the structurally validated, source-owned overview artifact set."""
from __future__ import annotations

from pathlib import Path

from .models import SourceContract
from .overview_data import CSV_PATH as CSV_PATH
from .overview_data import EXPECTED_PATHS, validate_overview
from .overview_data import JSON_PATH as JSON_PATH
from .overview_data import SVG_PATH as SVG_PATH
from .overview_data import OverviewFigureError as OverviewFigureError
from .presentation import markdown_text
from .template_slots import TemplateSlotError, fill_slot


def stage_overview_figure(contract: SourceContract, staged_content: Path) -> None:
    """Append the approved figure and provenance to the project overview."""
    approved_paths = {item.path for item in contract.files}
    if not EXPECTED_PATHS.intersection(approved_paths):
        return
    artifacts = validate_overview(contract)
    point_count = artifacts.descriptor.grid.point_count
    generator_commit = artifacts.descriptor.generator_commit
    overview = staged_content / "project/overview.md"
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
    from pyEUVICS {markdown_text(artifacts.descriptor.package_version)}; the published artifacts are locked by
    this site to pyEUVICS commit `{contract.lock.commit}`.

'''
    try:
        fill_slot(overview,"figure",insertion)
    except TemplateSlotError as exc:
        raise OverviewFigureError(str(exc)) from exc
