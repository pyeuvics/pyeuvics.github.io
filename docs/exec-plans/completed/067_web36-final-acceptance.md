# WEB-36 — Independent final artifact and performance acceptance

## Scope
Compare every public artifact byte and declared review evidence across repeated
builds with fixed source locks, epoch and environment. Exercise both EUVICS
schemas and empty/partial/full synthetic approval states with PDF, notebook,
campaign, figure and mixed links. Verify failure containment and proposal
manifest evidence independently. Record phase timing and process memory limits.
Run final quality and browser checks from a clean proposed-code snapshot.

## Decisions
No artifact files or provenance fields are normalized away. Build scratch paths
are diagnostic workspace data, not public/review artifacts. Measurements are
observational under local load, not cross-platform performance promises. Do not
add a cache or remove source/publication/final-artifact checks to improve time.
Real locked private-source assembly and hosted/signed-out review remain outside
this separately authorized local synthetic acceptance scope.

## Progress
Completed the six repeated-build schema/approval combinations and full PDF
failure-containment case. Compared all public file bytes and declared review
evidence, independent manifest hashes/sizes, controlled comparison changes and
source snapshots. Recorded real phase timings and scoped RSS observations in
`docs/refactoring-acceptance.md`; no cache or verification shortcut was added.

The clean bound-quality run exposed the pre-existing `CLAUDE.md → AGENTS.md`
alias missing from evidence policy. A regression failed before correction;
allow only the two reviewed internal aliases with tracked regular targets,
and retain rejection of unknown, redirected, external or untracked targets
and hidden tracked-target changes. All 36 focused evidence tests passed.

Final quality ran from a clean disposable proposed-code snapshot in the isolated
full environment: dependency policy, bounded lint, 670 tests, strict typing of
67 files and strict MkDocs passed, with unchanged bound website/environment.
All 15 Chromium checks passed from the clean snapshot before the evidence-only
alias correction; frontend and assembly code stayed unchanged. The receipt
binds that proposed-code snapshot, not this later documentation-closing commit.
All 36 backlog tasks and the cross-cutting acceptance checklist are complete.
Hosted/private-source release checks and publication approval remain separate.
No push, deployment, source-lock or numerical-pin change occurred.

## Verification
670 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
