# Information architecture and status language — completed

## Scope

Task 1 from `docs/codex_tasks.md`: define the initial website information
architecture, controlled status vocabulary, and accessibility and content
review checklists without importing or asserting source-repository content.

## Boundaries

- Documentation only; no MkDocs scaffold, source checkout, source content,
  workflow, deployment, branding, or scientific claims.
- The authoritative repositories remain `chongshikpark/euvics` and
  `chongshikpark/pyEUVICS`; publication still requires an allowlist and locked
  source commit.
- Unknown ownership, approvals, affiliations, contact details, and publication
  states remain explicit owner decisions.

## Planned work

- [x] Define the page hierarchy, page responsibilities, and navigation labels.
- [x] Define source, edit, and provenance-link behavior.
- [x] Define the controlled status terms, evidence requirements, and badge use.
- [x] Add accessibility and content/scientific review checklists.
- [x] Check internal consistency, project-site URL use, relative links, and
      source-of-truth boundaries.
- [x] Record verification evidence and move this plan to `completed/`.

## Decisions

- Architecture documents live in `docs/architecture/` and describe the future
  site; they do not create public pages.
- Status labels are metadata claims backed by source evidence, never inferred
  from filenames, location, or visual presentation.

## Completed work

- Added `docs/architecture/information-architecture.md` with the complete
  initial navigation, page responsibilities, ownership boundaries, and
  source/edit/provenance link behavior.
- Added `docs/architecture/status-vocabulary.md` with all eleven required
  controlled terms, their dimensions and minimum evidence, badge rules, and
  explicit safeguards against conflating release, validation, and claim type.
- Added `docs/architecture/review-checklists.md` for headings, alternative text,
  link text, contrast, keyboard use, equations, tables, responsive and print
  layout, citations, attribution, provenance, and scientific limitations.
- Added `docs/architecture/README.md` as the architecture-document index and a
  concise statement of source authority and unresolved decisions.

## Verification evidence

- `git diff --check` passed.
- All relative Markdown links in the four architecture documents resolve.
- A terminology scan confirmed all required controlled status labels are
  defined.
- URL and base-path scans confirmed the architecture uses
  `https://chongshikpark.github.io/euvics.github.io/` and
  `/euvics.github.io/`; it makes no root-domain hosting claim.
- Source-boundary review confirmed that scientific/document corrections remain
  assigned to `chongshikpark/euvics` or `chongshikpark/pyEUVICS`, and that
  publication requires an allowlist and locked commit.
- A personal absolute-path scan found none in the Task 1 files.
- Manual claim review found no invented branding, affiliations, contacts,
  performance values, document approval, or validation assignment.

## Unresolved owner decisions

- Approve final navigation labels/order and decide whether selected static
  notebooks need their own navigation entry.
- Identify authorized approvers and evidence locations for release and
  validation states.
- Approve any source items through their source publication manifests before
  import.
- Decide branding, logo, affiliations, contact route, custom domain, and public
  performance claims separately; none was added by this task.
