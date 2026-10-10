# WEB-25 — Testable proposal lifecycle and bounded recovery

## Scope
Extract duplicate/orphan discovery and proposal writes from workflow shell.
Keep read-only gate and explicitly authorized write interfaces separate.
Use paginated GitHub reads and distinguish failures from an empty result.

## Decisions
GitHub pagination follows the [CLI API contract](https://cli.github.com/manual/gh_api)
and [pull-request endpoint](https://docs.github.com/en/rest/pulls/pulls#list-pull-requests).
Only this run's numeric proposal branch and exact created commit may be removed,
using a force-with-lease compare-and-delete. Recover an already-created PR after
a lost response; retain ambiguous state. SIGTERM/interrupts attempt recovery;
SIGKILL/runner loss can leave an orphan, which blocks the next automatic proposal
and requires explicit review. No sweeping cleanup. Tests use injected runners
and create no real remote branches, pull requests or pushes.

## Progress
Extracted a standard-library read gate, pure active/orphan/recovery decisions and an explicit write-only proposal interface. API errors do not imply empty results; paginated reads include all PR associations. Create-only push and compare-and-delete leases protect existing or changed refs. Lost PR responses preserve already-created proposals; failures, cancellation and ambiguous recovery retain or remove only the run-owned ref. Thirty new mock cases cover these states and require no remote calls. Existing workflow permissions, source token creation and job separation remain; no actual push or pull request was performed.

## Verification
591 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
