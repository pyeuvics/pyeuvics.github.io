# Organization site migration

## Scope

Update the website-owned canonical repository and GitHub Pages URL from the
former personal project site to the `pyeuvics` organization site. Preserve the
locked scientific source repositories and historical deployment evidence.

External repository settings, credentials, pull requests, pushes, and live
deployment are outside this local change.

## Decisions

- Canonical repository: `https://github.com/pyeuvics/pyeuvics.github.io`
- Canonical site: `https://pyeuvics.github.io/`
- Canonical base path: `/`
- `chongshikpark/euvics` and `chongshikpark/pyEUVICS` remain authoritative.
- Completed execution plans, dated release-readiness records, and the original
  task catalog retain their contemporaneous URLs and receive a migration note.

## Progress

- [x] Confirm local remotes and clean starting worktree.
- [x] Update governing, site, deployment, architecture, and checklist text.
- [x] Update active URL/base-path tests.
- [x] Add a migration record and mark historical documentation.
- [x] Run targeted tests, the full test suite, strict MkDocs build, and
      `git diff --check`.
- [x] Record verification and move this plan to `completed/`.

## Verification evidence

- `python3.13 -m pytest` initially could not find `pytest` in the unconfigured
  system interpreter. The repository's existing Python 3.13 documentation
  environment was used for the equivalent required check.
- `.venv-docs-313/bin/python -m pytest`: 76 passed in 41.37 seconds. The run
  required normal localhost socket access for Jupyter kernel tests.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- Generated `site/index.html` and `site/project/overview/index.html` use
  `https://pyeuvics.github.io/` canonical links and organization-repository
  edit links. No generated URL retained the old project-site prefix.
- `sources.lock.yml` remains unchanged and points to
  `chongshikpark/euvics` and `chongshikpark/pyEUVICS`.

## External follow-up

- Create new source-repository deploy keys and organization-repository Actions
  secrets; secret values cannot be migrated from the personal repository.
- Protect `main`, require site validation, verify Actions permissions, restrict
  the `github-pages` environment to `main`, select GitHub Actions as the Pages
  source, and set the repository homepage.
- Resolve personal-repository PR #7 deliberately.
- Push only after the external controls and credentials are ready, then verify
  the organization workflow and signed-out production site.
- Decide whether the personal repository becomes an archive or maintained
  non-deploying mirror.

