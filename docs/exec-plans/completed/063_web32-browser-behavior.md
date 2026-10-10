# WEB-32 — Bounded real-browser behavior verification

## Scope
Track Chromium checks for scaffold and real synthetic assembled pages. Cover
keyboard routes, search, equations, lifecycle errors, local overflow, zoom,
focus contrast, reduced motion, print, headings, captions, downloads and 404s.
Replace CSS/JS string assertions with behavior checks; retain source ownership
and scientific qualification assertions.

## Decisions
Use exact Playwright 1.64.0 and MathJax 3.2.2 development dependencies with npm
lock integrity and Node 24. A loopback-only fixture server builds disposable
synthetic sources. Browser requests are local or fulfilled from installed
MathJax; other network is blocked. Existing required source check name and
read-only permissions stay unchanged. No private sources or hosted access.

## Progress
Tracked exact Playwright 1.64.0 and MathJax 3.2.2 dependencies, integrity lock, Node 24 configuration, and a disposable loopback fixture server. Fifteen Chromium cases cover desktop/mobile keyboard routes, focus, search, equations and failures, repeated lifecycle setup, responsive overflow, zoom/contrast, reduced motion, print, captions/headings, downloads/notebooks and custom 404s. Both scaffold and synthetic approved PDF/notebook/campaign assemblies run without private content; external browser/worker requests are blocked or locally fulfilled. Server shutdown cleans its temporary directory. All 655 Python tests, strict typing of 67 files, strict build and actionlint pass. Hosted signed-out and assistive-technology review remains separately documented; no remote action occurred.

## Verification
655 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
