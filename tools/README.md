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

```bash
SOURCE_DATE_EPOCH=1785628800 python tools/assemble_site.py \
  --euvics-source /path/to/clean/euvics \
  --pyeuvics-source /path/to/clean/pyEUVICS \
  --output .staging/review-build
```

The command refuses unresolved/mismatched locks, dirty checkouts, an existing
output path, and incomplete or non-reproducible document releases. Production
locks identify the reviewed source-contract commits exactly. Static notebook
rendering remains outside this command for now.
