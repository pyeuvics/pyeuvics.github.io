# WEB-26 — Bind proposal evidence to validated inputs

## Scope
Record exact website bytes/revision, lock bytes/commits, environment, timestamp,
completed checks and artifact-manifest/ownership evidence after successful
validation. Verify the same bound evidence in the separate proposal write job.
Require explicit ancestry evidence and prevent reports claiming absent checks.

## Decisions
Evidence establishes consistency and integrity within the trusted workflow. It
is not scientific approval, a signature, or authentication against a compromised
validator. Website inputs must be clean and match every tracked Git blob, even
when assume-unchanged hides edits. Environment evidence fingerprints installed
distribution files, requirements, package versions and the interpreter; generated
Python caches are excluded. Compare before/after execution. Baseline/candidate
records must agree on website, environment and epoch. No actual remote proposal,
source lock update, credential or permission change is performed.

## Progress
Validation now checks website, lock and environment identity before and after execution, then records completed checks and ownership evidence alongside the review manifest. Proposal packages bind both records, manifests, ancestry, report, complete comparison and candidate lock. The write job verifies this package before copying the candidate lock. Thirty-one new tests cover tampering, malformed/missing checks, mixed/stale inputs, hidden website edits, changed installed files, report claims and workflow order. One real local environment fingerprint covered 97 packages in 20.94 seconds. This is consistency/integrity evidence, not scientific approval or authentication of a compromised validator. No remote writes, source lock changes or permission changes.

## Verification
622 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
