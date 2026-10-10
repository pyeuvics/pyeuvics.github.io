# WEB-02 — Separate test responsibilities

## Scope
Split contract/parser, staging, PDF, notebook, link, workflow and presentation
coverage without dropping the 130 baseline cases. Keep full CI selection.
Run contract rejection checks at admission and retain assembly failures.
Share a session scaffold build for presentation tests.

## Progress
All 130 baseline case names and parameters are preserved. Contract admission
failures now exercise the loader directly, while integration cases retain
source dirt, commit mismatch, unsafe links, PDF rebuild and notebook failures.
The default pytest invocation still runs every tier; no filtering was added.

## Verification
130 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update. Local commits authorized; no push.
