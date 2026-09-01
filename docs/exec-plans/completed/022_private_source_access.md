# Private source access and lock resolution

## Scope

Keep the authoritative EUVICS and pyEUVICS repositories private while allowing
the public website repository to validate exact locked commits, deploy approved
content, and propose reviewed source-lock updates. Resolve approved PR `#1`
after private-source CI is operational.

## Boundaries

- Use one read-only deploy key per private source repository; grant no write
  access and no access to other repositories.
- Store private keys only as encrypted Actions secrets in the website
  repository. Never print, artifact, cache, or persist them in checkouts.
- Preserve exact commit locking, publication manifests, validation, and the
  protected Pages deployment path.
- Do not change scientific content or publication approvals.

## Progress

- [x] Configure repository-scoped read-only deploy keys and encrypted secrets.
- [x] Update all source checkouts and authenticated candidate discovery.
- [x] Add regression coverage and documentation.
- [x] Run local and GitHub validation, including a protected deployment.
- [x] Update, validate, and resolve PR `#1`.
- [x] Record evidence and complete this plan.

## Verification evidence

- GitHub records deploy keys `162005464` and `162005465` as read-only on
  `chongshikpark/euvics` and `chongshikpark/pyEUVICS`, respectively. The
  website repository stores their private halves only as encrypted secrets
  `EUVICS_SOURCE_DEPLOY_KEY` and `PYEUVICS_SOURCE_DEPLOY_KEY`; temporary local
  key files were deleted immediately after configuration.
- Focused Python 3.13 checks passed: 17 workflow/source-update tests, strict
  mypy for `tools/source_update.py`, Ruff for affected Python files (with the
  repository's pre-existing executable-shebang diagnostic excluded), strict
  MkDocs, and `git diff --check`.
- The sandboxed full suite reported 71 passes and the three expected notebook
  socket failures. All seven notebook execution/failure-path cases passed when
  rerun outside the socket-restricted sandbox.
- Private-source access PR `#4` passed site-validation run `33572018171` and
  merged as `a666214843e42959706df9dcc94c75ce4c749058`. Protected Pages run
  `33572138570` checked out both private sources, validated the exact public
  artifact, and deployed successfully.
- Approved source-lock PR `#1` was updated to the credential-enabled main tip
  and passed private-source validation run `33572268990`. It merged as
  `1e60bec823f2acbb57f46dd942035c4b4b6274ce`; its completed automation branch
  was deleted. Protected Pages run `33572376144` validated and deployed the new
  exact locks successfully.
