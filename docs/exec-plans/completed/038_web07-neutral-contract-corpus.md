# WEB-07 — Independent publication conformance corpus

## Scope
Add versioned synthetic positive/negative vectors for EUVICS 1.0/1.1 and
pyEUVICS 1.0, with explicit expected admission and content-policy outcomes.
No private source data, upstream validator imports, or source-lock changes.

## Progress
Thirty versioned cases cover EUVICS 1.0/1.1 and pyEUVICS 1.0 approvals,
canonical paths, approval hashes, package metadata, unknown fields/versions,
pending/blocked candidates, notebook dependencies/policies, and rendered
content boundaries. Positive cases assert exact ordered admissions. Corpus
expectations are explicit data, not generated from production parser outputs.

## Verification
202 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
