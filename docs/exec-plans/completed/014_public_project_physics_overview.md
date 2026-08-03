# Public project physics overview — completed

## Scope

Lock the website to the Task 2-approved EUVICS publication commit and replace
the project-overview placeholder with a scientifically careful summary derived
only from locked, allowlisted EUVICS and pyEUVICS sources.

## Boundaries

- Do not publish Proposal/CDR PDFs, the restricted CDR layout figure, costs,
  internal records, notebooks, or campaigns.
- Preserve kinetic-energy and angle conventions, model assumptions, CAIN
  disagreement, provisional 13.5 nm status, and synthetic-calibration limits.
- Keep equations as explanatory documentation; pyEUVICS remains the sole
  implementation.
- Do not push or deploy.

## Plan

- [x] Update only the EUVICS lock to approved commit
      `f142bd188892f9518a956989ebaf7a42b6930f33` and validate ancestry/contracts.
- [x] Rewrite `content/project/overview.md` with the required accessible
      structure, equations, output-control table, status labels, and links.
- [x] Add deterministic assembled-build provenance for the overview and tests.
- [x] Run focused and full tests, strict local and assembled builds, artifact
      scans, and base-path/link checks.
- [x] Defer desktop, mobile, equation, table, theme, and print visual inspection
      by user direction on 2026-08-04.
- [x] Record verification evidence and move this plan to `completed/`.

## Verification evidence

- Source-lock transition verification and Git ancestry verification passed for
  EUVICS `f142bd188892f9518a956989ebaf7a42b6930f33`; pyEUVICS remains locked at
  `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`.
- All 62 tests passed in bounded groups: 26 general/overview tests, 24 core
  source-assembly tests, 7 notebook-execution tests, and 5 source-update tests.
- Ruff passed for all changed Python files. Strict mypy passed for the complete
  validation tool set.
- `mkdocs build --strict` passed for the authored site.
- Production-equivalent assembly passed with 56 approved files at
  `SOURCE_DATE_EPOCH=1785628800`; the final site and inventory are under
  `/private/tmp/euvics-task3-assembly-final/` and the artifact scan passed.
- Generated HTML contains MathJax wrappers for inline and display equations,
  relative imported-source links, and both exact locked commits. `git diff
  --check` passed.
- Visual desktop/mobile, light/dark, and print inspection was explicitly
  deferred by user direction on 2026-08-04 and is not a Task 3 completion gate.
