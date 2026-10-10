# Final refactoring acceptance — 2026-10-10

The final synthetic matrix covers EUVICS schemas 1.0 and 1.1 crossed with
empty, partial and full approvals. Full cases combine an exact rebuilt PDF,
a notebook executed twice per build, a campaign, the complete overview figure
set, and inline/reference/HTML links. Pending material remains excluded.
These fixtures contain no private content or scientific calculation result.

## Complete artifact identity

All six cases build twice from the same locked source bytes, Python environment
and `SOURCE_DATE_EPOCH=1785628800`. Every public file name and byte is compared,
including compressed assets, search data, sitemap and provenance. The staging
plan, artifact plan, ownership manifest, inventory, notebook provenance and
available document toolchain evidence are also compared byte-for-byte. **No
file or metadata field is normalized away.** Review manifests are checked
against independently computed public-file sizes/hashes and against each other;
a controlled one-file change must appear exactly in proposal comparison data.

A seventh combined full-approval case alters the final copied PDF. Ownership
verification rejects it before promotion, records the failure phase only in an
owned incomplete workspace, preserves a caller-owned sentinel, and leaves both
source snapshots unchanged. Existing lifecycle, admission, privacy, cancellation,
proposal-state and evidence-tamper suites provide the wider negative matrix.

The complete artifact boundary is the public `site/` plus declared review
evidence. Disposable exported sources, generated local MkDocs configuration,
kernel workspaces and diagnostic command logs are build scratch data; they are
not uploaded public/review files. Their incidental local paths are not hidden by
normalizing a published artifact. Retained failed workspaces are diagnostic,
never releasable sites.

## Observed local costs

Python 3.13.16 on Intel macOS, with the reviewed dependency constraints. These
are wall-clock observations under local host load, not performance guarantees
or a controlled before/after comparison. Per-phase timing wraps the real
prepare/materialize/render/verify/finalize functions without replacing them.

| Approvals | EUVICS schema | Public files | Public bytes | Build 1 seconds | Build 2 seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| empty | 1.0 | 70 | 3,048,093 | 8.88 | 8.11 |
| empty | 1.1 | 70 | 3,048,093 | 8.11 | 11.26 |
| partial | 1.0 | 74 | 3,127,507 | 10.42 | 9.55 |
| partial | 1.1 | 74 | 3,127,507 | 9.42 | 9.80 |
| full | 1.0 | 83 | 3,257,999 | 31.24 | 30.83 |
| full | 1.1 | 83 | 3,257,999 | 32.23 | 28.61 |

Mean phase costs across the four full-approval builds:

| Phase | Mean seconds |
| --- | ---: |
| prepare | 2.451 |
| materialize | 16.334 |
| render | 5.008 |
| verify | 6.933 |
| finalize | 0.001 |

Observed process high-water RSS reached **163.1 MiB**; the terminated-child
high-water value reached **69.7 MiB**. These are process-lifetime
`getrusage` high-water marks (including earlier cases), not simultaneous total
memory or per-phase allocation measurements. Native macOS byte units were
confirmed with a 32 MiB touched-allocation probe. The Linux test log converts
its native KiB values to bytes. No timing or memory threshold makes the suite
flaky on a slower runner.

Materialization includes source exports, exact document work and dual notebook
execution; it is the largest measured full-build phase. No additional cache or
verification shortcut was introduced. Existing quality-receipt reuse remains
limited to equal immutable website/environment/time/policy identities and
never bypasses source approval, document/notebook or final-artifact checks.

## Final verification record

- Focused final matrix: **7 passed**; six repeated-build comparisons plus one
  full failure-containment case.
- Clean proposed-code snapshot in the isolated full Python environment:
  **670 tests passed**, dependency policy, bounded Ruff checks, strict typing
  (67 files), and strict MkDocs build passed. The bound quality receipt confirms
  the snapshot and installed environment were unchanged during the run.
- Chromium: **15 passed** from the clean snapshot with locked Node dependencies.
  The browser run preceded the evidence-only alias correction; frontend and
  assembly code were unchanged. No browser result is inferred from Python tests.
- Clean-checkout binding exposed the existing `CLAUDE.md → AGENTS.md` governance
  alias missing from the evidence policy. A failing regression reproduced it;
  the narrow fix accepts only the two reviewed aliases with tracked regular
  targets. Unknown, redirected, external and untracked-target aliases remain
  rejected, and hidden target edits remain detected. All 36 focused evidence
  checks passed after the fix.
- The receipt binds the disposable proposed-code snapshot, not the later final
  commit that records these outcomes and closes the backlog.
- The maintained browser layer covers scaffold and synthetic assembled pages;
  it does not certify hosted access or every assistive technology.

Real locked private-source assembly, GitHub-hosted runners, live settings,
actual CDN delivery and signed-out hosted release review were not exercised by
this local refactoring. Passing synthetic checks grants no source publication
approval. Source locks, numerical pins, scientific content and remote settings
remain unchanged; no push or deployment is part of acceptance.
