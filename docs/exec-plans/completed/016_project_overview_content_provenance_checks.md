# Project overview content and provenance checks — completed

## Scope

Add focused, offline automated checks that prevent regression of the approved
project overview, scientific conventions, source provenance, publication
boundary, schematic accessibility, and project-site link behavior.

## Boundaries

- Extend existing tests and assembly fixtures; do not introduce a second
  content or provenance source of truth.
- Avoid brittle full-paragraph matching and live network dependencies.
- Preserve strict manifest and assembly failures.
- Do not push or deploy.

## Plan

- [x] Strengthen authored-overview content and scientific guardrail tests.
- [x] Strengthen fixture-based allowlist, exclusion, mismatch, and exact-link
      provenance checks.
- [x] Add project-site base-path, MathJax, unique-navigation, and rendered image
      accessibility assertions.
- [x] Run focused tests, then all tests, typing, lint, strict build, and a real
      locked-source assembly.
- [x] Review the generated artifact for duplicate/unapproved paths and local
      filesystem leakage.
- [x] Record evidence and move this plan to `completed/`.

## Verification evidence

- Fifteen focused overview, schematic, lock, provenance, positive-allowlist,
  negative-missing-path, and exclusion tests passed.
- The authored-page checks require meaningful sections, reject placeholders,
  dummy equations, author markers, template tokens, and local paths, and enforce
  the energy, angle, limiting-scaling, and nonlinear-harmonic guardrails without
  matching whole paragraphs.
- Fixture assembly proves each source inventory exactly equals its allowlist,
  an unlisted pyEUVICS note remains absent, missing allowlisted content fails
  with the exact path, and commit mismatch errors name the source plus expected
  and actual commits.
- Generated provenance was verified to use exact commit-tree links and exact
  allowlisted paths; mutable `main`/`master` provenance links are rejected.
- The configured `/euvics.github.io/` base path, unique overview navigation,
  arithmatex/MathJax configuration, canonical URL, relative schematic URL, alt
  text, and caption association are covered.
- All 70 repository tests passed in 45.28 seconds. Strict mypy, targeted Ruff,
  `mkdocs build --strict`, and `git diff --check` passed.
- Production-equivalent assembly passed with 56 approved inputs: 3 EUVICS and
  53 pyEUVICS entries, with 56 unique staged paths. The unlisted note and
  duplicate overview page were absent, and the generated overview scan found
  no placeholders, author markers, dummy equation, or local filesystem path.
- The checks are intentionally offline and structural. Human review remains
  necessary for the scientific meaning and publication approval of future
  source changes; source-update pull requests retain that review gate.
