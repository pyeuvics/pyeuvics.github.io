# Numerical patch environment compatibility

## Scope
Reproduce pytest failures with the user’s Python 3.13.16 interpreter and NumPy
2.5.3 / SciPy 1.18.1. Align the website’s reviewed validation pins with the
requested patch upgrades, while retaining exact dependency and source-policy
checks. Do not change source locks, frozen campaign evidence, approvals, or
scientific tolerances. No push or deployment.

## Verification
Run the pin regression before updating declarations, focused environment tests,
full website quality and browser tests. Check the locked manifest’s publication
boundary before updating pins.

## Progress
Confirmed old website pins (2.5.1 / 1.18.0) conflict with the installed versions.
The locked pyEUVICS manifest keeps its notebook candidate set approval-pending;
source environment checks will continue to reject incompatible frozen policies.

## Implementation and focused evidence
- Reproduced the environment fingerprint failure against the old NumPy pin.
- Updated the numerical pin assertion first: 1 failed, 14 passed before repair.
- Aligned NumPy 2.5.3 and SciPy 1.18.1 in direct requirements and constraints.
- Then detected a second conflict: installed types-PyYAML 6.0.12.20260906,
  required by current pyEUVICS development metadata, versus the website’s old
  6.0.12.20260518 pin. Aligned this development-only pin in both declarations.
- Added a regression ensuring upgraded website versions still reject a frozen
  source policy requiring older versions. No validator behavior was loosened.
- All 22 focused dependency/environment tests pass; all 97 installed constrained
  package versions pass policy checks and upgraded packages retain RECORD data.
- All 15 browser checks passed in 35.9 seconds under Node 24 with the exact
  shared Python interpreter supplying fixture builds.
- Full baseline website run was stopped after targeted reproduction, before
  dependency inputs changed. Full post-change quality is running separately.

## Final verification and outcome
- Exact user interpreter: Python 3.13.16, NumPy 2.5.3, SciPy 1.18.1,
  types-PyYAML 6.0.12.20260906.
- `PYTEST_ADDOPTS='-v tests' python -m tools.quality` with an owned edited-tree
  output: 674 tests passed in 470.55 seconds, with no skips. Dependency policy
  passed for 97 installed constrained packages, bounded Ruff passed, strict mypy
  passed for 67 files, and the strict MkDocs build passed.
- `npm run test:browser` using Node 24: 15 passed in 35.9 seconds.
- `git diff --check`: passed. Current development and dependency-policy guidance
  now describes the upgraded pins and the retained source-environment boundary.
- Inspected both locked source campaign environment policies: they require
  NumPy 2.5.2 and SciPy 1.18.0. Their notebook candidates remain approval-pending
  and excluded; source locks, publication approvals and source bytes are unchanged.
- These checks establish local test compatibility, not a trusted source-backed
  publication receipt, source approval, or deployment. No source-backed build
  or remote CI result is claimed by this repair.

The shared-interpreter pytest failures are resolved. Exact pins, installed-file
provenance, source-policy rejection and numerical tolerances remain enforced.
Committed locally with the requested message format; no push or deployment.
