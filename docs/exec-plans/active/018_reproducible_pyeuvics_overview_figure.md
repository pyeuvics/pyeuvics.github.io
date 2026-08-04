# Reproducible pyEUVICS overview figure

## Scope

Create one compact kinetic-energy scan in the authoritative pyEUVICS repository,
export deterministic SVG, CSV, and JSON artifacts, and prepare—but do not publish—
the website integration until the project owner explicitly approves the scientific
content and publication contract entry.

## Decisions

- Scan electron **kinetic** energy for an 800 nm laser in head-on (180 degree),
  forward-observation (0 mrad) geometry.
- Use the public exact linear Compton API with recoil included, harmonic 1, and
  no nonlinear correction. The figure is a model calculation, not a measurement
  or validation result.
- Keep the generator, configuration, data, regression checks, and publication
  candidate in pyEUVICS. The website will only consume an approved artifact from
  a subsequently locked immutable commit.
- Do not use the provisional 6.7 nm or 13.5 nm reference campaigns.

## Progress

- [x] Read both repositories' instructions and inspect both working trees.
- [x] Select an approved teaching configuration and define scientific labels.
- [x] Add and verify the pyEUVICS generator and focused regression test.
- [x] Generate deterministic SVG, CSV, and JSON from an immutable pyEUVICS commit.
- [x] Add an approval-pending pyEUVICS publication candidate.
- [ ] Obtain explicit scientific and publication approval.
- [ ] Update the website source lock, assemble the approved artifact, add accessible
      overview content, and run full verification.
- [ ] Inspect desktop/mobile and light/dark rendering before publication.

## Verification evidence

- Authoritative generator commit: `e54abc5d520932c6a71f6b6231ae2c49336c0e5c`.
- Candidate artifact/manifest commit: `382507b70f8441869922d30ab6a073b44944527f`.
- Two independent generations were byte-for-byte identical.
- The pyEUVICS focused suite passed (15 tests), full suite passed (339 tests),
  and Ruff and strict mypy passed for affected files.
- Rendered SVG inspection found legible axes, units, title, tick labels, and an
  unclipped monotonic curve.
- The website overview and assembled artifact remain unchanged.

## Publication gate

The generated candidate must remain absent from assembled website content until
the pyEUVICS publication manifest records explicit owner approval and the website
locks the corresponding immutable source commit.
