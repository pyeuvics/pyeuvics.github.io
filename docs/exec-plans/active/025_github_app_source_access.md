# GitHub App source access

## Scope

Replace private-source deploy-key authentication with a narrowly scoped,
short-lived GitHub App installation token in all source-reading workflows.
Preserve exact source locks, checkout paths, validation, and least-privilege job
permissions.

## Starting state

- `EUVICS_DOCS_APP_ID` and `EUVICS_DOCS_APP_PRIVATE_KEY` are present as
  repository Actions secrets.
- The App is reported installed on `pyeuvics/euvics` and
  `pyeuvics/pyEUVICS` with read-only source access.
- The local branch contained existing migration commits ahead of `origin/main`;
  those commits were preserved.

## Work

- [x] Mint one installation token per source-reading job.
- [x] Use the token for all exact source checkouts without persisting it.
- [x] Update workflow contract tests and credential documentation.
- [x] Run the full test suite, strict MkDocs build, and diff checks.
- [ ] Record verification and complete this plan.

## Local verification

- `.venv-docs-313/bin/python -m pytest`: 76 passed in 36.96 seconds.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- Workflow contract tests confirm one token action per source-reading job,
  exactly two repository targets, Contents read-only scope, token-based source
  checkouts, and `persist-credentials: false`.

## External verification

After the workflow change reaches GitHub, verify token creation, both private
checkouts, credential cleanup, artifact validation, and Pages deployment.
