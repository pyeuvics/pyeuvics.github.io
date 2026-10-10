# WEB-19 — Explicit notebook kernel and environment provenance

## Scope
Create an owned kernel spec backed by the invoking virtual-environment Python;
isolate kernel/config/runtime caches and record interpreter, package, source
and requirement fingerprints. Validate declared source environment policies.
Describe Python hash seeding separately from scientific RNG seeding; inject no
scientific seed code. Retain independent real execution twice.

## Decisions
Use explicit jupyter_client kernel selection with no native/global fallback and
explicit client cleanup. Pin already installed jupyter_client 8.9.1 and packaging
26.3 as direct dependencies without upgrades. Fingerprints contain hashes and
versions, never machine-specific absolute paths. They describe the selected
trusted execution environment, not a hostile-code security attestation.
Only declared environment.yaml/yml configuration records define frozen source
numerical policies. The locked real source currently requests NumPy 2.5.2;
the website pins 2.5.1, and real notebook publication remains approval-pending.
Do not alter either approval or pins: admitted mismatches must fail explicitly.

## Progress
Every real execution uses an owned publication kernel backed by the invoking virtual environment, with explicit cleanup and isolated kernel/config/cache directories. Version and installed RECORD fingerprints, interpreter bytes, website requirement hashes, source tree and declared frozen environment policies are recorded without machine paths. Both executions must match their environment and outputs. Public notebook provenance includes the environment fingerprint and precise seed semantics; no scientific seed code is inserted. Seven added tests include a real hostile-global-kernel case, cleanup, source immutability, dependency mismatch, source policy version checks and seed bounds. The pending real source policy requires NumPy 2.5.2 while website pins remain 2.5.1: this is recorded, not silently upgraded or approved. No source lock, scientific approval, or installed package changes.

## Verification
462 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
