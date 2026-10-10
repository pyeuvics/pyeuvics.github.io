# Local Python environment repair

## Scope and evidence
The user reports failures from `python -m pytest -v tests` after the hosted
validation-record fix. Local `.venv-docs` uses Python 3.14 and fails the pinned
execution environment check (ast-serialize differs). Both local virtual
environments retain launchers and activation scripts naming the removed
`euvics.github.io` checkout. A separate verification environment had concealed
this local setup failure.

## Approach
Preserve the old local environments in ignored backups. Recreate the canonical
local environment with Python 3.13 and the existing validation requirements;
keep both established environment names usable through one canonical environment.
Document environment recreation after a checkout move and interpreter checks.
Verify the user's exact pytest command, dependency policy, typing/build checks,
and browser behavior. Do not change dependency pins, source locks or checks.

## Progress
Completed the local environment repair and verification.

## Changes
- Preserved both old environments under the ignored
  `.staging/environment-backups/local-repair-20261010/` directory.
- Created `.venv-docs` with Python 3.13.16 and installed the unchanged
  `requirements-validation.txt` dependency set.
- Made `.venv-docs-313` an alias of that fresh environment, preserving both
  established local activation names without maintaining divergent packages.
  Explicitly ignored this local symlink because directory-only ignore patterns
  do not match symlinks.
- Verified that activation and pytest launchers no longer reference the former
  checkout name. The direct pytest console launcher also works.
- Documented recreation after checkout moves and interpreter/pin diagnostics.
  Existing user terminals must reactivate to refresh their shell settings.

## Verification
- Legacy environment reproduction: 1 failed, 5 passed; notebook environment
  capture rejected the installed ast-serialize version against reviewed pins.
- A preliminary Python 3.13 diagnostic run was deliberately interrupted before
  replacing that environment. Its interrupted notebook result is not treated
  as a product regression or a completed suite.
- Activated the repaired environment through `.venv-docs-313/bin/activate`;
  confirmed Python 3.13.16 at the current checkout and working pytest launchers.
- `python -m pip check`: no broken requirements.
- `PYTEST_ADDOPTS='-v tests' python -m tools.quality` passed in the actual local
  checkout. This runs the user's verbose, complete tests selection through the
  shared quality command: all 673 tests passed in 409.96 seconds.
- Dependency policy passed for all 97 installed constrained packages; bounded
  lint, strict typing for 67 source files, and the strict MkDocs build passed.
- Browser checks used the repaired Python environment with Node 24 and the
  existing Chromium cache: all 15 passed in 29.5 seconds.
- The two historical cached metadata failures use obsolete payload-based IDs;
  their current explicit unicode-long cases passed in this full suite. No
  cached failures were deleted to obtain the result.
- `git diff --check` passed. No dependencies, source locks, scientific content,
  production tools, test expectations or publication checks were changed.

## Outcome
The local environment is repaired, and full validation now passes in the
user's checkout rather than only in a separate verification environment.
Environment files and backups remain ignored; the commit records only the
runbook, the local alias ignore rule, and this repair evidence. No push or deployment was performed.

## Follow-up clarification — 2026-10-10

The owner subsequently identified a different interpreter in the pyEUVICS
checkout. Its Python and numerical versions already match the website pins;
the repair above did not diagnose that interpreter's failure. See
[the exact-interpreter metadata repair](070_shared-interpreter-record-metadata.md)
for the reproduced missing-RECORD cause and the verified fix.
