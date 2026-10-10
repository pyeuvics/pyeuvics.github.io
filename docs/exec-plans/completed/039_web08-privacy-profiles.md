# WEB-08 — Shared privacy scanning profiles

## Scope
Unify the reviewed path/key/token vocabulary for source, notebook, public
artifact and runner scans. Keep runner scanning key-only and dependency-free.
Stream bounded records, reject unreadable/oversized input, and never echo a
matched value. These heuristics do not confer publication approval.

## Progress
Shared source, notebook, public-artifact and runner profiles now use one stdlib-only
privacy vocabulary. Regression cases reproduced the missing notebook JWT check
and false-positive drive description before correction. Synthetic fixtures cover
tokens, escaped Windows/POSIX paths, safe URLs, unreadable and invalid UTF-8
inputs, oversized records, and markers crossing streamed blocks. Source assets
and public artifacts stream bounded records; runner scans remain key-only and
work with Python site-packages disabled. Heuristics do not establish approval.

## Verification
237 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
