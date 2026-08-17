# Project-physics overview release review — completed

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
- [x] Obtain the project owner's explicit approve/reject decision for the exact
      candidate presented in the release report.
- [x] Establish authenticated Git transport for the reviewed push and use the
      public Actions API for exact run inspection.
- [x] After approval, record it, commit the release evidence, follow the normal
      protected `main` workflow, and confirm the exact deployed commit/run.
- [x] Retain the signed-out browser desktop/mobile review as an explicit
      unresolved post-deployment finding at the owner's direction.
- [x] Complete this plan after deployment and available evidence are recorded.

## Current evidence and blockers

- Release matrix: `docs/release-readiness/2026-08-04_project_physics_overview.md`.
- Website candidate at review start: `541cb05`; `origin/main` is `4a0822f`, so
  the reviewed Task 3–5 commits are local and have not been published.
- Source locks: EUVICS `f142bd188892f9518a956989ebaf7a42b6930f33` and
  pyEUVICS `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd`.
- The project owner explicitly approved the presented candidate for deployment
  on 2026-08-04 (Asia/Seoul).
- Approved commit `e12667fbf46a4fc641577b51bd806106ba41f949` was pushed to
  `main`. Protected Pages run `30862675387` completed both validation/package
  and deployment jobs successfully at 2026-08-03T23:35:25Z.
- Signed-out HTTP checks returned 200 for the overview, original SVG, science
  page, Proposal destination, and CDR destination. The live overview contains
  the exact locks and required CAIN, 13.5 nm, calibration, and PDF caveats.
- GitHub CLI's separate token remains invalid, but authenticated Git transport
  and the public Actions API completed the authorized push and exact run review.
- Browser discovery reports no available browser, so the interactive preview
  and signed-out responsive checks cannot currently be executed.
- Browser discovery was retried on 2026-08-17 through the supported browser
  integration and again returned no available browser. The owner directed
  remediation of the stale active-plan state, so this plan is closed without
  representing the interactive review as passed.
