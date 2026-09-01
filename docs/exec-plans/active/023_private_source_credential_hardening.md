# Private-source credential hardening

## Scope

Verify that private-source checkout identities are absent before any
source-derived validation executes, exercise the complete scheduled update path,
and correct private-source documentation and discovery behavior.

## Boundaries

- Keep both authoritative source repositories private.
- Preserve repository-scoped, read-only deploy keys and exact commit locking.
- Do not weaken validation, publish unapproved source content, or merge a new
  source-lock proposal without its normal publication review.

## Progress

- [x] Add fail-closed post-checkout credential scans and ordering regressions.
- [x] Require authenticated checkouts for source discovery.
- [x] Correct deployment and automation documentation.
- [ ] Run local and GitHub validation and protected deployment.
- [ ] Exercise the source-update workflow by controlled manual dispatch.
- [ ] Record evidence and complete this plan.

## Verification evidence

- Official `actions/checkout@v6` source confirms that
  `persist-credentials: false` removes SSH authentication in the checkout
  step's `finally` block. The workflows now additionally scan `RUNNER_TEMP`
  immediately after private checkouts and before source-derived commands.
- Local Python 3.13 verification passed: 19 focused tests, Ruff for affected
  Python files, strict mypy for both affected tools, strict MkDocs, and
  `git diff --check`.
- The full sandboxed suite reported 73 passes and the three expected notebook
  socket failures. All seven notebook execution/failure-path cases passed when
  rerun outside the socket-restricted sandbox.
