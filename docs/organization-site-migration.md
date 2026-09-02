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

The authoritative scientific sources are
[`pyeuvics/euvics`](https://github.com/pyeuvics/euvics) and
[`pyeuvics/pyEUVICS`](https://github.com/pyeuvics/pyEUVICS), as locked in
`sources.lock.yml`.

Before the organization repository becomes the production deployment source,
an administrator must:

- install a Contents-read-only GitHub App only on the two private source
  repositories and store its App ID and private key as repository Actions
  secrets;
- protect `main` and require the site-validation check;
- confirm least-privilege Actions workflow permissions;
- restrict the `github-pages` environment to `main` and configure Pages to use
  GitHub Actions;
- set the repository homepage to <https://pyeuvics.github.io/>;
- resolve personal-repository pull request #7 deliberately; and
- choose whether the personal repository is a read-only archive or a maintained
  non-deploying mirror.

Secret values cannot be retrieved or copied from the personal repository. The
organization build must succeed before production deployment is considered
ready.
