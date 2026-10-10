# WEB-30 — Single stylesheet ownership and ordered layout

## Scope
Remove the unregistered obsolete stylesheet, document the canonical alias,
group component defaults before responsive overrides and share repeated color
tokens without splitting the file. Preserve print and reduced-motion rules.

## Decisions
Repository-wide consumer search found extra.css only as an unused file. Moving
figure defaults before media rules repairs the formerly overridden 52rem mobile
schematic rule. Add a dark outer focus ring to support the existing gold ring
on light content. Browser verification follows in WEB-32.

## Progress
Confirmed no consumers of extra.css and removed it. Documented one canonical CSS source, shared repeated colors, moved figure defaults ahead of narrow-screen rules, and added a dark outer focus ring. Existing scaffold and assembled ownership checks verify the exact CSS alias and final bytes. All 657 tests and full quality checks pass. Actual responsive and accessibility browser evidence follows in WEB-32.

## Verification
657 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
