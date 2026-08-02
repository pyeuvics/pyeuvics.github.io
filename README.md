# EUVICS Documentation Website

This repository builds the public website that brings together approved documentation from the **EUVICS light-source project** and the **pyEUVICS scientific software package**.

## Repository and website address

```text
Repository: https://github.com/chongshikpark/euvics.github.io
Default Pages URL: https://chongshikpark.github.io/euvics.github.io/
```

This is a GitHub **project site** because the repository is owned by `chongshikpark` but is not named `chongshikpark.github.io`. GitHub therefore serves it below the repository-name path.

A repository named `chongshikpark/euvics.github.io` does **not** create `https://euvics.github.io/`. That account-level address would require a GitHub user or organization named `euvics` and a repository named `euvics.github.io`.

If a shorter URL is preferred later, review one of these separately:

- Rename the repository to `euvics`, producing `https://chongshikpark.github.io/euvics/`.
- Create or transfer the site to an approved `euvics` organization.
- Configure a separately registered custom domain.

Do not change ownership, repository name, or domain as part of ordinary website development.

## Authoritative sources

The website aggregates approved public content from:

- [chongshikpark/euvics](https://github.com/chongshikpark/euvics) — EUVICS Proposal, Conceptual Design Report (CDR), requirements, bibliography, and document builds.
- [chongshikpark/pyEUVICS](https://github.com/chongshikpark/pyEUVICS) — package documentation, tutorials, notebooks, scientific validation, and reference campaigns.

Those repositories remain authoritative. This repository owns only the website shell, navigation, staging, link transformation, search, and deployment. Scientific or document corrections must be made and reviewed in the appropriate source repository before republication.

## Publication model

The site uses an allowlist-and-lock approach:

```text
approved source commits
→ validate source publication manifests
→ build approved Proposal/CDR PDFs
→ stage approved pyEUVICS documents and notebooks
→ build one MkDocs site
→ inspect the complete static artifact
→ deploy through GitHub Actions
```

Every public build should record exact source commits. Files not included in a reviewed publication manifest remain excluded.

## Planned information architecture

```text
Home
├── Project
│   ├── Overview
│   ├── EUVICS concept
│   ├── Reference cases
│   └── Status and roadmap
├── Documents
│   ├── EUVICS Proposal
│   └── Conceptual Design Report
├── Software
│   ├── Installation and quickstart
│   ├── Physics and conventions
│   ├── Tutorials and API
│   ├── Workflows
│   ├── Validation
│   └── Selected static notebooks
├── Reference campaigns
│   ├── 6.7 nm
│   └── 13.5 nm
├── Downloads
└── About
```

## Technology

The planned site uses:

- [MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- MathJax for mathematical notation
- Static notebook rendering for selected pyEUVICS examples
- GitHub Actions for validation and Pages deployment

GitHub Pages serves static content. It does not run pyEUVICS, Python, or JupyterLab on the server. Website notebooks are readable static renderings; users run actual simulations from the pyEUVICS package or local JupyterLab environment.

## Current status

Tasks 0–7 established the repository, information architecture, source
publication contracts, local MkDocs scaffold, deterministic assembly, and the
Proposal/CDR and static pyEUVICS notebook/campaign publication pipelines. The
current locked EUVICS manifest approves no PDFs, while pyEUVICS notebook sets
remain approval-pending and campaign sets remain blocked. Those production
pages therefore remain placeholders. Before further scientific content is
published, the project will:

1. Approve complete Proposal/CDR release metadata and artifacts in EUVICS.
2. Approve exact notebook and campaign sets with complete execution and
   validation metadata in pyEUVICS.
3. Add validation and deployment workflows.
4. Perform a signed-out public-release review.

See [Codex website tasks](docs/codex_tasks.md) for the sequenced implementation prompts.

## Intended repository structure

```text
euvics.github.io/
├── AGENTS.md
├── README.md
├── LICENSE
├── mkdocs.yml
├── requirements-docs.txt
├── sources.lock.yml
├── content/
├── tools/
├── tests/
├── docs/
│   ├── codex_tasks.md
│   └── exec-plans/
├── .github/workflows/
└── .gitignore
```

Temporary source checkouts, staging files, rendered notebook intermediates, and the generated MkDocs site must remain untracked.

## Local development

Create an isolated documentation environment and run the local checks:

```bash
python -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r requirements-docs.txt

mkdocs serve
mkdocs build --strict
python -m pytest
```

The generated site is written to ignored `site/`. Source assembly commands are
deferred until the source locks and publication contracts are integrated.

With both reviewed source-contract commits recorded in `sources.lock.yml`,
assemble a clean local review artifact with:

```bash
SOURCE_DATE_EPOCH=1785628800 python tools/assemble_site.py \
  --euvics-source /path/to/clean/euvics \
  --pyeuvics-source /path/to/clean/pyEUVICS \
  --output .staging/review-build
```

Assembly refuses unresolved locks, dirty or mismatched source checkouts, and an
existing output path. Approved Proposal/CDR PDFs are rebuilt and checksum-
verified in disposable source exports. Approved notebooks execute twice in a
disposable source export and are published only when their static renders match
exactly; approved campaign files are staged without recalculation.

Do not hard-code personal source paths into configuration, tests, generated pages, or committed scripts.

## Deployment

The production workflow will use GitHub Pages artifacts:

- Pull requests build and validate without deployment.
- Approved default-branch changes may deploy.
- Source repositories are checked out at locked commits.
- Private-source access, if required, uses a narrowly scoped read-only credential.
- The final artifact is checked for excluded content, secrets, and local paths.
- Deployment uses the protected `github-pages` environment.

The repository administrator must configure:

```text
Settings → Pages → Build and deployment → Source → GitHub Actions
```

Do not enable Pages until the first full artifact has passed publication review.

## Publication safety

GitHub Pages is public. Do not publish internal reviews, confidential costs, restricted figures, raw private data, credentials, local paths, or unapproved scientific claims.

Every published document should identify its status and provenance. Design targets, calculated results, simulations, references, validation results, and measurements must remain distinguishable.

## Contributing with Codex

Read [AGENTS.md](AGENTS.md) before making changes. Work through the tasks in [docs/codex_tasks.md](docs/codex_tasks.md) sequentially and keep an execution record under `docs/exec-plans/`.

Codex may scaffold, transform, test, and document the site. Scientific conclusions, publication approvals, repository visibility, credentials, Pages activation, custom domains, and public release remain owner-controlled decisions.

## License

The repository currently contains MIT license text. Before the first release, rename the existing `LINCESNE` file to `LICENSE` and confirm that the license applies to the website source. Imported documents, figures, data, and third-party material may have separate licenses and attribution requirements.

## References

- [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
