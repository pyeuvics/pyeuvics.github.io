# WEB-31 — Idempotent browser lifecycle and exact MathJax delivery

## Scope
Replace DOMContentLoaded-only drawer setup with disposable lifecycle handlers.
Serialize MathJax rendering after engine readiness and report load/render errors.
Pin the existing CDN dependency to reviewed compatible 3.2.2 and document its
license, update process and limits. Full-page navigation remains configured.

## Progress
Navigation now handles DOM readiness, Material document events and pageshow with explicit disposal; keyboard events no longer double-toggle through Material. MathJax waits for startup readiness, serializes new nodes and avoids duplicate output, clears replaced roots, and reports load/render failures with recovery. Reviewed official 3.2.2 startup/release/license documentation and retained existing CDN delivery with an exact version. All 657 Python tests and full quality pass; 14 real Chromium checks on scaffold/synthetic assembled pages plus controlled delayed-load/queue/error-recovery checks pass. These browser cases become a maintained harness in WEB-32. No hosted access, CSP, scientific math, or publication approval changes.

## Verification
657 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
