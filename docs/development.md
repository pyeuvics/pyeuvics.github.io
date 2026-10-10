# Website development and validation runbook

Reviewed against the maintained entry points and workflows on **2026-10-11**.
Run commands from the website repository root. A successful check is evidence
for review; it grants no scientific approval or permission to publish.

## Prepare the environment

```bash
python3.13 -m venv .venv-docs-313
source .venv-docs-313/bin/activate
python -m pip install -r requirements-validation.txt
python -m pip check
```

Virtual environments contain absolute checkout paths and must be recreated
when the checkout is moved or renamed. Activating an old environment can select
a stale interpreter even when its directory is still present. Preserve or remove
the old environment first, then create a fresh Python 3.13 environment using the
commands above; copying an existing environment does not repair its launchers.
Do not reuse a Python 3.14 environment for this validation setup.

Confirm the active interpreter and dependency pins before running pytest:

```bash
python -c "import sys; print(sys.executable); print(sys.version)"
python -m tools.dependencies
python -m pytest -v tests
```

Notebook provenance also requires installed package `RECORD` metadata. An
environment created with `--system-site-packages` can pass version checks yet
inherit global packages without this metadata. Identify the affected
distributions before repairing them; install wheels of the same pinned versions
locally in the virtual environment without changing global packages. Do not
bypass the provenance check or change numerical pins to silence this error.

The reviewed website numerical pins are NumPy 2.5.3 and SciPy 1.18.1.
The YAML typing stubs are pinned to 6.0.12.20260906.
Both `requirements-notebooks.txt` and `constraints-validation.txt` declare them.
A shared pyEUVICS interpreter must also satisfy every other website pin and
provide complete installed-file metadata. These patch upgrades do not revise
frozen source environments: an admitted notebook declaring older exact versions
still fails validation and requires a separately reviewed source update.

The same declared Python environment runs source-only synthetic checks and
source-backed assembly. Approved document builds additionally need the source's
TeX/font/toolchain packages. See [dependency policy](dependency-policy.md) for
roles, constraints, fresh installation and toolchain evidence. Do not upgrade
numerical packages merely to make a source execution policy pass.

## Preview the website shell

```bash
python -m mkdocs serve
```

This previews `content/` and theme overrides with placeholder sections. It does
not import source material, approve content, or represent a production assembly.
The canonical stylesheet is documented in [stylesheet ownership](stylesheet-ownership.md).

## Validate edited website code without source credentials

```bash
python -m tools.quality --output .staging/local-quality
```

Choose a new output path for each run. The shared command checks dependency
policy, bounded lint, the full synthetic Python test suite (including real fixture notebooks
and PDF checks), strict typing for tools and test support, and a strict scaffold
build. An edited-tree result is deliberately not a reusable CI attestation.
`--bind` additionally requires a clean website checkout and records exact
website/environment identities for narrow reuse by source-update validation.

With Node 24 installed, run the separate browser layer:

```bash
npm ci --ignore-scripts
npx playwright install chromium
npm run test:browser
```

Fresh Linux runners need `--with-deps` on the browser installation command.
[Frontend checks](frontend-checks.md) describes the disposable local fixtures,
network isolation, coverage and release-review limits. The required
`Validate website source` PR job runs both Python and browser checks without
private-source reads, secrets or deployment permissions.

## Assemble exact locked sources for local review

Provide clean source checkouts at the exact commits in `sources.lock.yml`.
Replace the example paths with your local checkouts; do not commit those paths.

```bash
SOURCE_DATE_EPOCH=1785628800 python -m tools.assemble_site \
  --euvics-source /path/to/locked/euvics \
  --pyeuvics-source /path/to/locked/pyEUVICS \
  --output .staging/local-assembly
```

This example fixes the timestamp for repeatability; select the reviewed epoch
for a real review and keep it identical across comparisons. Assembly rejects an
existing output directory, dirty/mismatched sources, unapproved inputs and
unsafe artifacts. It exports exact Git blobs into disposable workspaces,
requires exact rebuilt PDF bytes, executes approved notebooks twice and
verifies the entire final artifact. Failed output is never promoted; retained
incomplete workspaces are diagnostic evidence, not releasable sites. The final
public tree is `OUTPUT/site/`; sibling plans/receipts are internal evidence.

For complete trusted validation, start from a clean website revision:

```bash
python -m tools.validate_ci \
  --euvics-source /path/to/locked/euvics \
  --pyeuvics-source /path/to/locked/pyEUVICS \
  --output .staging/local-source-review
```

This validates both source contracts independently, runs shared Python quality,
assembles and verifies the artifact, and records review and validation evidence.
Without `SOURCE_DATE_EPOCH`, it uses the website commit time. It does not push,
open a PR, or deploy. Browser quality is separately recorded by the frontend
suite; the Python quality receipt does not assert that browsers ran.

## Review a source-update proposal

The trusted source-update workflow discovers descendants of the current locks,
creates a candidate lock changing only commit fields, validates baseline and
candidate independently, and compares typed artifact manifests. Candidate
validation can reuse only the baseline's bound **website-only quality** receipt
when website bytes, environment, dependencies, epoch and policy match exactly.
It never skips source validation, approved PDF/notebook work, or artifact scans.

The proposal package binds ancestry, both validation records, both review
manifests, exact candidate lock and comparison report. The separate writer
verifies that evidence before copying the lock and touching a managed branch.
A manifest diff alone is neither proof of repeatability nor a validation claim.
See [source-update automation](source-update-automation.md) and
[workflow boundaries](workflow-boundaries.md). Manual helper options can be
inspected safely with `python -m tools.source_update --help`; mutation requires
its separately authorized workflow scope.

## Deployment and release review

[Pages deployment](pages-deployment.md) documents the protected default-branch
workflow, administrator controls and rollback. Source-read credentials,
proposal-write credentials and Pages deployment remain separate trust zones.
PR checks never confer deployment or publication approval. Do not dispatch,
push, change settings, credentials or source approvals as a side effect of a
local refactoring task. Review the actual deployed revision signed out before
release and retain that evidence separately from local browser results.

## Approval snapshot, not an evergreen claim

At the locks reviewed on **2026-10-10** (exact values remain solely in
`sources.lock.yml`), the recorded EUVICS state has no approved PDF releases;
pyEUVICS notebook sets are approval-pending and campaign sets blocked. The
approved exact-linear overview figure remains allowlisted. These statements
summarize the reviewed lock state, not future source heads or release approval.
Read the locked manifests and their approval metadata again for every update.
Scientific corrections and release decisions belong in the authoritative source
repositories; website placeholders are replaced only by complete approved sets.
