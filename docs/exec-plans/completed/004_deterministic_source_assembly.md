# Deterministic source assembly — completed

## Scope

Task 5 from `docs/codex_tasks.md`: implement a typed, tested command that
validates locked EUVICS and pyEUVICS publication contracts, stages only exact
allowlisted Markdown and ordinary assets, rewrites links in staging, records
provenance/inventory, builds MkDocs strictly, and scans the final artifact.

## Boundaries

- Do not build or publish PDFs, render notebooks, add credentials/workflows, or
  deploy.
- Never modify either source checkout; prove byte-for-byte immutability in
  integration tests.
- Reject unresolved locks, dirty/mismatched commits, missing approvals,
  traversal, broken links, local paths, unexpected types/files, and suspicious
  credential-like content.
- Use only synthetic fixture repositories in tests. No private or scientific
  source material enters fixtures.
- Source-contract commits became available during implementation; production
  locks now identify those exact reviewed revisions.

## Planned work

- [x] Define strict website lock and supported source-contract adapters.
- [x] Implement commit/worktree/manifest validation and exact allowlist loading.
- [x] Implement temporary staging, collision-safe routing, link rewriting,
      provenance/edit metadata, and deterministic inventory generation.
- [x] Implement staged-tree verification, strict MkDocs build, and final
      artifact scans.
- [x] Add unit and synthetic integration tests for success, failure paths,
      source immutability, and deterministic output.
- [x] Document local assembly usage and production-lock workflow.
- [x] Run targeted/full pytest and strict placeholder-site build.
- [x] Record evidence and move the plan to completed only when implementation
      and synthetic verification are complete.

## Decisions

- Source files route below `content/imported/euvics/` and
  `content/imported/pyeuvics/`, preventing collisions with website-owned pages.
- Repository-relative links to another allowlisted file become staging-relative
  links. Links to existing but unpublished source files become locked-commit
  source links only when the source contract declares that policy; otherwise
  assembly fails.
- Source/edit/provenance metadata is appended to staged Markdown, never written
  back to source files.
- Assembly output is temporary by default. An optional explicit staging path is
  accepted only beneath ignored workspace/output locations.

## Completed implementation

- Added typed `tools/site_assembly/` modules for models, source locks/contracts,
  checkout verification, exact allowlist handling, staging, link rewriting,
  provenance, inventory, strict builds, and artifact scans.
- Added `tools/assemble_site.py`, requiring explicit clean source paths and a
  new output path. `SOURCE_DATE_EPOCH` is mandatory for deterministic build
  metadata.
- Locked EUVICS at `dcae0fba5b6cbb9073e0e552ca74c0a14484e2b0` and
  pyEUVICS at `6193ab3e2be39fc74d40cd7ed1f9cece993b9ecd` after both
  publication contracts became available in clean committed worktrees.
- Source files route below `content/imported/<source>/`. Markdown links to
  another approved file become staging-relative; pyEUVICS links to existing
  unpublished files become locked-commit source links under its declared
  policy. Broken, escaping, root-local, or unauthorized links fail assembly.
- Staged Markdown receives visible source, edit, repository, commit, status,
  source SHA-256, build timestamp, and known-limitations metadata.
- The deterministic JSON inventory records both source and staged checksums,
  which distinguishes transformed Markdown from authoritative input.
- Final scans reject unexpected artifact types, local paths, private-key
  markers, AWS keys, GitHub-token forms, and JWT-like material.
- Added 15 synthetic assembly tests using generic Git fixtures only. PDFs and
  notebooks remain deliberately deferred.

## Verification evidence

- Full repository tests: 21 passed (15 source-assembly tests plus six site
  foundation tests).
- Strict mypy: no issues in five assembly source files.
- Placeholder `mkdocs build --strict`: passed. Material printed its existing
  MkDocs 2.0 advisory; MkDocs reported no strict-build warnings.
- Synthetic CLI/integration builds passed, including source immutability,
  identical repeated inventories, staged link rewriting, provenance, search
  site generation, and final artifact scanning.
- Failure tests cover unresolved/mismatched commits, dirty checkouts, unknown
  manifest fields, traversal/globs, missing approval, exclusion leakage,
  missing/unpublished links, local paths, credential-like content, unexpected
  file types, and existing output paths.
- Real production assembly passed twice with `SOURCE_DATE_EPOCH=1785628800`.
  Both runs produced byte-identical inventories containing 53 approved files:
  zero from EUVICS (its current allowlist is intentionally empty) and 53 from
  pyEUVICS.
- Both real source worktrees remained clean after assembly. The built artifact
  includes `site/index.html` and the public staged inventory.
- `git diff --check` passed; generated review builds remain ignored below
  `.staging/`.

## Remaining decisions and deferred scope

- EUVICS overview/PDF content remains absent until its source contract records
  explicit file-level approval.
- The pyEUVICS campaign pages and selected notebooks remain non-public
  candidates under their source contract.
- Proposal/CDR building belongs to Task 6; notebook execution/rendering belongs
  to Task 7. No credential, workflow, or deployment work was performed.
