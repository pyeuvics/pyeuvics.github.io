# Repository security hardening

## Scope

Resolve findings covering pull-request credential exposure, branch protection,
Actions supply-chain policy, repository homepage metadata, credential
documentation, and post-merge consistency.

## Outcome

- Pull-request validation is secret-free, while trusted default-branch
  deployment obtains repository-scoped, read-only source access through the
  installed GitHub App.
- Every workflow action is pinned to an immutable commit.
- `main` requires pull requests, strict validation, admin enforcement,
  conversation resolution, and linear history; force pushes and deletions are
  disabled.
- The solo-maintainer policy requires zero approvals but retains the automated
  gate.
- GitHub Actions permits GitHub-owned actions only and requires SHA pinning.
- Repository metadata and deployment documentation use
  `https://pyeuvics.github.io/`.
- The renamed required context is `Validate website source`, matching the
  active secret-free pull-request job.

## Verification evidence

- `.venv-docs-313/bin/python -m pytest`: 77 passed locally.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- PR #1 merged as `9e57757c8b6948cc51c94bbc59a5f63bf7b51d70`
  after the prior required check passed.
- Pages run `33715477821` passed complete locked-source validation and
  deployment.
- PR #2 passed **Site validation / Validate website source** in run
  `33745118314` and merged as
  `06477490f0bda0d4098c7e960dcf1b12e46115fc`.
- Branch protection remains strict and now requires
  `Validate website source` from GitHub Actions.
- Pages run `33745388132` passed locked-source build and deployment.
- The public site returned HTTP 200 at `https://pyeuvics.github.io/`.

## Progress

- [x] Make pull-request validation fully secret-free.
- [x] Pin every workflow action to an immutable commit.
- [x] Update workflow tests and credential/deployment documentation.
- [x] Protect `main` with pull requests and structural restrictions.
- [x] Configure the solo-maintainer approval policy.
- [x] Restrict Actions and require SHA pinning.
- [x] Set the repository homepage.
- [x] Publish the required-check rename through a passing pull request.
- [x] Update branch protection to require the renamed check.
- [x] Remove merged review branches through automatic deletion.
