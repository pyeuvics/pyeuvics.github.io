# Proposal and CDR publication integration — completed

## Scope

Task 6 from `docs/codex_tasks.md`: extend deterministic assembly to build and
stage only manifest-approved EUVICS Proposal/CDR PDFs, verify source checks and
checksums, generate metadata-rich overview pages, and exclude historical or
internal PDFs.

## Boundaries

- Do not change the EUVICS source repository or infer approval from a generated
  file, repository release, filename, or document appearance.
- The locked EUVICS contract currently approves zero files, so production
  assembly must continue to publish no Proposal/CDR PDF.
- Do not convert complete LaTeX sources to Markdown.
- Do not render notebooks, add credentials/workflows, or deploy.
- Use only generic synthetic document fixtures for success/failure tests.

## Planned work

- [x] Define strict approved-document manifest metadata and roles.
- [x] Run the locked source repository's documented archive/check/build flow
      without modifying tracked source files.
- [x] Reject build failures, unresolved citation/reference/missing-file log
      markers, symlink/path escapes, checksum mismatches, and historical PDFs.
- [x] Stage only exact approved newly built PDFs and generate overview/download
      pages with title, revision, date, status, source commit, SHA-256,
      attribution/license, and known limitations.
- [x] Extend inventory and final-artifact verification for PDFs and links.
- [x] Add synthetic success/failure/source-immutability tests.
- [x] Run full pytest, strict mypy, strict placeholder build, and real locked
      assembly demonstrating fail-closed empty document publication.
- [x] Record PDF verification evidence and move the plan to completed.

## Decisions

- An approved PDF entry must use kind `pdf`, publication status `released`, an
  explicit approved role (`proposal` or `cdr`), expected build path, title,
  revision, document date, license, attribution, limitations, and SHA-256.
- The source contract remains the sole approval authority. The website never
  selects an arbitrary PDF from `build/`, `papers/`, or `archive/`.
- Synthetic PDFs may be minimal fixtures; no synthetic scientific content or
  results are used.

## Verification evidence

- `python -m pytest -q`: 29 passed.
- `python -m mypy --strict tools/site_assembly tools/assemble_site.py`: no
  issues in 6 source files.
- `mkdocs build --strict`: passed.
- Locked real-source assembly: passed with 53 approved files, all from the
  pyEUVICS contract; the generated site contained zero PDFs because the locked
  EUVICS manifest approves none.
- Both real source worktrees remained clean after assembly.
- Synthetic deterministic PDFs were parsed with pypdf, checked for pages, and
  exercised through text extraction. Poppler 26.07.0 is available at
  `/usr/local/bin/pdftoppm`; there is no approved production PDF to render
  visually in this task.
- The verified pyEUVICS checkout is
  `/Users/cspark/Work/simulation_codes-working/pyEUVICS`.

## Remaining publication decision

The EUVICS source owner must approve canonical Proposal/CDR PDF entries and all
required release metadata in the EUVICS publication manifest before either
download can appear. No website-side approval was inferred.
