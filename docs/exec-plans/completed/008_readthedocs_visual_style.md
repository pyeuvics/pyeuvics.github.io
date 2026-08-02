# ImpactX-inspired Read the Docs presentation — active

## Scope

Implement the presentation-only task in `docs/CODEX_TASK_READTHEDOCS_STYLE.md`
as an original classic documentation layout while preserving MkDocs Material,
content, source contracts, publication behavior, and deployment permissions.

## Boundaries

- Do not copy or hotlink ImpactX/Read the Docs CSS, fonts, images, branding,
  analytics, advertising, or generated markup.
- Do not change scientific content, source locks/allowlists, workflows, or
  repository identity.
- Keep the canonical stylesheet at the requested `docs/stylesheets/` path. The
  repository uses `content/` as MkDocs `docs_dir`, so expose the same file at
  `content/stylesheets/` without changing the documentation architecture.
- Do not deploy or push.

## Planned work

- [x] Add locally owned design tokens and classic documentation styling.
- [x] Configure breadcrumbs, code-copy controls, and the served stylesheet.
- [x] Implement fixed 300 px desktop navigation and bounded reading surface.
- [x] Preserve Material's accessible mobile header/drawer and add responsive,
      focus, reduced-motion, zoom, overflow, and print rules.
- [x] Add structural, asset, base-path, and presentation tests.
- [x] Build strictly and inspect generated pages/components.
- [x] Perform browser visual/keyboard checks if the browser surface becomes
      available; otherwise record that limitation explicitly.
- [x] Run the complete repository test and CI-equivalent validation set.
- [x] Record evidence and move the plan to completed.

## Verification evidence

- `18 passed`: presentation, site-foundation, and CI-validation tests.
- `24 passed, 7 deselected`: source-assembly tests not requiring a notebook
  kernel; all seven notebook tests also passed separately with localhost kernel
  access (`1 passed` and `6 passed`). This accounts for all 49 repository tests.
- `6 passed`: targeted Read the Docs style contract tests.
- Strict MkDocs build completed successfully in 0.56 seconds.
- Strict mypy validation passed for the nine CI-configured source files.
- `git diff --check` passed.
- Generated home and nested science pages were inspected structurally for
  stylesheet resolution, breadcrumbs, drawer markup, navigation enhancement,
  and project-site-safe local assets.
- WCAG contrast calculations passed for body, link, sidebar, muted sidebar,
  and active-state text pairs. Focus, reduced-motion, print, narrow-content,
  responsive asset, and horizontal-overflow rules are covered by tests.
- Browser runtime discovery and the documented retry found no available
  in-app browser instance. Therefore no claim is made that 1280, 1024, 768,
  390 px, 200% zoom, keyboard, or rendered print pages received live visual
  inspection. This is the remaining review limitation.
