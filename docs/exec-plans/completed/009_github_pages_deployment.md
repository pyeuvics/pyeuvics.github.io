# GitHub Pages deployment — active

## Scope

Implement Task 9 from `docs/codex_tasks.md`: add a production workflow that
rebuilds and validates the locked public artifact, uploads that exact site as a
GitHub Pages artifact, and deploys it only for `main` pushes or explicit manual
dispatches through the protected `github-pages` environment.

## Boundaries

- Do not enable or configure Pages remotely, add secrets, modify environment or
  branch protection, dispatch the workflow, deploy, push, or create `gh-pages`.
- Keep pull-request validation read-only and non-deploying.
- Use public locked-source checkouts and no credential persistence.
- Grant Pages and OIDC write permissions only to the deployment job.
- Do not alter source contracts, scientific content, approval metadata, or
  source locks.

## Planned work

- [x] Add the official configure/upload/deploy Pages action sequence.
- [x] Restrict triggers, permissions, concurrency, and environment correctly.
- [x] Reuse the complete local-equivalent validation entry point.
- [x] Prove that the deployed directory is the validated assembled site.
- [x] Add a manual administrator, first-release, and rollback checklist.
- [x] Add workflow structure and safety regression tests.
- [x] Run repository tests, strict typing, strict MkDocs, and YAML checks.
- [x] Record evidence and move this plan to completed.

## Verification evidence

- Official GitHub guidance checked on 2026-08-02 confirms
  `actions/configure-pages@v5`, `actions/upload-pages-artifact@v4`, and
  `actions/deploy-pages@v4`, with `pages: write`, `id-token: write`, a dependent
  deployment job, and the `github-pages` environment.
- Workflow tests parse both Actions YAML files and verify main/manual-only
  production triggers, locked refs, non-persisted checkout credentials, scoped
  permissions, deployment concurrency, official Pages actions, exact validated
  upload path, protected environment, and absence of secrets or `gh-pages`.
- Repository tests: 46 non-notebook tests passed; all seven localhost-kernel
  notebook tests passed separately, accounting for all 53 tests.
- Strict mypy validation passed for all nine CI-configured source files.
- `mkdocs build --strict` passed in 0.60 seconds.
- `git diff --check` passed.
- No workflow was dispatched, no artifact uploaded, no deployment performed,
  and no remote setting, secret, environment, or branch protection changed.
- Remaining external work is explicitly documented in
  `docs/pages-deployment.md`: Pages source selection, `github-pages` and `main`
  protections, first-artifact inspection/approval, signed-out verification,
  and authorized rollback handling.
