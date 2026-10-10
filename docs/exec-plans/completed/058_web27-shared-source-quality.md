# WEB-27 — Shared secret-free source quality checks

## Scope
Use one test/type/build command set for local, PR and source-backed validation.
Strict typing covers all tools and shared test support. Keep the required check
name and source-read/proposal/deploy boundaries unchanged.

## Decisions
Ordinary local checks support an edited working tree and emit a non-reusable
record. Bound checks require immutable website/environment identity before and
after. Baseline and candidate may share website-only results only when the
receipt matches exact website bytes, installed distribution files, requirements,
interpreter, timestamp and check policy. Both source-backed assemblies still run
all source approval, document, notebook, ownership and artifact checks separately.

## Progress
Added tools.quality with shared commands covering all tools, including credential scanning, and typed test support. Local edited-tree checks emit non-reusable records; bound checks verify immutable website/environment identity. Source-backed validation can reuse an exactly matching receipt, rechecks the copied receipt and still runs both source-contract validators and each full artifact assembly. Eleven new cases cover secret-free orchestration, policy/input tampering, actual failure for a newly untyped tool and pre-promotion input changes; lifecycle tests verify source gates still run on reuse. Verified the complete change through the new shared CLI: 633 tests, strict mypy and strict scaffold build. No credentials, permissions, source locks or required job-name changes.

## Verification
633 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
