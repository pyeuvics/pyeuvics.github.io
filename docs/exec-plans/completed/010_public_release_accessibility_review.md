# Public release and accessibility review — active

## Scope

Execute Task 10 from `docs/codex_tasks.md`: audit the complete proposed public
artifact against publication, provenance, base-path, content, security,
accessibility, and presentation requirements; check the public project URL; and
produce a severity-ranked release-readiness report with exact evidence, owners,
and retest requirements.

## Boundaries

- Do not deploy, dispatch a workflow, approve an environment, enable Pages,
  change visibility/settings/protection, add credentials, or change scientific
  or publication status.
- Do not close a finding without verification.
- Treat unavailable live signed-out browser testing as a release blocker, not
  as passed evidence.
- Preserve all source and website working trees.

## Planned work

- [x] Assemble and validate the artifact from both exact locked source commits.
- [x] Inventory routes, navigation, search, provenance, downloads, and status.
- [x] Verify base-path, links, checksums, files, exclusions, and secret/path scans.
- [x] Review equations, tables, code, notebook/campaign/PDF publication state,
      citations, licenses, attribution, permissions, and limitations.
- [x] Review static accessibility markup, styles, responsive rules, and print.
- [x] Check the public URL and attempt signed-out interactive browser review.
- [x] Write a severity-ranked report with owners and precise retest criteria.
- [x] Run repository tests and strict build, record evidence, and complete plan.

## Verification evidence

- Exact locked-source assembly succeeded with the reproducible timestamp
  `2026-08-02T00:00:00Z`: 0 EUVICS and 53 pyEUVICS approved files produced 68
  HTML pages.
- Inventory review confirmed 51 imported Markdown pages each include the locked
  commit, version 0.5.0, publication status, source checksum, source/edit links,
  timestamp, and required scientific limitations. `LICENSE` and `CITATION.cff`
  are present; PDFs, notebooks, campaign outputs, raw data, and source-only
  material remain excluded.
- Generated-artifact checks found zero broken local references, zero
  root-relative links outside the special 404 page, zero personal absolute
  paths, and no credential-like material. There are 94 math containers, 10
  tables, 80 code blocks, and one admonition.
- Static HTML review across all pages found main landmarks, no duplicate IDs,
  no heading-level skips, and alternative text for both image badges. CSS and
  scripts provide focus, keyboard drawer operation, reduced motion, responsive
  overflow containment, and print rules; these remain static rather than live
  browser evidence.
- The public URL returned GitHub `HTTP/2 404` on 2026-08-02. Browser discovery
  and the documented retry found no browser instance, so live signed-out,
  viewport, zoom, keyboard, focus, print, search, equation, PDF, and custom-404
  behavior remains unverified.
- The severity-ranked report is
  `docs/release-readiness/2026-08-02_task10.md`: one Critical and four High
  findings remain open with exact paths/URLs, owners, actions, and retests.
- Repository verification passed: 46 non-notebook tests plus all seven
  localhost-kernel notebook tests (53 total), strict mypy for nine CI source
  files, `mkdocs build --strict`, and `git diff --check`.
- No deployment, workflow dispatch, environment approval, remote setting,
  credential, source content, publication status, or visibility was changed.
