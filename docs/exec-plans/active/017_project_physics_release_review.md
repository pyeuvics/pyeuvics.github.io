# Project-physics overview release review — active

## Scope

Review the Task 3–5 project-physics overview release candidate, present the
required approval package, and deploy only after a separate explicit owner
approval.

## Boundaries

- Do not rewrite scientific results or bypass source publication contracts.
- Do not push, merge, dispatch, or deploy before explicit approval of the
  presented release candidate.
- Use the protected default-branch Pages workflow; never force-push or publish
  generated output through a branch.
- Keep Proposal/CDR PDFs and other unapproved material excluded.

## Plan

- [x] Compare scientific content and equations with both locked source commits.
- [x] Review publication, security, provenance, editorial, and accessibility
      evidence available from the assembled artifact.
- [x] Verify citations, source-commit links, live pre-release URL, current
      origin state, and deployment workflow without mutation.
- [x] Prepare the review matrix, caveats, source table, preview paths, and build
      report.
- [ ] Obtain the project owner's explicit approve/reject decision for the exact
      candidate presented in the release report.
- [ ] Restore GitHub CLI authentication needed for the reviewed push and run
      inspection.
- [ ] After approval, record it, commit the release evidence, follow the normal
      protected `main` workflow, and confirm the exact deployed commit/run.
- [ ] Complete signed-out canonical URL and browser desktop/mobile review, or
      retain an explicit unresolved post-deployment finding if the owner directs
      completion without browser evidence.
- [ ] Complete this plan only after deployment and required evidence are
      recorded.

## Current evidence and blockers

- Release matrix: `docs/release-readiness/2026-08-04_project_physics_overview.md`.
- Website candidate at review start: `541cb05`; `origin/main` is `4a0822f`, so
  the reviewed Task 3–5 commits are local and have not been published.
- Source locks: EUVICS `f142bd188892f9518a956989ebaf7a42b6930f33` and
  pyEUVICS `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`.
- Owner approval is pending by Task 6 policy.
- GitHub CLI reports that the active `chongshikpark` credential is invalid.
- Browser discovery reports no available browser, so the interactive preview
  and signed-out responsive checks cannot currently be executed.
