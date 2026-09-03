# Repository security hardening

## Scope

Resolve findings covering pull-request credential exposure, branch protection,
Actions supply-chain policy, repository homepage metadata, credential
documentation, and post-merge consistency.

## Progress

- [x] Make pull-request validation fully secret-free.
- [x] Pin every workflow action to an immutable commit.
- [x] Update workflow tests and credential/deployment documentation.
- [x] Protect `main` with pull requests, required validation, admin
      enforcement, conversation resolution, linear history, and force-push and
      deletion restrictions.
- [x] Configure the solo-maintainer policy with zero required approvals and no
      last-push approval requirement while retaining the pull-request gate.
- [x] Restrict Actions to GitHub-owned actions and require SHA pinning.
- [x] Set the repository homepage to `https://pyeuvics.github.io/`.
- [x] Align governance with the secret-free PR and trusted post-merge assembly
      model.
- [ ] Publish the required-check rename to `Validate website source` through a
      pull request and verify that the renamed check passes before updating
      branch protection to require it.
- [x] Remove the merged hardening branch and enable automatic branch deletion.

## Verification evidence

- `.venv-docs-313/bin/python -m pytest`: 77 passed in 36.02 seconds locally.
- `.venv-docs-313/bin/python -m mkdocs build --strict`: passed.
- `git diff --check`: passed.
- PR #1 merged commit `9e57757c8b6948cc51c94bbc59a5f63bf7b51d70`
  after **Site validation / Validate public artifact** passed under the prior
  check name.
- Post-merge Pages run `33715477821` passed complete locked-source validation
  and deployment.
- The public site returned HTTP 200 with canonical URL
  `https://pyeuvics.github.io/`.
- GitHub reports strict required status checks, zero required approvals,
  conversation resolution, linear history, admin enforcement, and disabled
  force pushes and deletions.
- GitHub Actions allows only GitHub-owned actions and requires SHA pinning.
- Repository homepage is `https://pyeuvics.github.io/`.

## Remaining work

The unpublished workflow and documentation changes are retained on local
branch `fix/complete-security-hardening`. Open a pull request from that branch,
confirm **Site validation / Validate website source** succeeds, merge it, and
only then change the required branch-protection context from
`Validate public artifact` to `Validate website source`. Record the pull
request, merge commit, and successful check here before moving this plan back
to `completed/`.

## Intended outcome

Pull requests validate website-owned code without private credentials. Trusted
default-branch workflows perform complete locked-source assembly before Pages
deployment. The solo-maintainer branch policy retains automated and structural
gates without requiring an impossible self-approval.
