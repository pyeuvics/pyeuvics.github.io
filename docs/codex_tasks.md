# Codex Tasks for `pyeuvics/pyeuvics.github.io`

> Historical task catalog: these prompts retain their original implementation
> scope, but repository identities and site-base instructions were updated on
> 2026-09-02 for the organization-site migration. They are not current
> deployment instructions; see the
> [organization-site migration record](organization-site-migration.md).

Run these tasks sequentially. Each task is intentionally bounded and includes its own verification requirements. Do not combine deployment, credentials, repository settings, or scientific publication with unrelated implementation work.

## Task 0 — Correct and baseline the website repository

```text
Work in the local clone of https://github.com/pyeuvics/pyeuvics.github.io.

Inspect the complete repository and preserve the current clean working tree. Add the reviewed root AGENTS.md and README.md supplied for this website. Create docs/exec-plans/active/ and docs/exec-plans/completed/, then create an active execution plan for repository foundation.

Make only these mechanical corrections:
- rename LINCESNE to LICENSE without changing the existing MIT text;
- replace or archive planning documents that incorrectly refer to pyEUVICS/pyEUVICS.github.io or https://pyEUVICS.github.io/;
- install the updated website Codex task file at docs/codex_tasks.md;
- review .gitignore for duplicate entries and ensure that a generic downloads/ rule will not hide intended content/downloads/ website source;
- document the actual default Pages URL as https://pyeuvics.github.io/;
- ensure temporary source checkouts, staging, rendered intermediates, secrets, and site output remain ignored.

Do not add scientific content, create a remote resource, change repository visibility, configure Pages, add credentials, push, or deploy.

Verify:
- git diff shows only intended foundation changes;
- LICENSE contains the unchanged reviewed text;
- no remaining active instructions claim that this repository produces https://euvics.github.io/ or https://pyEUVICS.github.io/;
- all README and task-file links resolve;
- no personal absolute paths appear.

Record verification evidence and move the execution plan to completed only when these checks pass.
```

## Task 1 — Define the website information architecture and status language

```text
Work in pyeuvics/pyeuvics.github.io after Task 0 is complete. Read AGENTS.md and the completed foundation plan. Create a new active execution plan.

Define the website's initial information architecture under docs/architecture/ without importing source-repository content yet. Specify:
- Home;
- Project overview and design status;
- Proposal and CDR overview/download pages;
- pyEUVICS installation, science, API, tutorials, workflows, and validation sections;
- 6.7 nm and 13.5 nm campaign pages;
- Downloads and About pages;
- source/edit/provenance links.

Create a controlled status vocabulary for Draft, Approval Pending, Design Target, Calculated, Simulated, Reference, Validated, Unvalidated, Superseded, and Released. Define where status badges may be used and what evidence each status requires.

Create accessibility and content checklists covering headings, alternative text, link text, contrast, keyboard navigation, equations, tables, mobile layout, print/PDF behavior, citations, attribution, and scientific limitations.

Do not invent branding, a logo, affiliations, contact information, performance values, document approval, or validation status. Mark unresolved owner decisions explicitly.

Verify all architecture documents are internally consistent with the organization-site URL and authoritative source boundaries. Do not deploy.
```

## Task 2 — Add the EUVICS source publication contract

```text
Work in https://github.com/chongshikpark/euvics, not the website repository. Read that repository's AGENTS.md and preserve its working tree. Create an active execution plan following its rules.

Design and implement a versioned public-content manifest consumed by pyeuvics/pyeuvics.github.io. Treat every file as excluded unless explicitly allowlisted.

Initially allowlist only reviewed material needed for:
- the project overview;
- Proposal overview and an explicitly approved PDF;
- CDR overview and an explicitly approved PDF;
- approved requirements/reference cases;
- bibliography, citation, license, permission, and document-status metadata.

Exclude internal reviews, comment registers, open decisions, confidential costs, unapproved requirements, historical archive PDFs, auxiliary LaTeX output, raw data, local paths, and restricted figures unless an approved manifest entry says otherwise.

Add schema validation and tests that reject path traversal, missing files, unknown fields, broad accidental globs, ambiguous publication status, and excluded-file leakage. Extend the existing verified build to produce machine-readable publication metadata and SHA-256 checksums for approved PDFs.

Run make check and all new tests. Do not deploy, push, change visibility, or add credentials. Record the completed plan only after the contract is verified.
```

## Task 3 — Add the pyEUVICS source publication contract

