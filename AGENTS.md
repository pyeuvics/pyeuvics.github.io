# AGENTS.md — EUVICS Website Repository

## 1. Mission

Develop and maintain the public EUVICS documentation website from:

```text
Repository: https://github.com/pyeuvics/pyeuvics.github.io
Default GitHub Pages URL: https://pyeuvics.github.io/
```

The website presents approved public material from two authoritative source repositories:

- `https://github.com/pyeuvics/euvics` — EUVICS Proposal, Conceptual Design Report (CDR), requirements, bibliography, and document releases.
- `https://github.com/pyeuvics/pyEUVICS` — pyEUVICS package documentation, tutorials, notebooks, validation reports, and reference campaigns.

This repository owns website navigation, branding, staging, link transformation, search, and deployment. It is not the authoritative location for scientific models, document prose, validation conclusions, or source data.

## 2. GitHub Pages naming convention

Because the repository owner is `pyeuvics` and the repository name is
`pyeuvics.github.io`, this is the `pyeuvics` organization-level GitHub Pages
site. It is served from the root of the Pages hostname, not a project-site
subpath.

Use this URL in MkDocs configuration and tests unless the repository is renamed or a custom domain is explicitly approved:

```text
https://pyeuvics.github.io/
```

Do not add `/euvics.github.io/` to the canonical URL or internal base path.

## 3. Source-of-truth boundaries

- Scientific or engineering corrections belong in the appropriate source repository.
- Website-owned pages may summarize approved source material, but must link to its provenance.
- Never create a website-only implementation of pyEUVICS equations or calculations.
- Never edit staged or generated copies by hand.
- Never copy an entire source repository into the public site.
- Publish only files explicitly authorized by a versioned publication manifest.
- Treat every unlisted source file as excluded.

When source content needs a correction, stop and identify the source repository and path. Make the correction there under that repository's `AGENTS.md`, obtain review, then update the locked source commit used by this website.

## 4. Scientific conventions

Website summaries, tables, captions, and equations must preserve the conventions used by the source repositories:

- Identify electron energy explicitly as kinetic or total energy.
- Define collision angle between electron and laser propagation vectors: `0°` is co-propagating and `180°` is head-on.
- Define observation angle relative to the electron propagation direction.
- State units and RMS/FWHM, waist, peak/average, and bandwidth conventions.
- State linear/exact, recoil, nonlinear, polarization, harmonic, aperture, and spectral-statistic assumptions.
- Use “extreme ultraviolet (EUV)” consistently.
- Keep known CAIN discrepancies and validation limitations visible.

Do not shorten a statement in a way that removes a scientific limitation or changes a design target into a validated result.

## 5. Publication and privacy policy

GitHub Pages is a public publishing surface. Before any source file enters the staged site:

1. Confirm that its source publication manifest allows it.
2. Confirm its publication status and owner approval.
3. Check confidentiality, copyright, license, and figure-permission status.
4. Check for credentials, internal URLs, personal data, machine names, and absolute local paths.
5. Preserve required attribution and validation notices.

Never publish by default:

- Internal reviews, comment registers, or open decision logs
- Confidential budgets, partner information, or institutional commitments
- Raw experimental or simulation data not explicitly released
- Credentials, tokens, environment files, or authentication material
- Local filesystem paths or user-specific configuration
- Restricted figures or copied material without permission
- Unapproved requirements or draft performance claims presented as baselined
- Historical archive documents merely because they exist in a source repository

If publication approval is ambiguous, keep the item excluded and report the decision needed.

## 6. Provenance and source locking

Every public build must record the exact source commits used for `euvics` and `pyEUVICS`. Use a versioned lock file such as:

```text
sources.lock.yml
```

The assembled site must expose sufficient provenance for material outputs:

- Source repository and commit
- Document or package version
- Publication or validation status
- Build timestamp
- Relevant configuration or campaign identifier
- SHA-256 checksum for downloadable PDFs and release artifacts

A build must fail when a source checkout does not match its locked commit.

## 7. Intended repository layout

```text
pyeuvics.github.io/
├── AGENTS.md
├── README.md
├── LICENSE
├── mkdocs.yml
├── requirements-docs.txt
├── sources.lock.yml
├── content/
│   ├── index.md
│   ├── project/
│   ├── documents/
│   ├── software/
│   ├── campaigns/
│   ├── downloads/
│   ├── about/
│   ├── stylesheets/
│   └── javascripts/
├── tools/
│   ├── assemble_site.py
│   ├── validate_allowlist.py
│   ├── rewrite_internal_links.py
│   ├── render_notebooks.py
│   └── verify_site.py
├── tests/
├── docs/
│   ├── codex_tasks.md
│   ├── exec-plans/active/
│   └── exec-plans/completed/
├── .github/workflows/
│   ├── site-check.yml
│   └── pages.yml
└── .gitignore
```

Use temporary or ignored directories for checked-out sources, staging, generated notebooks, and the built MkDocs site. Do not commit external repository checkouts or generated site output.

## 8. Site construction rules

