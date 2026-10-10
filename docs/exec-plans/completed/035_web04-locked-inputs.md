# WEB-04 — Bind consumed inputs to locked Git objects

## Scope
Reject ignored/untracked input files and index-hidden byte mutations. Recheck
consumed files at admission and use boundaries, including citation, notebook
dependencies, configuration and approved document baselines. Preserve the
tracked approved-release versus disposable rebuilt-document distinction.

## Progress
Six regressions first failed, then passed: ignored ordinary content, citation,
notebook dependency and PDF baseline; index-hidden mutation; mutation after
admission. Each consumed path must be a regular blob in the locked tree and
its raw-byte Git object hash must match. Checks repeat at copy, document and
notebook use boundaries and before successful assembly return. Existing
symlink, dirty-source, commit-mismatch and approved-PDF rebuild cases remain.
This is not a claim of protection against a concurrently hostile host.

## Verification
150 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
