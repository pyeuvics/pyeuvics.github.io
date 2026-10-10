# WEB-15 — Complete staged and final artifact ownership

## Scope
Reconcile tracked website inputs, planned staged files, runtime notebook assets,
MkDocs page destinations, exact theme assets, static templates, search output and
sitemaps. Reject missing/extra paths, aliases and copied-byte drift. Preserve the
one internal canonical CSS alias. Bind static theme assets to installed package
RECORD hashes; declare generated output paths before invoking the builder.
Record a complete internal artifact manifest from the verified expected graph.

## Decisions
The pinned Material/MkDocs configuration currently has 43 theme asset files,
two static template outputs, one gzip sitemap and one search index. These are
explicit producer outputs, not a suffix/wildcard allowance. Generated HTML has
an owned staged input and recorded output checksum; this is ownership evidence,
not an arbitrary-host security sandbox or independent scientific approval.

## Progress
Complete ownership receipts bind tracked website inputs and admitted sources to staged files and declared MkDocs outputs. Installed theme files are checked against package RECORD hashes. Final verification rejects missing, extra, symlinked, or changed copied files and records checksums only after ownership succeeds. Nine regression cases include six reproduced failures. Generated HTML is traced to its declared input; this does not claim an independent HTML byte oracle or hostile-host sandbox.

## Verification
392 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
