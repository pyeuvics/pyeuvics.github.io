# Website repository migration

## Scope

Migrate the website from the former `chongshikpark/euvics.github.io` project
site to the `pyeuvics/pyeuvics.github.io` organization site, update both locked
source locations, and deploy the validated site at
`https://pyeuvics.github.io/`.

## Decisions

- Use `pyeuvics/euvics` as the authoritative EUVICS document source.
- Use `pyeuvics/pyEUVICS` as the authoritative software source.
- Treat the website as an organization site hosted at the domain root.
- Preserve exact source-commit locking, publication allowlists, validation
  status, and the GitHub Pages artifact deployment path.
- Use a Contents-read-only GitHub App installed only on the two source
  repositories for private source access.

## Outcome

- [x] Updated the canonical repository, Pages URL, root base path, source locks,
      adapters, current governance, architecture, and operational documents.
- [x] Locked `pyeuvics/euvics` at
      `cae6d70f0e0d38b9859869626da5987c45462ef1` and `pyeuvics/pyEUVICS`
      at `806b900b2e404a753982aeab97fd3fda9a378a72`.
- [x] Deployed the validated organization site and verified it signed out.
- [x] Added a regression that prevents current governance and architecture
      documents from reverting to the former source owner.

## Verification evidence

- Pages run `33691189388` created the App token, checked out both exact private
  source commits, passed credential cleanup and the complete source-derived
  validation, uploaded the artifact, and deployed successfully.
- Local final suite: 77 passed in 39.79 seconds.
- Final standalone `mkdocs build --strict`: passed.
- `https://pyeuvics.github.io/`, `/project/overview/`, and
  `/software/installation/` returned the expected pages and organization-root
  canonical URLs in a signed-out HTTP session.
- A deliberately missing route returned HTTP 404.
- The former repository remains referenced only where historical context is
  intentional; current source ownership uses the `pyeuvics` organization.

## Remaining decisions

None for this migration. Normal branch, environment, publication, and source
review controls remain ongoing administrator responsibilities.
