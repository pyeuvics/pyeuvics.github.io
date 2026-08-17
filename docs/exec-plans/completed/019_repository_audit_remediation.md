# Repository audit remediation

## Scope

Resolve the 2026-08-17 repository audit findings without changing scientific
content or publication approvals:

- repair the README references to the absent `docs/codex_tasks.md` file;
- retry and record the browser checks blocking active plans 012, 017, and 018,
  then close the stale plans without representing unavailable checks as passed;
- provide and verify a Python 3.13 local validation path matching CI.

## Boundaries

- Do not change source locks, publication manifests, scientific claims, Pages
  settings, credentials, or deployment state.
- Preserve unresolved browser findings rather than marking them as passing.
- Do not commit generated site output or a local virtual environment.

## Progress

- [x] Determine the intended disposition of `docs/codex_tasks.md` from history.
- [x] Repair README task-document references and ignore rules.
- [x] Retry and record browser review evidence for plans 012, 017, and 018.
- [x] Close completed plans using their existing sequential plan numbers.
- [x] Create and verify a Python 3.13 local environment matching CI.
- [x] Run the full suite, strict mypy, and `mkdocs build --strict`.
- [x] Record verification evidence and complete this plan.

## Verification evidence

- Removing the accidental `codex_tasks.md` ignore rule revealed the intended
  local task document. It is now tracked; two embedded personal absolute paths
  were converted to EUVICS-source-relative paths without changing their
  publication findings. Both README links resolve.
- Supported browser discovery was retried on 2026-08-17 and returned no
  available in-app or extension browser. Plans 012, 017, and 018 are closed at
  the owner's direction with that interactive review explicitly unresolved and
  not represented as passing.
- `/usr/local/bin/python3.13` is CPython 3.13.15. The ignored
  `.venv-docs-313` environment contains both pinned requirement sets and
  `pip check` reports no broken requirements. README and CI documentation now
  give explicit Python 3.13 setup commands.
- Python 3.13 verification passed: 73 tests in 99.98 seconds, strict mypy for
  12 source files, `mkdocs build --strict`, local-path scanning for changed
  documentation, and `git diff --check`.
