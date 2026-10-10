# Website architecture

These documents define the website structure and review language for the
EUVICS documentation website at `https://pyeuvics.github.io/`.

- [Information architecture](information-architecture.md) defines navigation,
  page responsibilities, and provenance links.
- [Status vocabulary](status-vocabulary.md) defines controlled labels and the
  evidence required to display them.
- [Review checklists](review-checklists.md) defines accessibility, content,
  provenance, and scientific review gates.

This directory contains website-owned architecture and review guidance, not approved
scientific content. The `pyeuvics/euvics` and `pyeuvics/pyEUVICS`
repositories remain authoritative. A page or asset becomes publishable only
when a versioned source manifest allows it and the website build uses the
locked source commit.

## Implemented and remaining owner decisions

- The scaffold and explicit navigation are implemented in `mkdocs.yml`; use
  [current work](../current-work.md) and the [runbook](../development.md). The
  original before-scaffold navigation placeholder is historical.
- Identify the owner authorized to assign document release and validation
  states in each source repository.
- Approve any future branding, logo, affiliations, contact details, and custom
  domain separately. None is defined here.
