# WEB-01 — Extract synthetic fixture builders

## Scope and authorization
Implement WEB-01 from the dated backlog. The owner authorized sequential
implementation with one local commit per task on 2026-10-10; do not push.

## Plan
- Extract synthetic repository, manifest, PDF, notebook, campaign, lock, and overview builders.
- Share repository and lock setup with source-update tests.
- Isolate fixture Git identity, signing, hooks, and global settings.
- Preserve all 130 baseline cases and their assertions.
- Run the full suite, strict tooling typing, strict MkDocs build, and whitespace checks.

## Progress
Completed the extraction and shared synthetic Git/lock initialization.
All assembly and overview test bodies are unchanged; two source-update tests
now use shared initialization. Fixtures retain explicit malformed-value knobs.
Git user identity, signing, hooks, and global/system settings are isolated.

## Verification
- All 130 existing cases passed (88.46 seconds), including real notebook kernels.
- Strict mypy passed for 13 tooling and 3 test-support modules.
- Standalone strict MkDocs build passed; whitespace checks passed.
- The first sandboxed run could not open notebook sockets (126 pass, 4 fail);
  rerunning with permitted local sockets passed without weakening any test.

No source locks, dependencies, scientific content, or production logic changed.
This task is complete. WEB-02 is next; website work was interrupted by the
owner's request to repair pyEUVICS Windows CI.
