# GitHub App source access

## Scope

Replace private-source deploy-key authentication with a narrowly scoped,
short-lived GitHub App installation token in all source-reading workflows.
Preserve exact source locks, checkout paths, validation, and least-privilege job
permissions.

## Starting state

- `EUVICS_DOCS_APP_CLIENT_ID` is present as a repository Actions variable, and
  `EUVICS_DOCS_APP_PRIVATE_KEY` is present as a repository Actions secret.
- The App is installed on `pyeuvics/euvics` and `pyeuvics/pyEUVICS` with
  Contents read-only access.
- Existing migration commits ahead of the former `origin/main` were preserved.

## Completed work

- [x] Mint one installation token per source-reading job.
- [x] Use the token for all exact source checkouts without persisting it.
- [x] Update workflow contract tests and credential documentation.
- [x] Update Pages actions to Node.js 24-compatible releases.
- [x] Run the full test suite, strict MkDocs build, and diff checks.
- [x] Verify private checkouts, artifact validation, and deployment in Actions.

## Verification

- `.venv-docs-313/bin/python -m pytest`: 76 passed in 40.72 seconds.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- Workflow contract tests enforce one token action per source-reading job,
  exactly two repository targets, Contents read-only scope, token-based source
  checkouts, and `persist-credentials: false`.
- GitHub Actions run `33690783901` proved the initially converted App token,
  both exact private checkouts, credential cleanup, complete artifact
  validation, upload, and Pages deployment.
- GitHub Actions run `33691189388` passed after switching to the recommended
  Client ID input and Node.js 24-compatible `configure-pages@v6` and
  `upload-pages-artifact@v5`; both build and deployment jobs succeeded without
  the prior deprecation annotations.

## Outcome

GitHub App source access is operational for the two organization-owned private
sources, and the validated site deploys successfully from `main`.
