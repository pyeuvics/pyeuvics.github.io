# Automated source-update pull requests — active

## Scope

Implement Task 11 as a proposal-only workflow that detects newer default-branch
source commits, validates exact candidate locks and publication manifests,
compares complete baseline/candidate artifacts, and opens a reviewable pull
request changing only `sources.lock.yml`.

## Security boundaries

- Candidate source code runs only in a read-only validation job with no write
  credential and non-persisted checkout credentials.
- A separate credentialed job receives only the validated candidate lock and
  comparison report; it never checks out or executes candidate source code.
- Automation never merges, deploys, follows a branch tip in production, changes
  manifests, bypasses review, or writes generated site output.
- Existing production builds remain locked to exact 40-character commits.

## Planned work

- [x] Add typed discovery, lock-update, ancestry, verification, and artifact-
      comparison tooling.
- [x] Add scheduled/manual two-job automation with least-privilege permissions.
- [x] Prevent duplicate automated proposals and constrain the PR diff.
- [x] Document credential scope, provenance, comparison, rollback, failure
      modes, reviewer workflow, and deferred-material behavior.
- [x] Add unit and workflow safety tests.
- [x] Run all tests, strict typing, strict MkDocs, and workflow YAML checks.
- [x] Record evidence and complete the plan without dispatching the workflow.

## Verification evidence

- Added `tools/source_update.py` with strict public HEAD discovery, commit-only
  lock generation, nonempty diff verification, descendant-history enforcement,
  review-manifest validation, bounded artifact comparison, and fail-closed CLI.
- Added `.github/workflows/source-update.yml` for weekly/manual discovery. Its
  candidate-validation job has only content/PR read access and five
  non-persisted checkouts. The separate PR job receives only the validated
  proposal artifact and has narrowly scoped content/PR write access.
- Candidate validation runs complete baseline and candidate `validate_ci`
  builds. The PR job executes only trusted website code, commits only
  `sources.lock.yml`, and opens but never merges or deploys a pull request.
- Duplicate open automation proposals stop new work; workflow concurrency does
  not cancel an in-flight source review.
- Added `docs/source-update-automation.md` covering credentials, provenance,
  ancestry, comparison, failures, human review, protected merge/deploy, and
  rollback.
- Official artifact action versions were checked on 2026-08-03:
  `actions/upload-artifact@v7` and `actions/download-artifact@v8`.
- A real public discovery dry run resolved EUVICS
  `dcae0fba5b6cbb9073e0e552ca74c0a14484e2b0` and pyEUVICS
  `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`, exactly matching the current
  locks, and returned `has_updates=false` without creating anything.
- All 58 tests passed: 27 non-assembly tests, 15 general assembly tests, eight
  document tests, one campaign test, and seven localhost-kernel notebook tests.
- Strict mypy passed for all 10 CI-configured production modules;
  `mkdocs build --strict`, YAML parsing, and `git diff --check` passed.
- No workflow was dispatched; no source repository, lock, branch, pull request,
  remote setting, credential, merge, or deployment was changed.
