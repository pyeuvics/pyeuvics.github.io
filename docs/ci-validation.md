# Pull-request site validation

`.github/workflows/site-check.yml` validates proposed website changes without
deploying them or reading private sources. It runs for pull requests and manual
dispatches. Its sole repository permission is `contents: read`; it has no
private credential, Pages, identity-token, environment, or deployment access.

## Source checkout and credentials

Pull-request validation checks out only the website revision, installs pinned
dependencies, and runs pytest, strict mypy, and a strict MkDocs build. It does
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

Create a Python 3.13 virtual environment and run the shared source-only checks:

```bash
python3.13 -m venv .venv-docs-313
source .venv-docs-313/bin/activate
python -m pip install -r requirements-validation.txt
python -m pip check
python -m tools.quality
```

For a trusted source-backed review, use clean locked source checkouts and a clean
website revision:

```bash

python -m tools.validate_ci \
  --euvics-source /path/to/locked/euvics \
  --pyeuvics-source /path/to/locked/pyEUVICS \
  --output .staging/local-ci-review
```

The command refuses existing output paths. Unless `SOURCE_DATE_EPOCH` is
provided, it derives the build timestamp from the checked-out website commit.
It validates both source manifests, runs pytest and strict mypy, builds the
website scaffold strictly, assembles and scans the complete locked-source site,
and writes `review-artifact-manifest.json` with a SHA-256 checksum and byte size
for every uploaded file.

## Trusted review artifact

The source-update workflow uploads the candidate lock, comparison report, and
baseline/candidate review manifests for seven days. It does not upload either
rendered site. The Pages workflow uploads only its validated static site as a
Pages artifact for one day; that site includes the staged-content inventory.
Pull-request validation uploads no artifact.
