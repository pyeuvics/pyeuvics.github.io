# WEB-24 — Typed review manifests and complete comparisons

## Scope
Share the version-1 manifest contract between writer and reader. Enforce exact
fields, canonical unique sorted paths, digest strings and strict integer counts.
Separate pure complete comparison from bounded human-readable report rendering.

## Decisions
Retain version 1 and reject malformed legacy records rather than silently
coercing them. Paths are metadata; the reader never opens their targets. Store
all differences in a sibling machine-readable JSON record, with explicit
truncation counts in the Markdown report. No new scientific approval claims.

## Progress
Added typed version-1 review records shared by the writer and reader, with exact fields, canonical sorted unique paths, finite integer byte counts and digest strings. Pure comparisons include byte metadata changes and retain all paths in a companion JSON file; Markdown reports explicitly state truncation and escape path text. Twenty-nine new tests cover malformed/ambiguous inputs, duplicate JSON keys, version-1 round trips, complete comparisons, truncation and symlink rejection. Reader paths remain metadata and are never opened. No workflow permissions or source locks changed.

## Verification
561 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
