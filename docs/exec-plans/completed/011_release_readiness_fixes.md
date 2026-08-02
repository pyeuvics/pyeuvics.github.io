# Release-readiness fixes — active

## Scope

Resolve the website-owned Task 10 findings R10-002 and R10-003, reassemble and
reaudit the locked artifact, and update finding status only when supported by
new evidence. Recheck external blockers without bypassing publication,
deployment, or accessibility approval gates.

## Boundaries

- Do not invent or approve EUVICS PDFs, pyEUVICS notebooks/campaigns, scientific
  claims, validation conclusions, licenses, permissions, or attribution.
- Do not deploy, dispatch workflows, enable Pages, change remote settings or
  protection, add credentials, or claim live browser checks were performed.
- Keep imported scientific prose authoritative in its source repository.
- Never require hand edits to staged/generated copies.

## Planned work

- [x] Make website source pages neutral about assembly state.
- [x] Generate accurate build-specific entry pages and navigation links from
      the validated pyEUVICS publication contract.
- [x] Suppress website edit actions on imported pages while retaining correct
      authoritative source/edit provenance.
- [x] Add regression tests for accurate entry content, navigability, edit
      targets, source locking, and source immutability.
- [x] Reassemble and audit the exact locked artifact.
- [x] Update the Task 10 report with closed/open evidence and remaining owners.
- [x] Run all tests, strict typing, strict MkDocs, and diff checks.
- [x] Complete this plan only after the website-owned findings are verified.

## Verification evidence

- Static website pages now describe local-preview versus assembled-build state
  without claiming approved source content is absent.
- Assembly generates each website-owned pyEUVICS entry page from the validated
  source contract, including exact commit, version, publication status, build
  timestamp, known limitations, and links only to approved Markdown.
- Real locked-source retest assembled 53 pyEUVICS items. Home links to the
  package index; installation, science, API, tutorials, workflows, and
  validation expose 5, 8, 4, 8, 13, and 9 approved links respectively.
- The actions template suppresses the website-repository edit control only for
  imported pages. All 51 imported Markdown pages retain the authoritative
  pyEUVICS edit link at the locked commit; zero points at
  `edit/main/content/imported/`. Website-owned edit controls remain present.
- Regression coverage proves accurate build navigation, metadata, source/edit
  boundaries, deterministic assembly, and source immutability.
- R10-002 and R10-003 are marked resolved with evidence in the Task 10 report.
  R10-001 (deployment), R10-004 (live browser accessibility), and R10-005
  (authoritative publication approvals) remain open and were not bypassed.
- Verification passed: 46 non-notebook tests and seven localhost-kernel tests
  (53 total), strict mypy for all nine CI-configured source files,
  `mkdocs build --strict`, production locked-source assembly, and
  `git diff --check`.
- No source repository content, source lock, publication status, credential,
  remote setting, protection rule, workflow run, or deployment was changed.
