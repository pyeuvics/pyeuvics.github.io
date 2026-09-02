# Initial information architecture

## Principles

- The website is a public, static documentation index and publication surface;
  it is not an authoritative scientific repository or a running pyEUVICS or
  Jupyter environment.
- Only manifest-allowlisted material from locked source commits may be staged.
- Website summaries identify their source and preserve qualifications,
  assumptions, scientific limitations, and publication state.
- Navigation and authored Markdown use relative internal links so every page
  works from the `/` organization-site base path.
- The canonical default site URL is
  `https://pyeuvics.github.io/`.

## Navigation tree

```text
Home
├── Project
│   ├── Overview
│   └── Design status
├── Documents
│   ├── EUVICS Proposal
│   └── Conceptual Design Report (CDR)
├── pyEUVICS
│   ├── Installation
│   ├── Science and conventions
│   ├── API reference
│   ├── Tutorials
│   ├── Workflows
│   └── Validation
├── Reference campaigns
│   ├── 6.7 nm campaign
│   └── 13.5 nm campaign
├── Downloads
└── About
```

The labels are provisional pending owner review. Selected static notebooks may
appear under Tutorials, Workflows, Validation, or a campaign according to their
primary purpose; this does not imply that computation runs on GitHub Pages.

## Page responsibilities

### Home

Orient readers to EUVICS and pyEUVICS using only approved summaries. Present a
compact status legend, routes to the Project, Documents, pyEUVICS, and campaign
sections, and a visible notice that scientific claims and software behavior are
controlled by the source repositories. Do not present unapproved performance
values, affiliations, contact details, or release claims.

### Project

`Overview` explains scope, terminology, and the relationship between the
project, its documents, pyEUVICS, and reference campaigns. `Design status`
separates objectives and design targets from calculated, simulated, reference,
and validated results. Every material statement points to approved source
evidence and retains assumptions and limitations.

### Documents

The Proposal and CDR each receive an overview/download page rather than an
automatic full-text conversion. When an approved PDF exists, its page shows
title, revision or version, date, controlled publication status, source
repository and commit, SHA-256 checksum, attribution/license information, and
known limitations or review status. With incomplete approval metadata, the PDF
and download control remain absent; the page may state that publication is
pending without implying approval.

### pyEUVICS

- `Installation` links to an approved package installation source and states
  supported prerequisites and version scope when these are source-backed.
- `Science and conventions` explains approved model scope and conventions; it
  must preserve energy definitions, angle definitions, units, statistical and
  beam conventions, approximation regimes, recoil/nonlinear/polarization/
  harmonic/aperture assumptions, and known limitations.
- `API reference` presents or links to generated, version-matched API material.
- `Tutorials` provides reviewed learning paths and selected static notebook
  renderings.
- `Workflows` covers approved use patterns and provenance requirements without
  duplicating the pyEUVICS implementation.
- `Validation` distinguishes evidence, comparisons, discrepancies, and limits;
  known CAIN discrepancies remain visible.

Each page identifies the pyEUVICS version and locked source commit where
applicable. Corrections to models, code, tutorials, or validation conclusions
must be made in `chongshikpark/pyEUVICS` first.

### Reference campaigns

The `6.7 nm campaign` and `13.5 nm campaign` pages are separate, manifest-backed
summaries. Each identifies the campaign/configuration, source commit, pyEUVICS
version, execution or rendering policy, relevant seed when applicable,
scientific status, assumptions, and known limitations. Wavelength in a title is
an identifier, not evidence of achieved performance or validation. Unapproved
data and conclusions remain excluded.

### Downloads

Provide one inventory of approved artifacts. Each entry includes descriptive
link text, artifact type, version/revision, date, status, source and commit,
license/attribution, SHA-256 checksum, and file size. Never expose a directory
listing or make repository presence equivalent to publication approval.

### About

Explain site scope, authoritative sources, publication model, licensing and
attribution boundaries, accessibility route when one is approved, and build
provenance. Affiliations, governance, maintainers, contact channels, logos, and
branding remain omitted until explicitly approved.

## Source, edit, and provenance links

Every materially sourced page provides a consistent metadata block near its
title or footer:

- `Source` links to the authoritative file or artifact at the exact locked
  commit, not a moving branch.
- `Edit in source repository` links to the corresponding authoritative source
  editing location only when public contribution is appropriate. Generated or
  staged website copies never receive edit links.
- `Provenance` identifies repository, full commit, source path, document or
  package version, publication/validation status, and build timestamp. Campaign
  pages also identify configuration/campaign and execution policy. Downloadable
  PDFs and release artifacts include a SHA-256 checksum.
- A website-owned architecture or navigation page may link to its website
  repository source. It must not imply that the website repository owns
  scientific prose or calculations.

Links must have descriptive visible text, remain usable without color, and
resolve under the organization-site root path. Missing provenance is a publication
blocker, not a reason to omit the metadata field silently.

## Ownership matrix

| Material | Authoritative owner | Website responsibility |
| --- | --- | --- |
| Proposal, CDR, requirements, bibliography | `chongshikpark/euvics` | Approved overview, download, metadata, navigation |
| pyEUVICS code, science, API, tutorials, validation | `chongshikpark/pyEUVICS` | Approved staging, static rendering, metadata, navigation |
| Campaign results and limitations | Manifest-declared source in `pyEUVICS` | Approved summary and provenance presentation |
| Navigation, theme, search, assembly, deployment | This repository | Implementation and verification |

## Explicitly deferred decisions

- Final labels/order and whether selected notebooks need a dedicated navigation
  entry.
- Which Proposal, CDR, campaign, and pyEUVICS materials are approved by their
  source publication manifests.
- The authorized approvers and evidence locations for release and validation.
- Branding, logo, affiliations, contact route, custom domain, and any public
  performance values.