```text
Work in https://github.com/pyeuvics/pyEUVICS, not the website repository. Read AGENTS.md and preserve committed and untracked user work. Create an active execution plan using the repository's naming rules.

Design and implement a versioned public-content manifest consumed by pyeuvics/pyeuvics.github.io. Start with reviewed documentation from docs/, selected reference-campaign summaries and figures, and a bounded notebook set.

Candidate initial content:
- docs/index.md;
- docs/getting-started/;
- docs/science/;
- docs/api/;
- docs/tutorials/;
- docs/instrumentation/;
- docs/workflows/;
- docs/validation/;
- selected 6.7 nm and 13.5 nm campaign reports;
- selected notebooks for environment, kinematics, nonlinear ICS, scans, digital twin, CAIN comparison, and reference campaigns.

Exclude execution plans, legacy scripts, raw or synthetic test data, local release records, caches, build artifacts, private campaign data, and unreviewed notebooks unless individually approved.

Add checks for schema validity, missing assets, local absolute paths, internal links, unapproved file types, notebook size/output policy, source-notebook immutability, and visible validation limitations. Produce publication metadata with package version, source commit placeholder, documentation status, license, and known scientific limitations.

Run the repository-required pytest, Ruff, mypy, documentation, and notebook checks. Do not deploy, push, change visibility, or add credentials.
```

## Task 4 — Scaffold the local MkDocs website

```text
Work in pyeuvics/pyeuvics.github.io after Tasks 0 and 1 are complete. Read AGENTS.md and create an active execution plan.

Create a local, non-deploying site foundation:
- mkdocs.yml using Material for MkDocs;
- requirements-docs.txt with reviewed pinned constraints;
- sources.lock.yml with source repository URLs and placeholder/approved commit fields;
- content/ sections matching the approved information architecture;
- MathJax configuration;
- minimal accessible styling;
- tools/ and tests/ foundations;
- documented local commands.

Set `site_url` exactly to `https://pyeuvics.github.io/` and verify all
generated links work from the organization-site root path.

Use placeholders for unapproved content. Do not checkout source repositories, copy their documentation, render notebooks, build PDFs, add workflows, or deploy during this task.

Verify:
- mkdocs build --strict succeeds;
- navigation, search, equations, status labels, and 404 behavior work locally;
- there are no local absolute paths;
- site output is ignored;
- desktop/mobile layout and keyboard focus receive a basic review.

Report the exact dependency versions and warnings.
```

## Task 5 — Implement deterministic source assembly

```text
Work in pyeuvics/pyeuvics.github.io after both source publication contracts and the local site foundation are reviewed. Read AGENTS.md and create an active execution plan.

Implement a deterministic assembly command that accepts local paths to checked-out euvics and pyEUVICS repositories and verifies their exact commits against sources.lock.yml.

It must:
1. validate both source publication manifests;
2. reject commit mismatches;
3. copy only allowlisted files into a temporary staging tree;
4. preserve source checkouts unchanged;
5. rewrite repository-relative links only in staging;
6. generate source/provenance/edit links;
7. generate a complete staged-content inventory;
8. reject unknown files, missing approvals, path traversal, broken links, local paths, and unexpected file types;
9. build MkDocs in strict mode;
10. scan the final artifact for excluded content and credential-like material.

Keep substantial logic in typed, tested Python modules rather than a long shell script. Use synthetic fixture repositories in tests; do not copy private source material into fixtures.

This task imports Markdown and ordinary assets only. Defer LaTeX/PDF builds and notebook rendering to separate tasks. Run unit, integration, strict-build, and source-immutability tests. Do not add credentials or deploy.
```

## Task 6 — Integrate Proposal and CDR publication

```text
Work in pyeuvics/pyeuvics.github.io after deterministic source assembly is complete. Read AGENTS.md and create an active execution plan.

Extend the assembly pipeline to build approved EUVICS documents through the source repository's documented Makefile. Do not auto-convert the complete LaTeX sources to Markdown.

Required flow:
- verify the euvics source commit and publication manifest;
- run archive verification and make check;
- reject unresolved citations, references, missing figures, and build failures;
- stage only approved newly built Proposal/CDR PDFs;
- calculate and verify SHA-256 checksums;
- generate web overview/download pages showing title, revision, date, publication status, source commit, checksum, and known limitations;
- ensure historical or internal PDFs cannot enter the artifact accidentally.

Add failure-path tests using small synthetic document fixtures where practical. Verify PDF links and checksums in the completed MkDocs artifact. Do not alter the source repository, deploy, or declare documents approved without explicit metadata.
```

## Task 7 — Integrate pyEUVICS notebooks and campaigns

```text
Work in pyeuvics/pyeuvics.github.io after deterministic source assembly is complete. Read AGENTS.md and create an active execution plan.

Extend the assembly pipeline to render only allowlisted pyEUVICS notebooks into static website pages. Use a temporary staging directory and prove that source notebooks remain byte-for-byte unchanged.

