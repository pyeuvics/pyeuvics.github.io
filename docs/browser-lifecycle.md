# Browser lifecycle and equation delivery

The current Material feature list uses full-page navigation. Instant navigation
is not enabled. The navigation controller initializes at DOM readiness and on
`pageshow`, and subscribes once to Material's `document$` for preventive support
of future page replacement. Each initialization aborts old DOM listeners. Script
reevaluation disposes the prior controller and subscription. Enter/Space toggle
the drawer; Escape closes it and restores focus; checkbox changes synchronize
its accessible name and expanded state.

MathJax configuration is loaded before its engine. Its `pageReady` callback
starts serialized asynchronous typesetting, so early Material events cannot
lose initial equations or overlap rendering. Later document events use the same
queue, tracking successfully rendered equation nodes in a weak set to avoid
duplicate output, clearing references to a replaced content root and resetting equation
numbers. Repeating initialization does not create another subscription. A script
load failure or rejected typeset operation shows a short accessible status
message; original TeX is preserved when loading fails. A later successful render
removes the message. Error details are not copied into public page content.

## Reviewed delivery decision — 2026-10-10

Retain the existing jsDelivr delivery policy, now pinned to **MathJax 3.2.2**
instead of the mutable major `@3` URL. This is a compatibility pin, not a claim
that version 3 is current; moving to version 4 needs a separate equation and
accessibility review. No scientific math source or CSP setting changed. CDN
availability and CDN-served bytes remain external dependencies; exact version
pinning alone is not offline delivery or subresource integrity.

MathJax is Apache-2.0 licensed. The upstream package retains its license and
notices. Review the [3.2.2 release](https://github.com/mathjax/MathJax/releases/tag/3.2.2),
[license](https://github.com/mathjax/MathJax/blob/3.2.2/LICENSE),
[startup documentation](https://docs.mathjax.org/en/v3.2/web/configuration.html)
and [typesetting lifecycle](https://docs.mathjax.org/en/v3.2/web/typeset.html)
when updating the pin. Keep configuration, failure detection, offline browser
test package, and tests on the same version; review license changes and compare
representative equations before changing delivery or upgrading.
