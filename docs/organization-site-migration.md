# Organization-site migration

The canonical website repository is now
[`pyeuvics/pyeuvics.github.io`](https://github.com/pyeuvics/pyeuvics.github.io),
and its canonical GitHub Pages URL is <https://pyeuvics.github.io/>. Because
the repository name matches the organization name, the site uses the root `/`
base path.

The organization repository is a separate copy of the former personal
repository, not a GitHub repository transfer. Completed execution plans,
`docs/release-readiness/` records, and `docs/codex_tasks.md` preserve their old
repository URLs and `/euvics.github.io/` paths as historical evidence. Those
references describe the context in which the records were created; they are
not current deployment targets.

The authoritative scientific sources remain
[`chongshikpark/euvics`](https://github.com/chongshikpark/euvics) and
[`chongshikpark/pyEUVICS`](https://github.com/chongshikpark/pyEUVICS), as locked
in `sources.lock.yml`. Moving the website does not authorize moving or changing
those sources.

Before the organization repository becomes the production deployment source,
an administrator must:

- generate distinct read-only deploy keys for the two private source
  repositories and store their private halves as `EUVICS_SOURCE_DEPLOY_KEY`
  and `PYEUVICS_SOURCE_DEPLOY_KEY` Actions secrets in the organization
  repository;
- protect `main` and require the site-validation check;
- confirm least-privilege Actions workflow permissions;
- restrict the `github-pages` environment to `main` and configure Pages to use
  GitHub Actions;
- set the repository homepage to <https://pyeuvics.github.io/>;
- resolve personal-repository pull request #7 deliberately; and
- choose whether the personal repository is a read-only archive or a maintained
  non-deploying mirror.

Secret values cannot be retrieved or copied from the personal repository. Do
not reuse exposed private key material. Deployment remains blocked until these
controls and credentials are configured and the organization build succeeds.
