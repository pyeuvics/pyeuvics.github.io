# Pull-request site validation

`.github/workflows/site-check.yml` validates proposed website changes without
deploying them or reading private sources. It runs for pull requests and manual
dispatches. Its sole repository permission is `contents: read`; it has no
private credential, Pages, identity-token, environment, or deployment access.

## Source checkout and credentials

Pull-request validation checks out only the website revision, installs pinned
dependencies, and runs dependency policy, pytest, strict mypy, a strict MkDocs
build, and local Chromium behavior checks. It does
not mint a GitHub App token, check out either private source, upload a
source-derived artifact, or reference any Actions secret. This alone does not
protect repository secrets from a modified same-repository PR workflow. The
App key must exist only in the `source-read` environment, restricted to the
`main` branch as described in [github_app.md](github_app.md).

Complete source-backed validation runs only in trusted default-branch or
main-branch manual workflows: `.github/workflows/pages.yml` and
`.github/workflows/source-update.yml`. Those workflows use the GitHub App
described in [github_app.md](github_app.md), exact source locks, non-persisted
checkout credentials, and a fail-closed runner credential scan.

## Reviewed environment and reproducibility limits

CI uses Ubuntu 24.04 and Python 3.13. `requirements-validation.txt` combines the
direct declarations with `constraints-validation.txt`, which records reviewed
transitive versions without upgrading numerical pins. The pip cache is an
optimization, not evidence of a fresh installation. See
[Dependency and toolchain policy](dependency-policy.md) for dependency roles,
fresh-install checks, installed-file fingerprints, and the separate external
TeX/font/toolchain layer. This is not a hermetic OS or a permanent security claim.

Trusted workflows install document tools only when the locked manifest exposes
PDF candidates; approval and exact rebuilt PDF byte checks remain separate.
Pull-request checks build only synthetic document fixtures.

## Local-equivalent validation

Use the [development and validation runbook](development.md) for copyable
commands. `python -m tools.quality` is the shared Python quality entry point;
`npm run test:browser` is the separately recorded browser layer in the required
PR job. `python -m tools.validate_ci` additionally validates locked source
contracts, assembles and checks the complete artifact, and emits review and
validation evidence. Local edited-tree quality results cannot be reused as
bound CI receipts. Trusted baseline/candidate quality reuse requires exact
website/environment/time/policy equality and never skips source-specific gates.

## Trusted review artifact

The source-update workflow uploads the candidate lock, comparison report, and
baseline/candidate review manifests for seven days. It does not upload either
rendered site. The Pages workflow uploads only its validated static site as a
Pages artifact for one day; that site includes the staged-content inventory.
Pull-request validation uploads no artifact.
