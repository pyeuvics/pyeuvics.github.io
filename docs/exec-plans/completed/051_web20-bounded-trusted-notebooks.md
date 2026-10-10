# WEB-20 — Bound trusted notebook execution

## Scope
Add a total execution deadline, message/output/cell budgets, monitored runtime
file/byte limits and cancellation cleanup. Give every run a distinct source
copy and writable runtime/home/temp directories. Preserve source immutability,
independent execution twice, credential scrubbing and static MIME policy.

## Trust boundary and decisions
Only reviewed, approved, exactly locked source code may execute. This is not a
filesystem/network sandbox or an OS memory/CPU quota. Python audit events reject
ordinary reads of undeclared data inside the exported source tree, source writes
and unmanaged Python child-process launches. Native I/O or deliberate bypasses
are outside this trusted-source model; regexes never establish complete data
access or network isolation. No OS/container/network controls, platform packages
or additional credentials are introduced. Untrusted execution requires a
separately approved isolation design.
Limits cover accumulated decoded messages and observed runtime files; they do
not promise a hard peak-memory bound before a message is decoded or a hard
filesystem quota between polls. A violation, unsupported guard setup, timeout,
partial error or cancellation prevents publication. The kernel is shut down
immediately and its connection resources removed on every exit.

The Python event vocabulary is checked against the [CPython 3.13 audit-event
table](https://docs.python.org/3.13/library/audit_events.html). It is not an
untrusted-code security boundary.

## Progress
Implemented bounded execution, independent run directories, source mutation guards and ordinary Python process/data access checks. Twenty-six additional cases cover timeout, output and runtime overflow, undeclared data, source writes, unmanaged processes, partial errors, cancellation cleanup and normal Matplotlib execution. Cancellation also unregisters the nbclient exit callback. Limits and trusted-source boundaries are documented explicitly; no untrusted-code sandbox, OS peak quota or complete native-access guarantee is claimed.

## Verification
488 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
