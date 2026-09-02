# Website repository migration

## Scope

Migrate the website from the former `chongshikpark/euvics.github.io` project
site to the `pyeuvics/pyeuvics.github.io` organization site, update the locked
pyEUVICS source location, and deploy the validated site at
`https://pyeuvics.github.io/`.

## Decisions

- Preserve `chongshikpark/euvics` as the authoritative EUVICS document source.
- Use `pyeuvics/pyEUVICS` as the authoritative software source.
- Treat the website as an organization site hosted at the domain root.
- Preserve source-commit locking, publication allowlists, validation status,
  and the existing GitHub Pages artifact deployment path.

## Progress

- [x] Confirm repository ownership, Pages configuration, and current 404.
- [x] Add regression coverage for the organization-site URL and source locks.
- [x] Update website configuration, source adapters, current documentation,
      and provenance expectations.
- [x] Lock the reviewed pyEUVICS migration commit and validate the complete
      assembled site.
- [ ] Push both repositories, deploy Pages, and verify signed-out access.

## Verification evidence

- GitHub Pages is configured for workflow deployment with the expected
  `https://pyeuvics.github.io/` URL; it returned HTTP 404 before migration.
- The reviewed pyEUVICS commit `806b900b2e404a753982aeab97fd3fda9a378a72`
  was pushed and locked exactly.
- Full website tests: 76 passed.
- Strict standalone MkDocs build: passed.
- Complete source-derived validation: both publication manifests passed, 76
  tests passed, strict typing passed for 11 source files, both strict MkDocs
  builds passed, and the review artifact manifest was generated.
- Deployment and signed-out verification: pending.
