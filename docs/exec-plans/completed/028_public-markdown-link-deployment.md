# Public Markdown link deployment

## Scope

Update the locked pyEUVICS source to the reviewed public-link cleanup, rebuild
and validate the website, deploy it through the protected default-branch
workflow, and verify signed-out public behavior.

## Decisions

- Lock to pyEUVICS commit
  `70706d676dff071d31375093913812671f94aa80`, which contains both the
  31-link cleanup and the hardened empty-alt-image regression.
- Preserve the source publication manifest and its 54-file allowlist.
- Publish through the required pull-request and protected-main workflow.

## Outcome

- Updated `sources.lock.yml` from pyEUVICS commit `806b900…` to `70706d6…`.
- The locally assembled imported index renders excluded repository paths as
  non-clickable code and retains links only to approved content.
- PR #2 passed the required website validation and merged as
  `06477490f0bda0d4098c7e960dcf1b12e46115fc`.
- Pages run `33745388132` completed both artifact validation and deployment.
- An unsigned request to the live imported documentation returned HTTP 200,
  exposed provenance for `70706d6…`, and contained no hyperlinks to the
  excluded development, execution-plan, or legacy paths.

## Verification

- `.venv-docs-313/bin/python -m pytest -q`: 77 passed.
- Strict mypy: passed for 11 website assembly and deployment source files.
- `python -m mkdocs build --strict`: passed.
- `python -m tools.validate_ci` against exact detached source locks: passed
  both source publication contracts, 77 tests, strict typing, strict builds,
  assembly, final scans, and review-artifact hashing.
- Generated imported index inspection: excluded paths appear only as code;
  no excluded private-source hyperlinks remain.
- GitHub Actions run `33745118314`: required PR validation passed.
- GitHub Actions run `33745388132`: Pages build and deployment passed.
- Live unsigned HTTPS verification: HTTP 200 and source commit `70706d6…`.

## Progress

- [x] Update the pyEUVICS source lock.
- [x] Run website tests, strict typing, source assembly, and strict build.
- [x] Publish through a pull request and protected `main`.
- [x] Confirm the Pages deployment succeeds.
- [x] Verify the public imported documentation without authentication.
- [x] Record evidence and move this plan to completed sequence `028`.
