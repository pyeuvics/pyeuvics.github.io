"""Synthetic overview data; no scientific model is evaluated here."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.site_assembly.models import PublishedFile, SourceContract, SourceLock
from tools.site_assembly.overview_figures import CSV_PATH, JSON_PATH, SVG_PATH


def overview_contract(root: Path, paths: tuple[str, ...] = (SVG_PATH, CSV_PATH, JSON_PATH)) -> SourceContract:
    lock = SourceLock(
        "pyeuvics",
        "https://github.com/pyeuvics/pyEUVICS",
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
    return SourceContract(lock, root, files)


def write_overview_candidate(root: Path) -> None:
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
        "artifact_status": "calculated-unvalidated",
        "calculation_entry_point": "examples/generate_overview_energy_scan.py",
        "files": [Path(CSV_PATH).name, Path(SVG_PATH).name],
        "package": {"name": "pyEUVICS", "version": "0.5.0", "source_commit": "1" * 40},
        "model": {
            "api": "pyEUVICS.linear_ics",
            "collision_angle_convention": "between electron and laser propagation vectors; 180 degrees is head-on",
            "observation_angle_convention": "relative to electron propagation; 0 mrad is forward",
            "electron_kinetic_energy_MeV": {"minimum": 1.5, "maximum": 4.5, "point_count": 61, "spacing": "linear"},
            "laser_strength_a0": None,
            "polarization": "not-applicable-to-linear-kinematics",
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
