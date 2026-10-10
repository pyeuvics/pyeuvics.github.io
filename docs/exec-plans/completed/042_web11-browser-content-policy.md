# WEB-11 — Explicit browser content and resource policy

## Scope
Distinguish navigation, image and other resources. Reject base/meta mutation,
executable/unsupported elements and attributes, duplicate attributes, dangerous
encoded schemes, active CSS, malformed resources and HTML/SVG data URLs.
Preserve inert math, reviewed raster data, images and static SVG references.
Apply the same policy to notebook Markdown and rendered notebook bodies.

## Dependency decision
Declare tinycss2 1.5.1 (already installed transitively) as a direct exact pin.
A real CSS tokenizer is needed to interpret comments, escaped identifiers and
URL values. No environment upgrade is involved. Support bounded declarations
and a reviewed function/property subset; reject stylesheets, at-rules, custom
properties, unknown functions and malformed syntax. This is a publication
subset, not a general browser sanitizer or arbitrary-code sandbox.

## Progress
Twenty-two reproduced failures are resolved. Explicit element/attribute policy
rejects base/meta mutation, duplicate attributes, executable/unsupported SVG and
HTML, unsafe encoded schemes, and HTML/SVG data URLs. Raster data requires a
matching signature. tinycss2 1.5.1 is now a direct exact dependency without an
upgrade; CSS comments, escapes, URLs, reviewed declarations/functions and bounded
nesting use its parser. Unsupported stylesheets/at-rules/functions fail closed.
Escaped CSS destinations remain compatible with source-span mapping. Shared
policy also inspects notebook Markdown and rendered output. Forty-two synthetic
hostile/benign and notebook cases cover these boundaries. The existing private
form-target test now expects rejection at the earlier explicit element boundary.

## Verification
312 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
