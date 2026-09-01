# Pull-request site validation

`.github/workflows/site-check.yml` validates proposed website changes without
deploying them. It runs for pull requests and manual validation dispatches only.
Its sole repository permission is `contents: read`; it has no Pages,
identity-token, environment, or deployment permission.

## Source checkout and credentials

The workflow reads repository names and full 40-character commits from
`sources.lock.yml`, then checks out EUVICS and pyEUVICS at those exact commits
with `persist-credentials: false`. Both repositories are private. Each has one
read-only deploy key, stored as a separate encrypted Actions secret because
GitHub does not permit one deploy key to be shared across repositories:
`EUVICS_SOURCE_DEPLOY_KEY` and `PYEUVICS_SOURCE_DEPLOY_KEY`. Each key grants
read access only to its named source repository and no access to other account
resources. Never expose either key through generated pages, logs, checkout
URLs, caches, or artifacts.

Pull requests from forks do not receive these secrets and therefore cannot run
the complete source-backed validation. A maintainer must review such changes
and run them from a trusted branch; the workflow must not be changed to
`pull_request_target` to make credentials available to untrusted code.

## Reproducible environment

CI uses Ubuntu 24.04, CPython 3.13, exact versions from
`requirements-docs.txt` and `requirements-notebooks.txt`, and a pip cache keyed
from both requirement files plus `sources.lock.yml`. CPython 3.13 matches the
supported pyEUVICS runtime; pyEUVICS excludes Python 3.14.

The EUVICS TeX toolchain is installed only when the locked publication manifest
contains an approved PDF. Source validators still run on every build.

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

## Review artifact

Successful runs upload only:

- the final static `site/` directory;
- `staged-content-inventory.json`;
- `review-artifact-manifest.json`.

The artifact is retained for seven days and is not a GitHub Pages artifact.
The workflow contains no deployment job or action.
