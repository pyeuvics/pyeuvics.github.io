# WEB-16 — Format-aware public asset validation

## Scope
Inspect imported SVG, CSS, JSON/maps, YAML, PDF and raster assets before copying;
inspect final owned assets including compressed sitemap output. Preserve bytes.
Keep trusted website/theme scripts separate from imported active content.

## Decisions
Bound each file to 32 MiB, decompressed text to 8 MiB, structured traversal to
100,000 nodes / 64 levels, images to 20 million decoded pixels, and PDF work to
30 seconds with per-stream and aggregate decode limits in an isolated process.
Pin already installed Pillow 12.3.0 and defusedxml 0.7.1 as direct dependencies.
Reject unsupported encodings/formats and source asset references whose original
relative route is not preserved. PDF inspection rejects active actions,
attachments and unsupported stream filters; normal navigation is permitted.
These checks cannot certify scientific approval, copyright, figure permission,
or sensitive information visible only in raster pixels. Human publication and
image review remains required. No source lock or publication approval changes.

## Progress
Format-aware inspection runs before copying source assets and on every owned final non-HTML artifact. SVG/CSS references must resolve to admitted unchanged-route resources; active source scripts, PDF actions and attachments, malformed formats, hidden paths, and excessive decoded payloads fail closed. PDF decoding runs in a disposable process with a 30-second timeout and restricted filters. Thirty-seven added cases cover adversarial payloads, exact-byte preservation, Matplotlib-style SVG compatibility, and pre-render admission enforcement. The full synthetic site asset pass took 2.759 seconds locally. Raster pixels still require human privacy/rights review; structural checks do not establish publication or scientific approval.

## Verification
429 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
