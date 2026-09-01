# Source-update review remediation

## Scope

Resolve the repository review findings for automated source-lock PR `#1`:

- approve and verify its blocked non-deploying site validation;
- review and remove only confirmed obsolete automation branches;
- make failed PR creation clean up its newly pushed branch and add regression
  coverage;
- complete the required source/publication review for the proposed exact locks.

## Boundaries

- Do not merge PR `#1`, change source publication manifests, alter scientific
  source content, deploy, broaden credentials, or weaken validation.
- Preserve the active proposal branch for PR `#1`.
- Delete a remote branch only after confirming that it has no open PR and is
  superseded by the active proposal.

## Progress

- [x] Approve and monitor PR `#1` site validation; diagnose the resulting
      mutable-lock test failure.
- [x] Review the four obsolete automation branches and remove confirmed stale
      branches.
- [x] Implement failure cleanup and branch-aware duplicate protection.
- [x] Add targeted regression coverage and update automation documentation.
- [x] Run targeted and full local checks.
- [x] Review source commit ranges, manifests, campaign status, checksums,
      limitations, permissions, and representative artifact changes.
- [x] Publish the workflow fix for review without merging or deploying.
- [ ] Record evidence and complete this plan.

## Verification evidence

- Approved run `33441868806`; it started normally but exposed a website test
  that duplicated the old EUVICS lock hash. The exact-pin assertion was removed
  because schema, lock state, ancestry, and source-contract checks already
  enforce the mutable lock. A regression test now rejects current lock hashes
  duplicated anywhere in website tests.
- Confirmed four older unprotected branches had no PR and contained only
  superseded lock proposals. Deleted branches for runs `31356799127`,
  `31992912934`, `32688561809`, and `33378750208`; preserved active PR `#1`
  branch `automation/source-lock-update-33441656088`.
- Duplicate gating now checks both open automation PRs and matching remote
  branches. If PR creation fails after a successful push, a failure-only step
  deletes that run's proposal branch; cleanup failure remains visible.
- Candidate review: both publication manifests, the three EUVICS allowlisted
  scientific files, the approved pyEUVICS overview artifacts, `LICENSE`, and
  `CITATION.cff` are byte-unchanged. Both campaign checksum inventories pass.
  Campaign publication remains blocked with approvals false; 6.7 nm retains
  the known CAIN disagreement and 13.5 nm remains provisional with no
  independent validation. Campaign numeric result payloads are unchanged
  except frozen Python/NumPy environment and corresponding provenance hashes.
- Baseline and candidate assemblies each produced 59 approved files. Review of
  the project overview, equations page, pyEUVICS landing page, and inventory
  confirms changes are updated immutable provenance links/hashes plus the
  approved pyEUVICS README constraint guidance; no campaign is admitted.
- Verification passes: 21 targeted tests, 73 full Python 3.13 tests, strict
  mypy for 12 files, `mkdocs build --strict`, and `git diff --check`.
- Review follow-up found repository setting `delete_branch_on_merge` is false.
  Duplicate gating was narrowed so only open automation PRs and branches with
  no PR association block new proposals; retained branches from merged or
  closed PRs no longer deadlock the schedule.
- Workflow lifecycle fix published as PR `#2`; its first complete site
  validation passed before the follow-up gate refinement.
