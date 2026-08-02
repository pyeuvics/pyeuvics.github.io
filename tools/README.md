# Website tools

`assemble_site.py` validates locked EUVICS and pyEUVICS checkouts, stages exact
allowlisted Markdown and ordinary assets, rewrites repository-relative links,
adds provenance, writes a deterministic inventory, builds MkDocs strictly, and
scans the final artifact.

```bash
SOURCE_DATE_EPOCH=1785628800 python tools/assemble_site.py \
  --euvics-source /path/to/clean/euvics \
  --pyeuvics-source /path/to/clean/pyEUVICS \
  --output .staging/review-build
```

The command refuses unresolved/mismatched locks, dirty checkouts, and an
existing output path. Production locks identify the reviewed source-contract
commits exactly. Later tasks add PDF builds and static notebook rendering; this
command intentionally handles neither.
