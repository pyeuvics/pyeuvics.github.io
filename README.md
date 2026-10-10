# EUVICS Documentation Website

This repository builds the public website that brings together approved documentation from the **EUVICS light-source project** and the **pyEUVICS scientific software package**.

## Repository and website address

```text
Repository: https://github.com/pyeuvics/pyeuvics.github.io
Default Pages URL: https://pyeuvics.github.io/
```

This is the `pyeuvics` organization-level GitHub Pages site because the
repository name matches the organization name. GitHub serves it from `/`; it
does not use an `/euvics.github.io/` project-site base path.

The previous `chongshikpark/euvics.github.io` repository remains a separate
personal copy. See the [organization-site migration record](docs/organization-site-migration.md)
for the historical-document policy and remaining administrator work.

## Authoritative sources

The website aggregates approved public content from:

- [pyeuvics/euvics](https://github.com/pyeuvics/euvics) — EUVICS Proposal, Conceptual Design Report (CDR), requirements, bibliography, and document builds.
- [pyeuvics/pyEUVICS](https://github.com/pyeuvics/pyEUVICS) — package documentation, tutorials, notebooks, scientific validation, and reference campaigns.

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

Every assembled public build records exact source commits. Files not included in a reviewed publication manifest remain excluded.

## Website sections

```text
Home
├── Project
│   ├── Overview
│   └── Design status
├── Documents
│   ├── EUVICS Proposal
│   └── Conceptual Design Report
├── Software
│   ├── Installation
│   ├── Science and conventions
│   ├── API reference
│   ├── Tutorials
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

The site uses:

- [MkDocs](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- MathJax for mathematical notation
- Static notebook rendering for selected pyEUVICS examples
- GitHub Actions for validation and Pages deployment

GitHub Pages serves static content. It does not run pyEUVICS, Python, or JupyterLab on the server. Website notebooks are readable static renderings; users run actual simulations from the pyEUVICS package or local JupyterLab environment.

## Current implementation and approval state

The website supports exact-lock source assembly, approved PDF rebuilds, dual
notebook execution, campaign imports, typed publication indexes, artifact
ownership checks and separate validation/proposal/deployment workflows.

For the source approval snapshot reviewed **2026-10-10**, see the
[development and validation runbook](docs/development.md#approval-snapshot-not-an-evergreen-claim).
That dated snapshot is not an approval of later source heads. The authoritative
manifests at `sources.lock.yml` determine what can enter each build.

Start with the [current runbook](docs/development.md), then consult
[CI boundaries](docs/ci-validation.md),
[Pages deployment](docs/pages-deployment.md), and
[source-update proposals](docs/source-update-automation.md) for their respective
review and authorization requirements. The historical foundation prompts are
retained in [docs/codex_tasks.md](docs/codex_tasks.md).

## Repository structure

```text
pyeuvics.github.io/
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

Use the [development and validation runbook](docs/development.md) for the
maintained installation and commands. It distinguishes a shell preview,
secret-free synthetic quality checks, local browser tests, exact-lock assembly,
trusted source validation, proposal evidence and deployment. Generated output
stays untracked. Never commit local source paths or credentials.

## Deployment

The production workflow uses GitHub Pages artifacts:

- Pull requests build and validate without deployment.
- Approved default-branch changes may deploy.
- Source repositories are checked out at locked commits.
- Private-source access, if required, uses a narrowly scoped read-only credential.
- The final artifact is checked for excluded content, secrets, and local paths.
- Deployment uses the protected `github-pages` environment.

The production workflow expects this Pages setting; verify live administrator
settings separately before release:

```text
Settings → Pages → Build and deployment → Source → GitHub Actions
```

The first scoped artifact was deployed only after publication review and owner
authorization. Future deployments remain gated by exact source locks,
publication manifests, validation, and the protected `github-pages` environment.

## Publication safety

GitHub Pages is public. Do not publish internal reviews, confidential costs, restricted figures, raw private data, credentials, local paths, or unapproved scientific claims.

Every published document should identify its status and provenance. Design targets, calculated results, simulations, references, validation results, and measurements must remain distinguishable.

## Contributing with Codex

Read [AGENTS.md](AGENTS.md), [current work](docs/current-work.md), and the [current runbook](docs/development.md) before making changes. Keep a bounded execution record under `docs/exec-plans/`; historical foundation prompts are not a current work queue.

Codex may scaffold, transform, test, and document the site. Scientific conclusions, publication approvals, repository visibility, credentials, Pages activation, custom domains, and public release remain owner-controlled decisions.

## License

The website source is MIT-licensed in `LICENSE`. Imported documents, figures,
data, and third-party material may have separate licenses and attribution
requirements.

## References

- [What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
