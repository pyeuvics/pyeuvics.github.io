# WEB-22 — One approved publication view

## Scope
Bind entry pages, section indexes and restricted downloads to the immutable
staging plan. Replace implicit append/heading insertion with explicit slots.
Keep scaffold states separate from assembled availability.

## Decisions
Only verified approved PDF document releases are listed in Downloads. Imported
data and notebook outputs remain accessible through their reviewed context,
not an automatic download directory. Metadata and checksums come from the same
planned entries and verified staged inventory. No scientific calculation,
publication approval or source lock changes.

## Progress
The staging plan now records a root-free immutable publication view used by entry sections, campaign overviews and document/notebook/campaign/download indexes. Downloads deliberately list only verified PDF releases with matching receipts and full metadata. Website prose uses explicit repeatable availability, provenance and figure slots. Eight added tests cover no approvals, partial and full synthetic approvals, missing/tampered PDF receipts, malformed slots and byte-identical repeat generation. Existing full synthetic document/notebook assemblies pass. No source lock or approval changes.

## Verification
525 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
