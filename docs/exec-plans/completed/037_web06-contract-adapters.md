# WEB-06 — Typed source-contract stages

## Scope
Retain the public loader facade; separate locks, checkout validation, common
values, reviewed policy constants, EUVICS versions, pyEUVICS package metadata,
notebook policy and candidate approval. Parse JSON once and emit immutable
validated records without coercing unknown values into strings.

## Progress
The loader facade delegates to explicit EUVICS 1.0/1.1 and pyEUVICS 1.0
adapters. Shared policy constants retain exact reviewed subsets; package and
notebook policy data become immutable typed records. JSON is decoded once.
Unknown input values are validated instead of coerced with str().
Before/after serialized SourceContract records, including notebook policies,
matched byte-for-byte for the same locked synthetic repositories. Existing
positive and rejection coverage remained unchanged.

## Verification
172 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
