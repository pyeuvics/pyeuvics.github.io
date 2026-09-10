# Repository review and remediation

## Scope

Review website assembly, publication boundaries, workflows, current guidance,
and live repository controls. Fix reproducible website-owned defects, then
repeat relevant checks. Preserve source locks and scientific source content.
The owner authorized the organization policy update, `admin:org` access, and
publication of the existing migration commit through a pull request on
2026-09-10. Preserve protected-branch checks throughout the migration.

## Progress

- [x] Inspect implementation, tests, workflows, and repository controls.
- [x] Reproduce and fix local defects with appropriate regression checks.
- [x] Run full tests, strict typing, strict build, and final diff review.
- [x] Record evidence and remaining external dependencies.
- [x] Publish the existing commit through a passing protected-branch PR.
- [x] Complete credential isolation and enable the authorized Actions policy.
- [x] Verify an environment-only production deployment.

## Findings and local fixes

- Scheduled run `34100289230` failed because the EUVICS consumer rejected
  `approval.sha256`. Support schema 1.1 with mandatory digest syntax and exact
  byte verification; retain explicit 1.0 support for the current source lock.
  Validate EUVICS identity, approval metadata, and publication status.
- Reject noncanonical manifest paths and symlinked ancestors, including
  publication manifests, so allowlist checks cannot follow path aliases.
- Verify both source checkouts against the lock before executing source
  validators, and pass the actual locked manifest paths.
- Detect fine-grained GitHub tokens and Windows file paths in artifact scans.
  Preserve ordinary web URLs and harmless bare-drive documentation.
- Preserve inline-link examples in fenced and inline code while continuing
  to reject actual links to unapproved files.
- Restrict privileged manual workflow jobs to `main` and use the `source-read`
  environment, with credential isolation verified below.
- Correct credential-scope and artifact-retention documentation and explain
  the human workflow-approval step for bot-created PRs.

## External dependencies — resolved on 2026-09-10

1. The owner authorized credential migration on 2026-09-10. Created
   `source-read`, configured its sole deployment policy as branch `main`,
   disabled administrator bypass, and installed `EUVICS_DOCS_APP_PRIVATE_KEY`
   from the retained PEM. The PEM authenticated the configured App, and both
   source installations report Contents read-only access. No credential value
   was printed or saved in this repository. After protected-main Pages run
   `34464934351` succeeded, deleted the repository-level secret. A second
   successful Pages run, `34465147467`, verified environment-only access.
   Repository secret metadata reports zero secrets; `source-read` lists the
   App key. The retained PEM and environment copy remain available for recovery.
2. The owner also explicitly authorized enabling PR creation/approval at the
   website repository. GitHub rejected the update with HTTP 409 because the
   organization disallowed it. Reading the organization policy initially
   returned HTTP 403 requiring `admin:org`. The owner then authorized that
   scope and the organization policy change and completed device authorization.
   Enabled `can_approve_pull_request_reviews` at both organization and website
   repository levels; verified both report `true` and retain
   `default_workflow_permissions: read`. The combined GitHub setting permits
   PR creation/approval, but the source-update workflow does not approve or
   merge proposals. No scientific source-update proposal was merged.
3. Published the owner's existing commit `e32f3d4` on
   `fix/source-read-environment-migration` through PR #5. Required check
   `Validate website source` passed in run `34464528935`; the PR merged without
   bypass at `af0a4bb2594acbd220bd59224df27566c50ce16b` on 2026-09-10.
   Post-merge Pages run `34464934351` and environment-only manual run
   `34465147467` both passed and deployed the same merge commit. Required-check
   names and main protection were not changed or weakened. GitHub automatically
   deleted the merged remote feature branch.

## Verification evidence

- Full CI-equivalent validation: 129 tests passed in 68.25 seconds, strict
  typing, standalone strict build, locked-source assembly, final artifact
  scans, and review-artifact hashing all passed. After extending Windows-path
  matching to cover JSON-escaped backslashes, all six focused scan/assembly
  checks passed. The final collected suite contains 130 cases.
- Strict mypy over all `tools` reports success on 13 source files. Dependency
  consistency (`pip check`) and `git diff --check` pass.
- Full validation output is retained in ignored `.staging/review-030-final/`.
- The current EUVICS 1.1 source manifest passes consumer verification with
  two checksum-approved files. No production source locks were changed.
- Complete assembly against both current locks succeeds with 60 inventory
  entries; the generated artifact passes strict build and privacy scans.
- The local environment was synchronized with the existing pinned requirements
  to install missing Markdown type stubs; dependency pins were unchanged.
- Live `main` protection requires `Validate website source` from GitHub
  Actions, strict up-to-date checks, PRs, conversation resolution, linear
  history, and administrator enforcement; force pushes and deletion are off.
- Actions remains restricted to selected actions with SHA pinning required.
- Credential follow-up (2026-09-10): environment secret metadata confirms
  installation; environment policy contains only `{name: main, type: branch}`
  and `can_admins_bypass: false`. Bearer JWT authentication against the App
  endpoint and installation metadata succeeded using the retained key. Both
  live Pages runs successfully consumed the environment credential.
- Post-merge CI ran all 130 tests successfully (23.29 seconds), strict typing,
  locked-source assembly, strict MkDocs build, artifact scans, and deployment.
- Anonymous HTTPS access to the public homepage succeeds and returns canonical
  URL `https://pyeuvics.github.io/`.

The migration is complete. This completion record was published through
[PR #6](https://github.com/pyeuvics/pyeuvics.github.io/pull/6), merged at
`b2f9f5a5e2b0dec729937376034a13a09b54c233`. The required
[`Validate website source` check](https://github.com/pyeuvics/pyeuvics.github.io/actions/runs/34496029712)
passed, and the subsequent
[Pages deployment](https://github.com/pyeuvics/pyeuvics.github.io/actions/runs/34496636017)
succeeded after all 130 tests, strict typing, strict builds, and artifact
validation passed.
