# WEB-12 — Typed metadata page views and contextual escaping

## Scope
Keep external metadata literal in generated headings, links, HTML, table cells,
provenance and limitation lists. Introduce typed document/notebook page views
and shared metadata/provenance renderers. Preserve approved scientific Markdown
verbatim, retain Unicode and line breaks, and expose notebook license/attribution.
Capture ordinary page rendering before implementation as a compatibility snapshot.

## Progress
Seventeen reproduced metadata failures are resolved. Typed document/notebook
views share literal text, URL, table, code, provenance and limitation renderers.
Contextual escaping retains Unicode, boundary whitespace and line breaks while
preventing HTML, Markdown, math and table injection from plain metadata.
Source Markdown remains untouched. Ordinary document rendering matches the
pre-change snapshot; notebook rendering preserves its snapshot plus explicit
license/attribution rows. Thirty-two cases exercise malicious and long values,
quotes, attributes, URLs, generated entry/campaign pages and retained source prose.

## Verification
344 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
