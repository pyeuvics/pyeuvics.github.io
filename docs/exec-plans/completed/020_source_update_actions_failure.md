# Source-update GitHub Actions failure

## Scope

Diagnose and fix the repeated scheduled `Propose source lock update` workflow
failure observed on 2026-08-24 and 2026-08-31.

## Boundaries

- Preserve source-lock validation, publication gates, artifact comparison, and
  review-only pull-request behavior.
- Do not merge a source update, deploy, weaken branch protection, broaden token
  permissions, add credentials, or change publication status.
- Change only the narrowly required repository setting or workflow behavior.

## Progress

- [x] Inspect failing runs and exact failed step.
- [x] Confirm the intended permission model and existing regression coverage.
- [x] Apply the smallest safe fix.
- [x] Run the workflow's full baseline and candidate validation.
- [x] Trigger a fresh workflow and record GitHub evidence.
- [x] Complete this plan after the failure is resolved.

## Initial evidence

- Runs `32688561809` and `33378750208` failed for the scheduled source-lock
  update workflow at website commit `23b3e4c`.
- Run `33378750208` validated both current and candidate artifacts, uploaded the
  proposal package, committed the lock-only change, and pushed branch
  `automation/source-lock-update-33378750208`.
- `gh pr create` then failed with GitHub GraphQL error `createPullRequest`:
  GitHub Actions is not permitted to create or approve pull requests.

## Resolution and verification

- The workflow already declares an empty top-level permission set, read-only
  validation permissions, and only `contents: write` plus
  `pull-requests: write` for the trusted proposal job. Existing tests enforce
  that separation, so no workflow-code change was required.
- With the owner's explicit authorization, the repository-level Actions option
  allowing Actions to create and approve pull requests was enabled. The
  repository default workflow permission remains `read`.
- Fresh manual run `33441656088` at website commit `23b3e4c` completed
  successfully on 2026-09-01 (Asia/Seoul). Both current and candidate locked
  artifacts passed full validation, comparison evidence was uploaded, and the
  trusted proposal job completed every step.
- The formerly failing `Open pull request without merge or deployment` step
  passed and created review-only PR `#1` from
  `automation/source-lock-update-33441656088` into `main`.
- No source lock was merged, no deployment ran, no secret or personal token was
  added, and no default workflow permission was broadened beyond read access.
