# Automated source-lock pull requests

`.github/workflows/source-update.yml` proposes reviewed source-lock updates on a
weekly schedule or manual dispatch. It is proposal automation, not release
automation: it cannot merge its own pull request, alter a source publication
manifest, deploy directly, or replace exact commits with branch names.

## Trust and credential model

The workflow separates candidate evaluation from repository mutation:

1. `validate` has `contents: read` and `pull-requests: read` only. Every checkout
   uses `persist-credentials: false`. It may execute candidate source validators,
   document builds, and notebook renders, but has no repository write token.
2. `propose` runs only after validation succeeds. It receives a GitHub artifact
   containing the candidate lock and comparison report, not candidate source
   checkouts or executables. It checks out trusted website `main`, reverifies
   that only exact commits changed, commits only `sources.lock.yml`, and opens a
   pull request with `contents: write` and `pull-requests: write`.

The built-in `GITHUB_TOKEN` is sufficient and is scoped per job. No personal
access token, source credential, Pages permission, OIDC permission, secret, or
deployment environment is used. If source repositories become private, stop;
credential design requires separate explicit authorization and threat review.

## Candidate discovery and provenance

Discovery resolves each public repository's default `HEAD` with
`git ls-remote`. The returned value must be a full lowercase 40-character
commit. The workflow checks out that exact commit with complete history and
requires the current locked commit to be its ancestor. Rewinds, rewritten or
unrelated histories, invalid hashes, unavailable repositories, and ambiguous
responses fail closed.

The candidate lock is produced from the current strict schema by changing only
the two commit fields. Repository URLs, manifest paths, lock status, source
names, and schema cannot change. A no-change result exits without an artifact,
branch, pull request, or deployment.

Website tests must validate the lock schema, provenance behavior, ancestry, and
publication contracts without duplicating a currently locked commit as a test
constant. Exact commit pins belong only in `sources.lock.yml`; duplicating them
in tests would make a verified lock-only proposal fail for an unrelated website
change.

## Validation and artifact comparison

Both baseline and candidate locks run the complete `tools.validate_ci` path:

- validate source publication contracts;
- run the website tests and strict typing;
- build MkDocs strictly;
- build approved PDFs and render approved notebooks when applicable;
- assemble only allowlisted content;
- reject dirty/mismatched sources, unsafe links and paths, unknown files,
  credentials, excluded content, and nondeterministic notebooks;
- hash every review-artifact file.

The pull-request body records old/new commits and counts and lists added,
removed, and checksum-changed artifact paths. Baseline and candidate review
manifests are retained with the workflow evidence for seven days. Comparison is
bounded to 100 displayed paths per category; reviewers use the uploaded
manifests for a larger diff.

Candidate commits can legitimately change only provenance text and therefore
many HTML checksums. A successful comparison is evidence of reproducibility,
not scientific or publication approval.

## Duplicate and failure behavior

Only one source-update workflow runs at a time. An open automation pull request
or a remote proposal branch with no associated pull request prevents another
proposal. Branches retained after a closed or merged pull request do not block
future proposals. If pull-request creation fails after the branch is pushed, a
failure-only cleanup step deletes that new orphan branch while leaving
production locks unchanged. A cleanup failure is visible in the failed run and
must be resolved before another proposal.
Expected failure modes include:

- public source/default branch unavailable;
- candidate is not a descendant of the current lock;
- invalid or unapproved publication manifest;
- missing permissions, licenses, attribution, limitations, or files;
- PDF, notebook, link, test, type, strict-build, determinism, or scan failure;
- artifact comparison/package failure;
- an already open automated proposal;
- branch push or pull-request permission denied.

Do not weaken checks to make an update pass. Correct source problems in the
authoritative repository, review them there, and let the next run rediscover the
new exact commit.

## Reviewer workflow

An automated pull request must receive the same review as a manual lock update:

1. Confirm the source commit histories and publication-manifest approvals.
2. Review scientific status, limitations, CAIN discrepancies, permissions,
   licenses, attribution, document metadata, notebook policy, and campaigns.
3. Inspect the old/new artifact manifests and representative rendered changes.
4. Confirm the PR changes only `sources.lock.yml` and contains two exact hashes.
5. Require normal site validation. Automation is never an approving reviewer.
6. Merge only through protected `main`; the normal Pages workflow rebuilds from
   the merged exact locks and protected deployment rules.
7. Verify the deployed artifact signed out and retain run/commit provenance.

Proposal branches are named `automation/source-lock-update-<run-id>`. Close an
obsolete proposal before requesting a replacement; do not force-update a branch
under review.

## Rollback

Revert the lock-update commit through a reviewed pull request, restoring the
preceding exact commits. The protected Pages workflow then rebuilds and deploys
from those restored locks. Never copy a prior generated site, rewrite `main`,
or point production at a mutable branch as a shortcut. If an incident is
urgent, use the separately documented Pages environment controls while the
revert is validated.
