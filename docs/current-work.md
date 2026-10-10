# Current work and governance

Start here for maintenance work. The [development runbook](development.md) owns
current commands; [architecture](architecture/README.md) describes supported
boundaries. Read [AGENTS.md](../AGENTS.md) before editing. The authoritative
scientific repositories remain `pyeuvics/euvics` and `pyeuvics/pyEUVICS`.

## Work queue

The owner authorized the ordered tasks in
[the 2026-10-10 refactoring backlog](refactoring_20261010.md), including a separate
local commit per task. Its checked task entries link to completed execution
plans. [Active plans](exec-plans/active/) show in-progress work and
[completed plans](exec-plans/completed/) retain task-specific decisions and
verification. WEB-35 and WEB-36 follow this governance task; update their status
only after their checks pass. [tasks/TODO.md](../tasks/TODO.md) is a short pointer
to this queue, not an independent contradictory backlog.

## Current boundaries and decisions

- Exact source locks and source-owned publication approvals determine admitted
  content. A test pass, candidate proposal, or old release authorization never
  grants new publication approval.
- PR validation is secret-free. Trusted source reading, proposal writing, and
  protected deployment remain separate; see [workflow boundaries](workflow-boundaries.md).
- Current navigation is the explicit `mkdocs.yml` configuration. The initial
  [scaffold/navigation decision](exec-plans/completed/003_mkdocs_site_foundation.md)
  is implemented; it is not pending foundation work.
- Scientific corrections and approval authority remain source-owned. No website
  document invents a release approver. Future branding, affiliations, contacts,
  custom domains and credential/settings changes still require specific approval.
- Local browser checks use public synthetic fixtures. Signed-out hosted release
  review remains separate and is not claimed complete by the refactoring.

## Historical records

`docs/codex_tasks.md`, dated review snapshots, migration records and completed
plans preserve what was requested or observed at the time. They are evidence,
not executable current instructions. Do not rerun foundation tasks, revive
obsolete private-source PR guidance, or reuse historic deployment/credential
permissions. Add a dated superseding note or link instead of rewriting old
measurements or silently erasing an unresolved decision. When an outcome is
known, link its completed record; otherwise keep the owner decision explicit.

This owner-requested implementation follows the formerly review-only backlog;
its original reviewed HEAD, baseline results and findings remain historical.
The backlog was already tracked when this reconciliation began. Review-only
storage language does not describe its current tracked execution status.
