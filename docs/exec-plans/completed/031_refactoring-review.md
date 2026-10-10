# Website refactoring review — 2026-10-10

## Scope

Review the website repository at `b62dc0ace6898a6f1db3436fe397c51ecc204880`
and prepare a sequential, evidence-backed refactoring backlog under `docs/`.
Keep this plan and the review output untracked. Do not implement refactors,
change source locks or dependencies, stage, commit, push, deploy, or change
credentials or remote settings. Source repositories are outside this review.

## Progress

- [x] Read repository instructions and inventory tracked implementation,
      configuration, tests, website content, and documentation.
- [x] Inspect assembly, contract, document, notebook, and update boundaries.
- [x] Complete isolated baseline checks and focused synthetic probes.
- [x] Write task priorities, dependencies, evidence, and acceptance checks.
- [x] Verify the review files remain untracked and tracked files unchanged.

## Verification boundaries

Use a disposable local clone for tests, typing, strict build, and synthetic
diagnostics. Do not fetch private sources, execute live update/deployment
workflows, or inspect secret values. Distinguish confirmed local behavior from
proposed design improvements and checks not performed.

## Outcome

Created [the 36-task refactoring backlog](../../refactoring_20261010.md),
including sequential order, dependencies, priorities, task types, concrete code
references, reproduced edge cases, acceptance checks, and risk boundaries.
The backlog is a snapshot-based review, not a claim that all possible future
issues have been ruled out. It separates hardening/bug fixes from mechanical
refactors and retains the website's independent consumer role.

Local macOS verification with the existing Python 3.13.16 documentation
environment: 130 tests passed in 95.87 seconds, strict mypy passed on all 13
tooling modules, the standalone strict MkDocs build passed, and pip reported
no broken requirements. Synthetic probes confirmed the specific gaps recorded
in the backlog. No production source-backed build, fresh installation, hosted
workflow, live browser/accessibility review, or deployment was performed.

Only this execution record and the backlog were added. Both remain untracked;
the Git index and all tracked implementation/configuration/content files are
unchanged. No source locks, scientific code, dependencies, credentials, remote
settings, or approvals changed. No staging, commit, push, or deployment occurred.