- Use MkDocs with Material for MkDocs unless an approved architecture decision changes the generator.
- Set `site_url` to `https://pyeuvics.github.io/`.
- Pin documentation dependencies outside the pyEUVICS runtime dependency list.
- Build with `mkdocs build --strict`.
- Keep navigation explicit and reviewable.
- Use MathJax or an equivalent approved static solution for equations.
- Ensure internal links work from the organization-site root path `/`.
- Prefer relative internal links in source Markdown.
- Do not hard-code local clone locations.
- Keep substantial transformation logic in tested tools rather than GitHub Actions shell fragments.

## 9. EUVICS document handling

Build the Proposal and CDR through the documented `euvics` repository build process. Publish web overview pages and approved PDFs rather than automatically converting complete LaTeX sources to Markdown.

For each PDF, display:

- Title
- Version or revision
- Date
- Draft/approved status
- Source commit
- SHA-256 checksum
- Known limitations or review status

Reject unresolved citations, references, missing figures, and failed archive checks.

## 10. pyEUVICS documentation and notebooks

- Import only allowlisted Markdown, assets, campaign summaries, and notebooks.
- Preserve the pyEUVICS package as the sole implementation of calculations.
- Render notebooks statically in a temporary staging directory.
- Never modify source notebooks during rendering.
- Record package version, source commit, execution policy, and validation status.
- Keep expensive or data-dependent notebooks unpublished until reviewed.
- GitHub Pages cannot provide a running Python or JupyterLab server; do not describe static notebook pages as interactive computation.

## 11. Credentials and external repositories

If source repositories are public, prefer public read-only checkout.

If private-source access is required:

- Use a narrowly scoped read-only GitHub App or fine-grained token.
- Grant access only to `pyeuvics/euvics` and `pyeuvics/pyEUVICS` contents.
- Store the credential only as a GitHub Actions secret.
- Never print it, save it in artifacts, place it in a remote URL, or write it to generated pages.
- Never request broader repository, workflow, administration, issue, or write permission merely for convenience.

Adding or changing credentials requires explicit user authorization.

## 12. GitHub Actions and deployment

Pull requests must run secret-free website tests, strict typing, and a strict
MkDocs build without deploying or reading private sources. Complete assembly
and validation against the locked private sources must run after protected
merge on the approved default branch, or in an explicitly authorized trusted
manual workflow, before deployment.

The deployment workflow should:

1. Check out this repository.
2. Check out the exact locked source commits.
3. Validate source publication manifests.
4. Build approved EUVICS PDFs.
5. Stage approved pyEUVICS documentation and notebooks.
6. Build MkDocs in strict mode.
7. Scan the final artifact for excluded content, secrets, local paths, and unexpected files.
8. Upload the Pages artifact.
9. Deploy through the protected `github-pages` environment.

Use least-privilege permissions. Do not change Pages settings, repository visibility, secrets, custom domains, or environment protection without explicit authorization.

## 13. Accessibility and presentation

- Use semantic headings and descriptive link text.
- Provide meaningful alternative text for informative images.
- Do not rely on color alone to communicate status.
- Maintain readable contrast and visible keyboard focus.
- Test desktop and mobile navigation.
- Verify equations, tables, code blocks, PDFs, and print behavior.
- Label Draft, Design Target, Calculated, Simulated, Reference, Validated, and Unvalidated states consistently.

Do not add decorative imagery that obscures scientific status or consumes excessive bandwidth.

## 14. Testing and completion checks

Once the corresponding tools exist, run at minimum:

```bash
python -m pytest
mkdocs build --strict
```

Also verify:

- Publication manifests and source locks
- Internal and external links
- Root base-path correctness under `/`
- No local absolute paths
- No excluded or unexpected files
- PDF checksums and metadata
- Notebook source immutability
- Secret scanning of the generated artifact
- Mobile and signed-out site access before release

Do not weaken checks or broad-exclude warnings merely to make a build pass.

## 15. Execution-plan discipline

Before a substantial website task:

1. Create a bounded plan under `docs/exec-plans/active/`.
2. Record scope, decisions, progress, and verification evidence.
3. Implement the smallest coherent change.
4. Run targeted and full checks.
5. Record unresolved publication or scientific questions.
6. Move the plan to `docs/exec-plans/completed/` only when the task is genuinely complete.

Use a sequential zero-padded prefix for completed plans, for example:

```text
00001_repository_foundation.md
```

## 16. Repository corrections to make first

The initial repository audit identified these foundation items:

- Add this root `AGENTS.md` and the website `README.md`.
- Rename `LINCESNE` to `LICENSE` without changing its MIT license text unless explicitly approved.
- Replace or archive planning text that incorrectly targets `pyEUVICS/pyEUVICS.github.io`.
- Review `.gitignore`; ensure the `downloads/` pattern does not accidentally hide intended website-source content.
- Confirm the organization-site URL in all current configuration and
  documentation while preserving historical records.

Do not combine these mechanical corrections with scientific-content publication.

## 17. Definition of done

A website change is complete only when:

- It respects authoritative source boundaries.
- Every imported item is allowlisted and traceable.
- Scientific status and limitations are preserved.
- The local build and relevant tests pass.
- The organization-site root path works.
- Generated artifacts contain no excluded content or secrets.
- Accessibility and link checks pass for the affected pages.
- Changed files, verification evidence, and remaining decisions are reported.
