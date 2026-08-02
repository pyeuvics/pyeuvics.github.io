# GitHub Actions pull-request validation — completed

## Scope

Task 8 from `docs/codex_tasks.md`: add a least-privilege pull-request workflow
that checks out the website and exact locked public sources, runs the same
validation entry point used locally, and uploads a non-deploying review artifact.

## Boundaries

- Do not deploy, enable Pages, change GitHub settings, or add credentials.
- Use public read-only source checkouts with persisted credentials disabled.
- Resolve source revisions exclusively from `sources.lock.yml`; do not duplicate
  commit SHAs in workflow YAML.
- Keep validation/build logic in tested Python tools, not shell fragments.
- Do not weaken publication, artifact, notebook, PDF, or strict-build checks.

## Planned work

- [x] Add a lock-output helper for exact source checkout refs and PDF-toolchain
      detection.
- [x] Add one local/CI validation entry point and deterministic artifact manifest.
- [x] Pin the Python/notebook environment and constrain the hosted runner/actions.
- [x] Add the pull-request workflow with read-only permissions and safe caching.
- [x] Upload the reviewed site/inventory only; add no deployment action or job.
- [x] Test workflow structure, lock resolution, artifact hashing, and failure paths.
- [x] Run the local CI-equivalent command, pytest, mypy, and strict MkDocs.
- [x] Record evidence and move this plan to completed.

## Decisions

- CPython 3.13 is the CI baseline because the locked pyEUVICS package supports
  Python 3.13 and explicitly excludes Python 3.14.
- The two source repositories are public, so no source-access secret is needed.
  Any later private-source credential requires separate explicit authorization.
- TeX packages are installed only when the locked EUVICS manifest contains an
  approved PDF entry.
- The pip cache key derives from documentation/notebook requirements and the
  source lock file; checked-out repositories and generated artifacts are never
  cached.

## Verification evidence

- Workflow YAML parsed successfully and structural tests confirm only
  `pull_request`/`workflow_dispatch`, `contents: read`, exact lock-derived refs,
  non-persisted checkout credentials, bounded pip caching, and no Pages,
  environment, OIDC, secret, or deployment action.
- The shared `python -m tools.validate_ci` command passed against the real locked
  source checkouts in a clean CPython 3.13.14 environment matching CI: both
  publication contracts validated, 43 tests passed, strict mypy passed, two
  strict MkDocs builds passed, and the complete assembly/artifact scan passed.
- The local-equivalent review artifact contains 119 site files plus its staged
  inventory. Its checksum manifest SHA-256 was
  `cfb2fcaa10f28467e0511b2b82be57c25c73fa2f45e0800b3bd1f9f1b2bba6ee`.
- Final checks after documentation/test updates: 43 tests passed, strict mypy
  reported no issues in 10 source files, and `mkdocs build --strict` passed.
- Independent CPython 3.13 and 3.14 local-equivalent builds produced byte-for-byte
  identical review-artifact manifests with the checksum recorded above.
- Both real source worktrees remained clean.

## Remaining external verification

No repository push or workflow dispatch was authorized in this task. The first
GitHub-hosted run therefore remains to be observed after these changes are
committed and proposed in a pull request. Its uploaded review artifact should be
compared with a local run from the same website commit and locked source SHAs.
