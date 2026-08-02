# Website tools

`assemble_site.py` validates locked EUVICS and pyEUVICS checkouts, stages exact
allowlisted Markdown and assets, rewrites repository-relative links, adds
provenance, writes a deterministic inventory, builds MkDocs strictly, and scans
the final artifact.

An EUVICS Proposal or CDR PDF is published only when its exact canonical build
path and complete release metadata are approved by the locked source manifest.
Assembly exports the locked source to a disposable directory, removes the
tracked PDF baseline there, runs `make verify-archive` and `make check`, rejects
unresolved-reference log markers, and requires the rebuilt PDF's SHA-256 to
match the approved source artifact. It then generates the document overview and
stages the PDF; no LaTeX source is converted to website Markdown.

Approved pyEUVICS notebooks are exported from the locked commit to disposable
staging, checked for empty source outputs, explicit data dependencies, size,
local paths, credentials, and network-dependent code, then executed twice with
a bounded local Jupyter kernel. Assembly accepts only byte-identical static
Markdown and assets from both executions and verifies that neither the real nor
temporary source tree changed. Every page records package/source provenance,
execution policy, seed/configuration, validation status, local requirements,
and limitations. Approved campaign Markdown and figures use the same exact-file
allowlist and replace placeholders only when a complete approved set exists.

```bash
SOURCE_DATE_EPOCH=1785628800 python tools/assemble_site.py \
  --euvics-source /path/to/clean/euvics \
  --pyeuvics-source /path/to/clean/pyEUVICS \
  --output .staging/review-build
```

The command refuses unresolved/mismatched locks, dirty checkouts, an existing
output path, and incomplete or non-reproducible document releases. Production
locks identify the reviewed source-contract commits exactly. Pending or blocked
notebook/campaign candidate sets remain excluded.
