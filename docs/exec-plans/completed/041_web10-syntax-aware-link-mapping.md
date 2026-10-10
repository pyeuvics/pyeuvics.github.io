# WEB-10 — Syntax-aware source destination mapping

## Scope
Validate and transform links using the exact renderer's parsed destinations.
Preserve source/code bytes; map Markdown-managed and raw HTML URLs using their
actual MkDocs behavior. Cover reference links, images, resource attributes,
PDF/notebook relocations, encoded paths, queries and fragments. Ambiguous or
unsupported source encodings fail closed. Keep probes bounded to 4096 spans.

## Decisions
Python-Markdown does not expose source positions. Inert per-span URL probes
identify only syntax that the exact parser renders as a destination, including
reference definitions, without a second Markdown parser or reserialization.
A final render verifies the complete destination multiset. File-to-URL mapping
uses MkDocs' own File implementation with reviewed directory URLs.

## Progress
Eleven reproduced link regressions now pass. Source-span probes use the exact
Markdown engine; only spans rendered as destinations are edited. A final render
checks destination multiplicities. Markdown-managed attributes and raw HTML
use distinct source/final URLs from MkDocs file mappings. Entity and percent
encoding, queries, fragments, reference labels and source code bytes are covered.
Approved notebook paths join the destination map, verified through real dual
notebook execution and assembled output. Nineteen golden/negative/built-site
cases plus directory-URL compatibility review cover the new behavior.
Unsupported or ambiguous forms and excessive probe counts fail closed.

## Verification
270 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
