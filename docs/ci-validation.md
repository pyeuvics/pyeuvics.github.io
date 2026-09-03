# Pull-request site validation

`.github/workflows/site-check.yml` validates proposed website changes without
deploying them or reading private sources. It runs for pull requests and manual
dispatches. Its sole repository permission is `contents: read`; it has no
private credential, Pages, identity-token, environment, or deployment access.

## Source checkout and credentials

Pull-request validation checks out only the website revision, installs pinned
dependencies, and runs pytest, strict mypy, and a strict MkDocs build. It does
not mint a GitHub App token, check out either private source, upload a
source-derived artifact, or reference any Actions secret. This protects the App
private key from both forks and same-repository feature branches.

Complete source-backed validation runs only in trusted default-branch or
administrator-controlled workflows: `.github/workflows/pages.yml` and
`.github/workflows/source-update.yml`. Those workflows use the GitHub App
described in [github_app.md](github_app.md), exact source locks, non-persisted
checkout credentials, and a fail-closed runner credential scan.

## Reproducible environment

CI uses Ubuntu 24.04, CPython 3.13, exact versions from
`requirements-docs.txt` and `requirements-notebooks.txt`, and a pip cache keyed
from both requirement files plus `sources.lock.yml`. CPython 3.13 matches the
supported pyEUVICS runtime; pyEUVICS excludes Python 3.14.

The complete trusted workflow installs the EUVICS TeX toolchain only when the
locked publication manifest contains an approved PDF. Pull-request validation
does not build private-source documents.

## Local-equivalent validation

Create a Python 3.13 virtual environment, install the two pinned dependency
sets, then run the same entry point used by CI:

```bash
python3.13 -m venv .venv-docs-313
source .venv-docs-313/bin/activate
python -m pip install -r requirements-docs.txt -r requirements-notebooks.txt

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

Successful source-backed trusted runs upload only:

- the final static `site/` directory;
- `staged-content-inventory.json`;
- `review-artifact-manifest.json`.

The artifact is retained for seven days. Pull-request validation uploads no
artifact; the Pages workflow uploads only its separately validated Pages
artifact.
