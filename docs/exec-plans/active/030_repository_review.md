# Repository review and remediation

## Scope

Review website assembly, publication boundaries, workflows, current guidance,
and live repository controls. Fix reproducible website-owned defects, then
repeat relevant checks. Preserve source locks and scientific source content.
No commit or push is authorized.

## Progress

- [x] Inspect implementation, tests, workflows, and repository controls.
- [x] Reproduce and fix local defects with appropriate regression checks.
- [x] Run full tests, strict typing, strict build, and final diff review.
- [x] Record evidence and remaining external dependencies.

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
- Restrict privileged manual workflow jobs to `main` and prepare them to use
  the `source-read` environment. This is not sufficient until the external
  credential migration below is complete.
- Correct credential-scope and artifact-retention documentation and explain
  the human workflow-approval step for bot-created PRs.

## External dependencies — still open

1. The App key is currently a repository Actions secret. A same-repository PR
   can edit its workflow to request it. Owner authorization and the retained
   PEM file (or owner-installed environment secret) are needed to configure
   `source-read` with an exact `main` branch rule, install the environment
   secret, and eventually remove the repository copy after verification.
   GitHub cannot return the existing secret value. Environment or credential
   settings were not changed during this review.
2. Live `can_approve_pull_request_reviews` is false, blocking the proposal
   workflow's PR creation. GitHub combines PR creation and approval capability
   in this setting. Automatic approval review rejected enabling it because
   the approval capability requires explicit user authorization. The default
   token remains read-only; the setting was left unchanged.
3. No commit or push is authorized. Workflow changes and the failed scheduled
   run cannot be verified live until a separately authorized PR is merged.
   Do not update required-check names or weaken main protection for this work.

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

Keep this plan active until the external dependencies are resolved and the
reviewed changes pass a live protected-branch workflow.
