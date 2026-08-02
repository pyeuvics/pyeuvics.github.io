# pyEUVICS notebook and campaign integration — completed

## Scope

Task 7 from `docs/codex_tasks.md`: extend deterministic assembly to render only
manifest-approved pyEUVICS notebooks as static pages and stage approved 6.7 nm
and 13.5 nm campaign material with complete provenance.

## Boundaries

- Do not change or execute source notebooks in place.
- Do not infer approval from candidate sets. The locked source contract leaves
  notebooks approval-pending and campaign material blocked, so the real build
  must publish neither at present.
- Do not describe static pages as interactive Jupyter environments.
- Do not publish unapproved data, generated campaign outputs, or package source.
- Do not deploy.

## Planned work

- [x] Define strict notebook/campaign manifest metadata and execution policy.
- [x] Render approved notebooks in disposable staging with deterministic inputs.
- [x] Record package version, commit, source path, execution policy, seed/config,
      validation status, limitations, and local requirements on every page.
- [x] Reject outputs in source notebooks, failed cells, local paths, secrets,
      unapproved dependencies, oversized inputs/outputs, and missing provenance.
- [x] Stage approved campaign pages/assets with explicit status and provenance.
- [x] Verify source bytes are unchanged and render output is deterministic.
- [x] Test links, assets, size limits, and strict MkDocs builds.
- [x] Run the real locked assembly and confirm fail-closed exclusion.
- [x] Record evidence and move this plan to completed.

## Decisions

- Synthetic notebook/campaign fixtures will exercise the successful path until
  the source owner admits exact files to the pyEUVICS allowlist with metadata.
- Notebook execution will use a clean temporary copy and a bounded kernel run;
  trusted-output rendering is not permitted for output-free source notebooks.
- Campaign files remain ordinary immutable source artifacts; the website adds
  provenance but never recalculates scientific results.

## Verification evidence

- `python -m pytest -q`: 37 passed. Jupyter tests ran with permission to bind
  process-local localhost kernel ports.
- `python -m mypy --strict tools/site_assembly tools/assemble_site.py`: no
  issues in 7 source files.
- `mkdocs build --strict`: passed.
- Synthetic execution covered deterministic Markdown/image rendering, source
  immutability, campaign link/assets, source/output size limits, failed cells,
  pre-existing outputs, nondeterminism, unapproved data, local paths, secrets,
  network-dependent code, active content, and unsupported output MIME types.
- Locked real-source assembly passed with 53 approved documentation files. It
  contained only the static-notebook placeholder and no campaign imports,
  because the locked pyEUVICS contract approves neither set.
- The real EUVICS and pyEUVICS source worktrees remained clean.

## Remaining publication decision

The pyEUVICS source owner must revise its publication-contract schema and
manifest to mark exact initial notebook/campaign sets approved and record the
execution, dependency, seed/configuration, validation, size, limitation, and
approval metadata enforced here. Directory-wide dependencies are not accepted;
approved dependencies must be exact files. The current 6.7 nm known disagreement
and provisional 13.5 nm validation status must remain visible.
