# Stylesheet ownership

Edit `docs/stylesheets/readthedocs.css` only. The tracked
`content/stylesheets/readthedocs.css` symlink points to it; do not replace the
symlink with a synchronized copy. MkDocs registers that served path. Scaffold
builds follow the alias and source assembly admits only this exact alias,
records its canonical bytes and verifies the final stylesheet byte-for-byte.

The single stylesheet is ordered as tokens and base typography, shared layout
and components, desktop navigation, compact drawer, narrow overflow, reduced
motion and print. Component defaults precede responsive overrides. The narrow
schematic intentionally stays readable at 52rem inside its own scrolling
paragraph; print restores page-width figures. Tables and equations scroll in
local containers. The two-color focus indicator remains visible against light
content and the dark navigation surface.

`content/stylesheets/extra.css` was an unregistered historical stylesheet:
repository consumer search found no configuration, template or script loading
it. It has been removed; its history remains in Git. Do not restore it as a
second source of design tokens. Browser behavior evidence is maintained with
the frontend checks; CSS string presence alone is not visual acceptance.
