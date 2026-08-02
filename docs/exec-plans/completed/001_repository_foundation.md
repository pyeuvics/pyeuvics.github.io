# Repository foundation — completed

## Scope

Task 0 from `docs/codex_tasks.md`: baseline the website repository, retain the
reviewed root instructions and README, make the prescribed mechanical
corrections, and leave deployment, credentials, remote settings, and scientific
content out of scope.

## Completed work

- Confirmed the reviewed `AGENTS.md` and `README.md` are installed at the root.
- Confirmed `LINCESNE` was renamed to `LICENSE` without changing the MIT text.
- Archived the obsolete `pyEUVICS.github.io` planning documents under
  `docs/archive/github_pages_plan_20260731/`; the current plan is
  `docs/codex_tasks.md`.
- Added `docs/exec-plans/active/` and `docs/exec-plans/completed/`.
- Removed duplicate `.gitignore` entries and changed the broad `downloads/`
  rule to the root-only `/downloads/`, so `content/downloads/` remains eligible
  for version control.
- Added ignore rules for temporary source checkouts, staging, rendered
  intermediates, local secrets, private keys, and generated MkDocs output.
- Confirmed the documented default Pages URL is
  `https://chongshikpark.github.io/euvics.github.io/`.

## Verification evidence

- `git diff --check` passed.
- `git log --follow --name-status -- LICENSE` confirms the license rename was
  detected with 100% similarity; SHA-256 of `LICENSE` is
  `570a81bfb4e4180eaf4394d5b4c6d7373ba7e27fde025afa4506d3c74bee170f`.
- Active-document URL scan found no claim that this repository produces
  `https://euvics.github.io/` or `https://pyEUVICS.github.io/`; explanatory
  warnings and Task 0's rejection criteria remain intentionally present.
- Every relative Markdown link in `README.md` and `docs/codex_tasks.md` resolves.
- Personal absolute-path scan of tracked text found none.
- Ignore checks confirm `content/downloads/example.md` is not ignored, while
  `.sources/`, `.staging/`, `.rendered/`, `.env`, private keys, and `site/` are
  ignored.
- `git status --short --untracked-files=all` and the tracked diff were reviewed to confirm that only
  the intended foundation files changed.

## Remaining decisions

None for Task 0. Scientific publication, source manifests, site construction,
GitHub configuration, and deployment remain deferred to their later tasks.
