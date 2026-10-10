# WEB-21 — Typed finite overview artifact validation

## Scope
Parse a typed overview descriptor and data table. Validate exact headers and
counts, finite positive values, the reviewed linear kinetic-energy grid, package
identity/version, complete model settings, declared files/status and accessible
SVG identifiers. Wrap JSON/XML/CSV failures in OverviewFigureError.

## Decisions
The reviewed model is a website-owned data record matching the already reviewed
source artifact. It is a compatibility gate, not an implementation of physics.
Compare grid coordinates with absolute tolerance 1e-12 to accommodate CSV float
serialization; require strict positive decreasing wavelengths without computing
the model. Preserve generator provenance as a source claim; a syntactically valid
commit is not independent verification of its scientific or Git history claims.
Test the three existing locked figure bytes through this structural validator
without executing source code, refreshing locks, or publishing new material.

## Progress
Added typed overview descriptor and table, complete data-driven reviewed settings, domain errors, package/artifact consistency, positive finite numbers and accessible SVG structure. Twenty-nine added cases reject invalid roots, versions, metadata, grids, CSV values/shapes/trends and SVG labels. Independently checked the three existing locked figure files from f6211eeb97c375262a087f98dc178b038fc9ee66 through the validator: accepted 61 points and original descriptor. No source execution, approval, lock or artifact changes.

## Verification
517 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
