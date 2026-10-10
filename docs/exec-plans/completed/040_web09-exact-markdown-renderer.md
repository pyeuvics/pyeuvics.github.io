# WEB-09 — Exact website Markdown renderer

## Scope
Use MkDocs-validated extension order, defaults and options for publication
validation. Gate configuration changes with an explicit compatibility review.
Check math, headings, attributes, nested Markdown, raw HTML, code and tables
against the same engine configuration used by MkDocs pages.

## Progress
The publication renderer now uses MkDocs-normalized settings rather than a
parallel extension-name list. Compatibility gates check explicit settings,
effective defaults, option types and order before rendering. Fourteen behavioral
and compatibility tests cover math, heading anchors, attributes, nested Markdown,
HTML, code, tables, configuration drift and page-state isolation. The former
renderer demonstrably produced legacy math scripts and omitted heading anchors.
Existing executable-script rejection remains represented in the full suite.

## Verification
250 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
