# WEB-13 — Typed staging plan and destination ownership

## Scope
Precompute fixed staged outputs, exact source input identities/checksums,
producer/owner relationships and source-to-destination bindings before writing.
Reject duplicate paths, file/directory conflicts, portable case/Unicode aliases
and invalid portable names. Reserve exclusive notebook asset namespaces, then
register each emitted asset before writing because filenames depend on execution.
Keep public routes and the existing source inventory schema unchanged.

## Progress
Deterministic plans cover empty, partial and full approvals, PDFs, notebook pages,
website-owned transformations and generated provenance. The destination registry
rejects duplicate destinations, file/directory conflicts, Unicode/case aliases
and non-portable names before materialization. Notebook assets use exclusive
planned namespaces and each emitted asset is registered before writing.
Document, notebook and import producers consume shared source bindings.
Twenty-five tests verify exact input hashes/commits, relationships, stable plans,
namespace ownership and failure before output creation. The plan is retained
as an internal staging-plan.json; existing public inventory schema is unchanged.

## Verification
369 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
