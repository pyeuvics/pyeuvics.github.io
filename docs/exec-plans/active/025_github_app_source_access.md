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
- The local branch is two commits ahead of `origin/main`; those commits and the
  untracked `docs/github_app.md` are user work to preserve.

## Work

- [ ] Mint one installation token per source-reading job.
- [ ] Use the token for all exact source checkouts without persisting it.
- [ ] Update workflow contract tests and credential documentation.
- [ ] Run the full test suite, strict MkDocs build, and diff checks.
- [ ] Record verification and complete this plan.

## External verification

After the workflow change reaches GitHub, verify token creation, both private
checkouts, credential cleanup, artifact validation, and Pages deployment.