Start with the manifest-approved subset for environment, linear kinematics, nonlinear ICS, parameter scans, end-to-end digital twin, CAIN comparison, and 6.7 nm/13.5 nm reference campaigns.

Each rendered page must identify:
- pyEUVICS version and source commit;
- notebook source path;
- whether execution occurred during the build or trusted outputs were rendered;
- relevant random seed/configuration;
- scientific validation status and known limitations;
- expected local execution requirements.

Do not describe the static pages as a running Jupyter environment. Reject notebooks with unapproved data dependencies, oversized outputs, local paths, secrets, failed cells, or missing provenance.

Run source-immutability, deterministic-render, link, asset, size, and strict-site-build tests. Do not deploy.
```

## Task 8 — Add GitHub Actions validation

```text
Work in pyeuvics/pyeuvics.github.io after the complete local site build is reviewed. Read AGENTS.md and create an active execution plan.

Add a pull-request validation workflow that:
- checks out the website repository;
- checks out source repositories at commits in sources.lock.yml;
- uses public access when possible and one documented read-only secret only if required;
- validates publication manifests;
- builds approved PDFs and rendered notebooks;
- assembles and scans the complete artifact;
- runs pytest and mkdocs build --strict;
- uploads a review artifact but never deploys from a pull request.

Pin or constrain toolchain versions consistently with repository policy. Cache only safe dependencies with lock-file-derived keys. Do not print credentials or persist checkout credentials unnecessarily.

Validate workflow syntax and demonstrate local/CI build equivalence. Do not enable Pages, add real secrets, or deploy during this task.
```

## Task 9 — Add GitHub Pages deployment

```text
Work in pyeuvics/pyeuvics.github.io only after Task 8 passes and the full public artifact is approved. Read AGENTS.md and create an active execution plan.

Add a deployment job for approved default-branch pushes and explicit manual dispatch. Use the official GitHub Pages configure, artifact-upload, and deployment actions, the protected github-pages environment, deployment concurrency, and least-privilege permissions.

The deployed artifact must be exactly the artifact that passed validation. Do not create a bot-written gh-pages branch or commit generated site output.

Add a manual administrator checklist for:
- source repository visibility and optional read credential;
- Settings → Pages → Source → GitHub Actions;
- github-pages environment protection;
- default branch restrictions;
- first-artifact inspection;
- signed-out verification at https://pyeuvics.github.io/;
- rollback to the preceding approved deployment.

Do not change GitHub settings, add secrets, enable Pages, or trigger the first public deployment without explicit authorization. Validate workflow configuration and document the exact external actions remaining.
```

## Task 10 — Public release and accessibility review

```text
Review the complete proposed website artifact and, after explicitly authorized deployment, the live signed-out site at https://pyeuvics.github.io/.

Check:
- all routes use the correct organization-site root path;
- navigation and search cover project, documents, software, campaigns, downloads, and about;
- Proposal/CDR PDF versions, statuses, source commits, and checksums;
- pyEUVICS equations, tables, code, assets, notebooks, and campaign pages;
- visible 6.7 nm and 13.5 nm validation limitations;
- authoritative source/edit links;
- citations, licenses, figure permissions, and attribution;
- absence of internal reviews, confidential costs, raw private data, credentials, local paths, and excluded files;
- mobile/desktop layout, keyboard navigation, focus, contrast, headings, alternative text, print behavior, PDF opening, and 404 handling;
- public access from a signed-out browser.

Create a severity-ranked release-readiness report with exact URLs/source paths, evidence, owners, and retest results. Do not close findings without verification. Do not change repository visibility, Pages settings, credentials, ownership, custom domains, or publication status without explicit approval.
```

## Task 11 — Automated source-update pull requests

```text
After several successful manually locked releases, design automation that detects newer approved source commits and opens a pull request updating sources.lock.yml.

The automation must not deploy directly from source-repository pushes, bypass publication manifests, merge its own changes, or follow an unreviewed branch tip in production. Document credential scope, provenance, artifact comparison, rollback, failure modes, and reviewer workflow before implementation.
```


## Task 12 - PDF renders

Both PDFs rendered successfully, but neither is production-release ready.

The Proposal at `build/proposal/main.pdf` in the EUVICS source repository has
visible red and green hyperlink borders throughout. It also contains extensive
TBD material and an almost-empty final page.

The CDR at `build/cdr/main.pdf` in the EUVICS source repository has the same
hyperlink-border issue. Pages 3–4 contain essentially headings without
technical content, and the page-2 layout figure still has unresolved
distribution permission.

Both PDFs remain excluded from website assembly until the CDR permission issue and required release metadata—version, date, license, attribution, limitations, approver, and approval date—are recorded in the EUVICS publication manifest.
