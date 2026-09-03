# Repository security hardening

## Scope

Resolve the review findings covering pull-request credential exposure, branch
protection, Actions supply-chain policy, repository homepage metadata, and
credential documentation.

No commit or push is authorized. Local changes remain uncommitted.

## Work

- [x] Make pull-request validation fully secret-free.
- [x] Pin every workflow action to an immutable commit.
- [x] Update workflow tests and credential/deployment documentation.
- [x] Protect `main` with pull requests, required validation, admin
      enforcement, and force-push/deletion restrictions.
- [x] Restrict Actions and require SHA pinning.
- [x] Set the repository homepage to `https://pyeuvics.github.io/`.
- [x] Run full tests, strict MkDocs build, and diff checks.
- [ ] Record evidence; keep this plan active until local changes are committed
      and pushed under separate authorization.

## Verification evidence

- `.venv-docs-313/bin/python -m pytest`: 77 passed in 36.90 seconds.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- `site-check.yml` contains no secret, variable, App-token, or private-source
  checkout reference.
- Every workflow `uses:` reference is pinned to a 40-character commit.
- GitHub reports strict required status checks, one required approving review,
  stale-review dismissal, last-push approval, conversation resolution, linear
  history, admin enforcement, and disabled force pushes and deletions.
- GitHub Actions allows only GitHub-owned actions and requires SHA pinning.
- Repository homepage is `https://pyeuvics.github.io/`.

## Remaining handoff

The workflow hardening is intentionally uncommitted and unpushed per user
instruction. Live workflow verification and plan completion require a later
authorized commit and push through the newly protected branch process.
