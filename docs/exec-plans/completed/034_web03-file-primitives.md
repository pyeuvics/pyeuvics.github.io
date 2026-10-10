# WEB-03 — Shared filesystem/process primitives

## Scope
Share streaming hashes, locked-tree archive export, atomic small-file writes,
and bounded command output. Preserve caller-specific document/notebook errors.
Test malicious members, immutable exports, failed commands, and atomic failure.

## Progress
Document and notebook exporters use one disk-spooled, POSIX-member-validated
archive helper. Four hash consumers share streaming reads. Review manifests
and staged inventories use atomic UTF-8/LF replacement. Failed commands report
context and exit status without echoing arguments or untrusted output.
Fourteen focused cases cover unsafe members, exact exports, unreadable input,
atomic replacement failure, missing tools, nonzero exits and output bounds.

## Verification
144 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
