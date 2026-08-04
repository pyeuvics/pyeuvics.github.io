# pyEUVICS overview figure candidate

Date: 2026-08-04 (Asia/Seoul)

Decision state: **Scientific and publication approval pending**

## Candidate

The proposed overview addition is a calculated scattered-wavelength scan over
electron **kinetic** energy from 1.5 MeV to 4.5 MeV. It uses an 800 nm laser,
180 degree head-on collision, 0 mrad forward observation, exact linear Compton
kinematics with recoil, harmonic 1, and no nonlinear or polarization-dependent
correction.

It is labeled **Calculated — Unvalidated**. It is not a measurement, experimental
validation, CAIN validation, yield prediction, bandwidth prediction, brilliance
prediction, or detected-signal prediction. It does not use either provisional
reference campaign.

## Provenance

- Generator: `examples/generate_overview_energy_scan.py`
- Generator source commit: `e54abc5d520932c6a71f6b6231ae2c49336c0e5c`
- Candidate artifact/manifest commit: `382507b70f8441869922d30ab6a073b44944527f`
- pyEUVICS version: `0.5.0`
- SVG: `docs/generated/overview-figures/kinetic-energy-scan.svg`
- CSV: `docs/generated/overview-figures/kinetic-energy-scan.csv`
- Settings and limitations: `docs/generated/overview-figures/kinetic-energy-scan.json`

## Numerical checks

| Electron kinetic energy | Calculated scattered wavelength |
| --- | --- |
| 1.5 MeV | 13.3487208347 nm |
| 3.0 MeV | 4.28234181102 nm |
| 4.5 MeV | 2.09093189426 nm |

All 61 serialized points were compared with `pyEUVICS.linear_ics`; the wavelength
decreases monotonically across the scan.

## Reproducibility and artifact checks

- Two independent generations were byte-for-byte identical.
- CSV SHA-256: `8ea3497d4e9bbe5006c4e4adf003829ed0a1e32dad954931d184363a3f161126`
- JSON SHA-256: `bcc7696b7f3179e03a95acdbf95c54e5ecfc52508d5a758311a4561219c39f9a`
- SVG SHA-256: `9d70e584c4d2f0caa48084a7e48483d747244a94b11a9df6a17e787270bc2a15`
- Focused generator and publication-contract tests: 15 passed.
- Full pyEUVICS suite: 339 passed.
- Ruff and strict mypy: passed for affected files.
- Rendered SVG inspection: axes, units, title, tick labels, and curve were legible
  and unclipped.

## Publication gate

The pyEUVICS manifest records `overview-linear-kinematics-figure` as
`approval-pending`; the three files are not public allowlist entries. The website
source lock remains unchanged and the figure is absent from assembled content.
Integration, responsive/theme review, push, and deployment require explicit
scientific and publication approval of this exact candidate.
