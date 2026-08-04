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
- [x] Obtain explicit scientific and publication approval.
- [x] Update the website source lock, assemble the approved artifact, add accessible
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
- The project owner explicitly approved the exact candidate for publication on
  2026-08-04.
- pyEUVICS commit `38853bc773bf8594b31fe4c211f444cda5b91320`
  records the approval and was pushed to `main`.
- The locked website assembly succeeded with 59 approved files; the staged SVG,
  CSV, and JSON are byte-for-byte identical to the approved source files.
- The full pyEUVICS suite passed (340 tests), the full website suite passed
  (72 tests), strict MkDocs passed, and affected Ruff/strict-mypy checks passed.
- Browser discovery found no connected browser. Interactive desktop/mobile and
  light/dark inspection remains unresolved and is not represented as passing.

## Publication gate

The publication gate is satisfied for the exact approved artifacts and source
lock. Any regenerated artifact or scientific-setting change requires renewed
approval.
