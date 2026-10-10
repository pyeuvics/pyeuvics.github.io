# Canonical validation requirement evidence

## Scope
Fix the post-pytest evidence failure in hosted run 38043236800 at c68492c.
The hosted run passed all 670 tests, source contracts, typing and strict builds,
then rejected its own validation record as an unordered evidence sequence.

## Diagnosis and acceptance
The dependency input catalog appended pyproject.toml after tools/dependency-policy.json.
Requirement fingerprints preserve catalog order, but evidence readers require
canonical sorted, unique pairs. Existing synthetic fixtures include only two
already-sorted requirements and missed the complete dependency profile.

Add a regression using all real dependency inputs; preserve rejection of
unordered/duplicate evidence. Canonicalize the fingerprint producer, retain
all input hashes, and run full quality, browser and exact locked-source validation.
Do not change source locks, publication approvals, dependencies or deployment.
No push is authorized for this maintenance fix.

## Progress
Implemented and verified. Requirement fingerprints are sorted by filename at
the producer; strict readers continue rejecting unordered or duplicate pairs.
The regression uses the complete repository dependency profile and checks every
input digest through the write/read round trip.

## Verification
- Hosted failure: [run 38043236800](https://github.com/pyeuvics/pyeuvics.github.io/actions/runs/38043236800),
  job 114187510574. All 670 pytest tests passed before the evidence failure.
- Before the fix: the complete-profile regression reproduced the same
  `ambiguous or unordered evidence sequence` error; 12 rejection cases passed.
- After the fix: 46 focused evidence and quality tests passed.
- Clean disposable website snapshot: `python -m tools.quality --bind` passed.
  All 673 pytest tests passed in 578.45 s; bounded lint, dependency policy
  (97 installed constrained packages), strict typing (67 source files), and
  the strict MkDocs scaffold build passed.
- `npm run test:browser` under Node 24: all 15 checks passed in 34.5 s.
  The first local attempt could not locate Chromium; the verified rerun used
  the already installed browser cache. No browser or website code changed.
- Complete `python -m tools.validate_ci` passed against clean checkouts at
  the unchanged source locks: EUVICS `63f605f585ec8f0c75147b478ea041aea24aa14c`
  and pyEUVICS `9117c843dcc9f1f47a6ced8d5144e94741314d3f`.
  This reused only the bound quality receipt from the same clean website
  snapshot and environment; it reran both source contracts, complete assembly,
  artifact scans, review manifest generation and final validation evidence.
  Its final record successfully round-tripped all six dependency input hashes.
- `git diff --check` passed. No source lock, scientific content, dependency pin,
  publication approval, workflow permission or deployment change was made.

## Outcome and hosted boundary
The exact post-pytest failure is resolved in local end-to-end validation.
The temporary snapshot was solely a verification fixture, not a release or
publication. No push or deployment was performed; hosted confirmation awaits
an authorized push and the subsequent GitHub Actions run.
