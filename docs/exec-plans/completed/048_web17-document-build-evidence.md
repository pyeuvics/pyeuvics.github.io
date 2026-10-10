# WEB-17 — Separate document build and evidence

## Scope
Separate release metadata admission, required build interface, disposable build,
bounded command/log evidence, byte verification and publication rendering.
Rename CI's raw PDF-presence output to pdf_candidate: installing a toolchain
must not imply release approval. Preserve exact rebuilt/approved checksums.

## Decisions
Use the source-owned make verify-archive/check interface. Require Make and a
regular source Makefile for an admitted document set; do not infer arbitrary
LaTeX engines or loosen byte identity to accommodate a different toolchain.
Record typed command and log checksums and tool path internally, never publish
raw build logs. Cap each log at 8 MiB and all log evidence at 32 MiB/256 files.
Separate no-PDF preflight from Proposal/CDR build requirements. No private
source build, source-lock change, or hosted settings update is authorized here.

## Progress
DocumentRequirements validates release metadata and the source-owned Make interface before building. DocumentBuildResult carries verified PDF bytes and bounded log/command checksums; publication rendering consumes that result. Sources are checked before and after the disposable build, and unapproved build artifacts never enter the published inventory. CI reports pdf_candidate for raw PDF presence and both toolchain consumers use that output. Ten added cases cover zero/Proposal/CDR/both releases, bad dates, missing Make, invalid/oversized/aliased logs, exact evidence and source immutability. Existing build, output, checksum and publication failure cases remain enabled.

## Verification
439 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
