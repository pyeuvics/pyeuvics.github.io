# Local MkDocs site foundation — completed

## Scope

Task 4 from `docs/codex_tasks.md`: create a local, non-deploying MkDocs website
foundation matching the approved Task 1 information architecture.

## Boundaries

- Use placeholders only; do not import source-repository content, check out
  sources, build PDFs, render notebooks, add workflows, or deploy.
- Set the canonical URL exactly to
  `https://chongshikpark.github.io/euvics.github.io/` and preserve project-site
  base-path behavior.
- Do not invent branding, affiliations, contacts, scientific values, approval,
  release, or validation status.
- Source locks may use explicit unresolved placeholders in this task; later
  assembly must reject unresolved or mismatched commits.

## Planned work

- [x] Add reviewed pinned documentation dependencies and `mkdocs.yml`.
- [x] Add explicit navigation and placeholder pages for every approved section.
- [x] Configure MathJax, accessible status-label styling, keyboard focus,
      responsive tables/layout, and print behavior.
- [x] Add `sources.lock.yml`, tools/tests foundations, and local commands.
- [x] Add automated checks for URL/base path, navigation, placeholders, local
      paths, status labels, MathJax, ignored output, and strict build output.
- [x] Install documentation dependencies in an ignored local environment.
- [x] Run targeted tests and `mkdocs build --strict`.
- [x] Review desktop/mobile structure and keyboard focus at a basic level.
- [x] Record versions, warnings, evidence, and unresolved decisions, then move
      this plan to `completed/`.

## Implementation decisions

- Material for MkDocs remains the approved generator/theme.
- Placeholder pages describe publication requirements and unresolved decisions;
  they do not apply controlled badges to unapproved source material.
- A small website-owned status-language demonstration may show the controlled
  terms as examples, clearly labeled as vocabulary rather than project status.

## Completed work

- Added MkDocs/Material configuration with the exact project-site URL, explicit
  15-page navigation, search, repository/edit links, light/dark schemes,
  MathJax, custom styling, and a root 404 override.
- Added placeholder-only Home, Project, Documents, pyEUVICS, campaign,
  Downloads, and About pages. No authoritative source content or artifacts were
  imported and no project/scientific status was assigned.
- Added unresolved `sources.lock.yml` records for EUVICS and pyEUVICS; future
  assembly must replace both null commits with reviewed 40-character commits.
- Added local commands, ignored `.venv-docs/` and `site/`, a tools placeholder,
  and six automated foundation tests.

## Dependency versions

- Python 3.14 (local documentation environment)
- MkDocs 1.6.1
- Material for MkDocs 9.7.7
- pytest 9.1.1

Direct dependencies are pinned in `requirements-docs.txt`, separately from the
pyEUVICS runtime environment.

## Verification evidence

- `.venv-docs/bin/python -m pytest -q`: 6 passed.
- `.venv-docs/bin/mkdocs build --strict`: passed; MkDocs reported no content,
  navigation, link, or configuration warnings and built in approximately 0.8
  seconds.
- Material for MkDocs printed its upstream advisory about incompatible,
  currently unlicensed MkDocs 2.0. This scaffold remains pinned to MkDocs 1.6.1
  and the advisory did not produce a strict-build failure.
- Artifact inspection confirmed the canonical project URL, relative internal
  links from ordinary pages, `/euvics.github.io/` links on the root 404 page,
  a nonempty search index, MathJax markup/scripts, and all 15 page outputs.
- Root `404.html` uses the custom accessible message and canonical home link;
  no redundant `/404/` page is generated.
- Static responsive/accessibility review confirmed Material's viewport,
  keyboard skip link, labeled search and mobile drawer controls, custom
  `:focus-visible` outline, text-bearing status labels, mobile table overflow,
  and print rules that preserve content while removing navigation chrome.
- Local-path and unexpected root-relative-link scans passed; `git diff --check`
  passed; `git check-ignore` confirmed both `site/` and `.venv-docs/` are
  ignored.

## Remaining decisions

- Replace both unresolved source commits only after publication-contract review.
- Approve branding, logo, affiliations, contact route, and any custom domain in
  a separate owner decision.
- Review real imported pages and PDFs for accessibility once approved content
  exists; this task could review only the placeholder scaffold.
