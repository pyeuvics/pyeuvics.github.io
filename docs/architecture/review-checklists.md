# Accessibility and content review checklists

Use these gates for authored, staged, and generated pages. A checked item means
the rendered artifact—not only its Markdown source—was reviewed. Record any
not-applicable item and rationale in the relevant execution or publication
record.

## Accessibility and presentation

### Structure and navigation

- [ ] The page has one descriptive level-one heading and a logical, unskipped
      heading hierarchy.
- [ ] Landmarks and semantic elements identify navigation and main content.
- [ ] Navigation order and breadcrumbs match the approved information
      architecture and work from the `/` organization-site base path.
- [ ] All controls and links are reachable and operable by keyboard with a
      visible focus indicator; focus order follows reading order.
- [ ] Skip navigation and menus work with keyboard and screen-reader use.
- [ ] Link text describes its destination or action without relying on nearby
      prose; avoid ambiguous text such as “click here” or repeated “read more.”

### Images, color, and media

- [ ] Informative images, plots, diagrams, and equations rendered as images have
      concise meaningful alternative text; complex visuals also have an
      adjacent data table or long description.
- [ ] Decorative images use empty alternative text and add no scientific claim.
- [ ] Captions identify source, permissions/attribution, status, units,
      conventions, and limitations where applicable.
- [ ] Text, controls, focus indicators, plots, and status labels have readable
      contrast; color is never the sole carrier of meaning.
- [ ] Status labels retain visible text and meaning in grayscale/high-contrast
      rendering.

### Equations, tables, and code

- [ ] Equations render with accessible MathJax semantics or an equivalent
      approved representation and remain readable when zoomed.
- [ ] Every symbol is defined, units and assumptions are stated, and equation
      numbering/references resolve.
- [ ] Tables use a caption and programmatic row/column headers; complex header
      relationships and abbreviations are explained.
- [ ] Tables reflow, scroll, or receive an equivalent small-screen
      representation without losing headers or values.
- [ ] Code blocks identify language where useful, support keyboard selection,
      do not rely on color alone, and wrap or scroll without covering content.

### Responsive and alternate output

- [ ] Navigation, headings, badges, tables, equations, code, figures, and
      downloads are usable at representative desktop and mobile widths and at
      200% zoom without two-dimensional page scrolling (except intrinsically
      wide content such as tables).
- [ ] No control requires hover or pointer precision alone.
- [ ] Print and PDF output preserves headings, URLs or useful link context,
      figure/table captions, status text, provenance, limitations, and page
      breaks; content is not clipped or hidden by navigation.
- [ ] Linked PDFs receive an accessibility review appropriate to their approved
      source format; unresolved PDF accessibility limitations are disclosed.

## Content, provenance, and scientific integrity

### Publication authority and privacy

- [ ] Every imported file is explicitly allowlisted by a versioned source
      publication manifest and comes from the exact locked commit.
- [ ] Publication status and owner approval are recorded; ambiguity causes
      exclusion and an owner decision, not publication by default.
- [ ] Confidential material, credentials, internal URLs, personal data,
      machine names, absolute local paths, restricted figures, and unapproved
      raw data are absent.
- [ ] Copyright, license, figure permission, and required attribution are
      verified for text, code, data, images, PDFs, and downloads.
- [ ] Website summaries do not become a second authoritative copy and provide a
      route to correct material in its source repository.

### Provenance, links, and citations

- [ ] Material outputs state source repository, full commit, source path,
      document/package version, controlled status, and build timestamp.
- [ ] Campaign/notebook outputs state configuration or campaign, execution
      policy, source notebook, seed where relevant, and validation scope.
- [ ] PDFs and release artifacts show and verify SHA-256 checksum, version/date,
      license/attribution, and known review limitations.
- [ ] Source links target the locked commit; edit links target the authoritative
      repository rather than staged/generated copies.
- [ ] Internal links are relative and pass a base-path check; external links and
      descriptive text are reviewed, including citations and references.
- [ ] Citations support the adjacent claim, resolve to an approved source, and
      preserve required bibliographic attribution; unresolved citations or
      references block publication.

### Scientific statements

- [ ] Claims use only the controlled status vocabulary and link to the evidence
      required by [status-vocabulary.md](status-vocabulary.md).
- [ ] Design targets are not presented as achieved, and calculated, simulated,
      reference, released, and validated states remain distinct.
- [ ] Electron energy is explicitly kinetic or total energy.
- [ ] Collision angle is defined between electron and laser propagation
      vectors, with `0°` co-propagating and `180°` head-on.
- [ ] Observation angle is defined relative to the electron propagation
      direction.
- [ ] Values state units and applicable RMS/FWHM, waist, peak/average, and
      bandwidth conventions.
- [ ] Linear/exact, recoil, nonlinear, polarization, harmonic, aperture, and
      spectral-statistic assumptions are explicit where applicable.
- [ ] “Extreme ultraviolet (EUV)” terminology is used consistently.
- [ ] Known discrepancies—including applicable CAIN discrepancies—validation
      scope, uncertainty, and other limitations remain visible near the claim.
- [ ] Summaries do not remove a qualification, expand a validation domain, or
      convert a source result into a stronger conclusion.

### Static software and notebook content

- [ ] pyEUVICS remains the sole implementation of calculations; the website
      contains no independent equation/calculation implementation.
- [ ] API and installation guidance matches the named pyEUVICS version and
      locked commit.
- [ ] Static notebooks are labeled as static, identify whether they were
      executed or rendered from trusted output, and do not imply server-side
      Python or Jupyter availability.
- [ ] Source notebooks remain byte-for-byte unchanged and unapproved data
      dependencies, failed cells, oversized output, secrets, and local paths
      are absent.

## Release review record

- [ ] Desktop, mobile, keyboard-only, print/PDF, and signed-out checks are
      recorded with date, reviewer, build identifier, and affected pages.
- [ ] Automated link, artifact inventory, secret/local-path, source-lock,
      checksum, and strict-build results are attached or referenced.
- [ ] Remaining accessibility, publication, and scientific decisions name an
      owner and keep affected content excluded until resolved.
