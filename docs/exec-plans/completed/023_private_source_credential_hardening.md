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
- [x] Run local and GitHub validation and protected deployment.
- [x] Exercise the source-update workflow by controlled manual dispatch.
- [x] Record evidence and complete this plan.

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
- Remediation PR `#6` passed site-validation run `33573391303` and merged as
  `e37831e413618ed2d7adf3149f5e69fadcc50716`. Protected Pages run
  `33573515296` passed the residue scan, full artifact validation, and deploy.
- Controlled source-update run `33573646857` passed authenticated candidate and
  locked checkouts, both residue scans, ancestry checks, baseline/candidate
  validation, comparison, evidence transfer, and lock-only PR creation. It
  opened review-only PR `#7`; approved site-validation run `33573833450` also
  passed its residue scan and complete validation. PR `#7` remains unmerged for
  the normal scientific/publication review of its new source commits.
