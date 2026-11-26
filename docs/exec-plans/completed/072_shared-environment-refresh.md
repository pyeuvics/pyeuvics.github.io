# Shared validation environment refresh

## Scope and acceptance
Resolve website pytest failures using the owner's shared Python 3.13.16 environment.
Reconcile existing direct/constraint pins with installed versions, retaining exact
pin enforcement, installed RECORD checks, source locks, and source-owned policies.
Do not change source approvals, scientific inputs, public content, or deployment.

## Plan
1. Record dependency drift and reproduce the environment fingerprint failure.
2. Update pin regression first, then reconcile existing declarations and guidance.
3. Run focused tests, complete quality, browser tests, and fresh-install validation.

## Evidence
The environment fingerprint test fails on the old appnope constraint (1 failed,
6 passed); many more declared dependencies differ after the shared environment
upgrade, including NumPy 2.5.5, PyYAML 6.0.4, and Markdown 3.11.4. The baseline
full run was interrupted after reproducing failures to avoid testing mixed inputs.
No validator bypass or source-policy exception is authorized by this repair.

## Repairs and focused evidence
- Pin regression before refresh: 1 failed, 14 passed. The existing catalog had
  58 version mismatches with the shared interpreter; updated those exact pins
  and Ruff's required version, without adding dependency groups or bypasses.
- PDF reproduction exposed pypdf 7.1.1 rejecting legacy parser-limit constants.
  Adopted its public configuration API with the same six 8 MiB limits. Reference:
  [pypdf configuration](https://pypdf.readthedocs.io/en/7.1.1/_modules/pypdf/_configuration.html).
- Updated the unsafe-PDF fixture to construct its JavaScript action explicitly,
  replacing a removed writer convenience method; active content remains rejected.
- Fresh Python 3.13 installation succeeded, pip check passed, and policy accepted
  96 installed constrained distributions (97 in the owner's shared environment).
  All 66 focused dependency, environment, PDF-asset and document tests passed.
- First browser run: 14 passed, 1 failed because the offscreen lazy schematic had
  not been requested before an immediate naturalWidth assertion. The test now
  scrolls it into view and waits within the existing bounded assertion timeout
  for complete loading and positive width. Broken images still fail.

## Final verification and outcome
- Full `python -m tools.quality` using the owner's shared Python 3.13.16:
  dependency policy passed for 97 installed constrained packages, bounded Ruff
  passed, all 674 pytest tests passed with no skips in 879.39 seconds, strict
  mypy passed for 67 files, and the strict MkDocs build passed. Exit status 0.
- `npm run test:browser` with Node 24.22.3, the pinned Playwright Chromium, and
  the same Python environment: all 15 checks passed in 1.1 minutes, exit status 0.
- Fresh-environment installation, pip check, dependency policy, and 66 focused
  PDF/document/dependency/notebook-environment tests passed (63.85 seconds).
  The optional legacy six constraint is inactive there; source policy remains exact.
- `git diff --check` passed. Source locks, publication approvals, source content,
  notebook input bytes, scientific tolerances, and deployment workflows are unchanged.
- This is local edited-tree validation on macOS, not a trusted source-backed
  publication receipt or a hosted CI/deployment result. Local commit authorized after verification; no push or deployment.

The reported local pytest failures are resolved in the requested shared environment.
