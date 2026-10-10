# Shared interpreter installed-file metadata repair

## Corrected diagnosis
The user identified the exact interpreter: the environment rooted in their
pyEUVICS checkout, running Python 3.13.16. Its 97 website dependency-version
checks pass. The earlier legacy website environment repair was verified for
that environment but did not identify this user's actual failure.

This interpreter resolves packaging 26.3 and Pillow 12.3.0 from global
site-packages. Both distributions lack RECORD and a file inventory, causing
notebook environment capture to reject execution before the notebook tests run.
The supplied traceback reports 20 failed and 653 passed tests for this reason.

## Approach
Install wheel distributions of those same two versions into the user's virtual
environment, without changing global packages, dependency versions, source
locks or strict metadata checks. Verify RECORD provenance and the reported
regression, then full website quality and browser checks using that interpreter.
No push or deployment is authorized.

## Progress
Completed the repair in the exact interpreter identified by the user.

## Implementation
The environment includes system site-packages. Installed packaging 26.3 and
Pillow 12.3.0 from wheels into its own site-packages with pip's explicit virtual
environment prefix, `--ignore-installed`, `--no-deps`, and `--only-binary=:all:`.
These local distributions take precedence over the unchanged global copies.
Both local distributions now have RECORD and an installed-file inventory.
No RECORD was invented, and no metadata or execution check was bypassed.

## Verification
- Before repair, the supplied interpreter reproduced the exact failing
  environment-fingerprint unit test: 1 failed with the missing-file-record error.
- After repair, all six notebook-environment unit tests passed.
- Verified imported Python 3.13.16, NumPy 2.5.1, SciPy 1.18.0, packaging 26.3,
  and Pillow 12.3.0. These versions were retained, not upgraded or downgraded.
- All 97 website dependency-version checks passed before and after repair.
- `PYTEST_ADDOPTS='-v tests' python -m tools.quality`, using that exact interpreter
  in the actual website checkout: 673 tests passed in 430.42 seconds; bounded
  lint, strict typing and the strict MkDocs build also passed.
- All 15 browser checks passed in 30.9 seconds using the same interpreter for
  fixture construction, Node 24, and the existing Chromium cache.
- Verified both repaired distributions resolve inside the virtual environment;
  the original global copies remain without RECORD and were not modified.
- pyEUVICS source checkout remained clean; installed files are ignored.
- `git diff --check` passed. No dependency pins, numerical libraries, source
  locks, test assertions, production code or publication checks changed.

## Outcome
The reported 20-failure pytest run is resolved in the user's actual shared
interpreter. The earlier website-environment repair was separate and did not
explain this failure. The development runbook now distinguishes matching
versions from complete installation metadata. Environment changes remain local;
this record and runbook changes are committed without a push or deployment.
