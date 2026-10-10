# WEB-14 — Isolated build phases and exclusive finalization

## Scope
Separate planning, materialization, rendering, verification and finalization
with immutable build context. Create uniquely owned sibling workspaces, retain
labelled failed workspaces, and exclusively promote verified output. Never
replace existing destinations, including empty directories or symlinks.
Unify timestamp validation for CI/direct builds without mutating process state.
CI review manifests must succeed before the requested review output appears.

## Platform decision
Use Windows rename, macOS renamex_np(RENAME_EXCL), and Linux
renameat2(RENAME_NOREPLACE). Ordinary POSIX rename can replace an empty directory.
Unsupported platforms/filesystems fail closed and retain diagnostics. Same-parent
workspaces avoid cross-filesystem promotion; no atomicity claim is made for
unsupported/network filesystem behavior. Native macOS flags were checked against
the installed SDK sys/stdio.h; Linux semantics follow
https://man7.org/linux/man-pages/man2/rename.2.html .

## Progress
Five reproduced output/timestamp failures are resolved. Immutable build inputs
and context separate plan, materialize, render, verify and finalize phases.
Failed workspaces are labelled INCOMPLETE.json and retained separately from the
requested output; retries use fresh owned workspaces. Native exclusive promotion
preserves even an empty destination created after the precheck. CI validation
also waits for review-manifest completion before promotion. Direct/CI timestamp
validation is shared, representable and non-negative; subprocesses receive the
epoch explicitly. Fourteen lifecycle tests cover failures/retries at each phase,
real-render retry, native promotion races, CI review failure and environment
isolation. Native macOS execution is tested locally; other hosted platforms
remain subject to their own CI run.

## Verification
383 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
