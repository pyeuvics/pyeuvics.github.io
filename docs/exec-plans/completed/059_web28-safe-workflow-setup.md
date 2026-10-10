# WEB-28 — Share setup without merging trust zones

## Scope
Extract only the common validation Python/cache/dependency setup into a small
local composite action. Keep source credentials, checkouts, residue checks,
conditional document tools, artifact upload and deployment explicit in jobs.
Centralize independently reviewed action pin expectations in test support.

## Decisions
The proposal writer retains its separate uncached Python/docs-only setup. That
duplication preserves a visible privilege boundary. The common action accepts
no tokens, permissions, environment or source parameters. Existing action pins,
job names, permissions, source-read/main guards and deployment protections stay.

Use [actionlint 1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12)
for local workflow syntax/expression/action checks. The official darwin/amd64
archive SHA-256 is 5b44c3bc2255115c9b69e30efc0fecdf498fdb63c5d58e17084fd5f16324c644;
it was verified before extraction. ShellCheck is not installed locally; do not
claim its separate shell analysis. No remote settings or workflows are run.

## Progress
Three validation jobs now use a small local composite action with no credential, permission, source or environment inputs. The proposal writer deliberately retains separate uncached setup. Centralized test policy retains existing reviewed action pins; three new structural cases check action contents, setup ordering, uncached writer setup and every workflow action. All 54 focused workflow checks and the complete shared quality command pass. Official actionlint 1.7.12, checksum verified before execution, passes all changed workflows; its core checks ran without the optional uninstalled ShellCheck analyzer. No remote settings, credentials, permissions, source locks or workflow runs changed.

## Verification
636 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
