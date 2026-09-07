# Publication contract consumer alignment

## Scope

Align the website's pyEUVICS manifest adapter with the authoritative source
contract, reject unpublished private-source links, and update the locked
pyEUVICS revision after both repositories pass compatibility tests.

## Progress

- [x] Add source-contract compatibility fixtures.
- [x] Align approved notebook fields and dependency handling.
- [x] Replace unpublished-source rewriting with hard rejection.
- [x] Validate reference-style and raw-HTML destinations as rendered by
  Python-Markdown, while excluding fenced code examples.
- [x] Isolate approved notebook runtime writes outside the archived source
  tree and verify deterministic rendering.
- [x] Scrub unrelated build credentials and nondeterministic environment
  variables before launching approved notebook kernels.
- [x] Update the pyEUVICS source lock after the source changes receive a commit
  identifier.
- [x] Run website tests and strict assembly/build verification.
- [x] Archive this plan as completed sequence `029`.

## Verification

- `python -m pytest`: 104 passed (2026-09-04 re-run).
- Ruff check of `tools/site_assembly` and `tests/test_source_assembly.py`:
  passed with the shared pyEUVICS Ruff executable and `--no-cache`.
- `python -m mkdocs build --strict --clean`: passed.
- `python -m mypy tools`: failed on first re-check with
  `Library stubs not installed for "markdown"` after `pipeline.py` began
  importing `markdown` directly for rendered-link validation. Pinned
  `Markdown==3.10.3` and `types-Markdown==3.10.2.20260712` in
  `requirements-docs.txt` (previously an undeclared transitive dependency of
  `mkdocs`); `python -m mypy tools` now reports success on 13 source files.
- `sources.lock.yml` pyEUVICS commit updated to
  `f6211eeb97c375262a087f98dc178b038fc9ee66` (2026-09-07), the commit
  identifier the source-contract compatibility changes landed on.
- Re-ran `python -m pytest` (104 passed), `python -m mkdocs build --strict
  --clean` (passed), and `python -m mypy tools` (success on 13 source
  files) against the updated lock (2026-09-07).

The source lock update and verification are complete in the working tree.
Per the explicit no-commit/no-push constraint below, these changes remain
uncommitted; committing and pushing them is left to the user.

## Constraints

- Do not commit or push changes.
