# WEB-23 — Route source and correction actions by ownership

## Scope
Provide explicit page ownership from the staging plan to the rendered theme.
Keep immutable source views and route correction proposals to the owning
repository. Never suggest editing generated Markdown in the website repository.

## Decisions
Source corrections open the source repository issue composer with the immutable
source reference as context; these links do not submit issues. Website-generated
pages point to their real website template/producer and website correction route.
Ordinary website pages retain the configured branch edit action. No mutable
source provenance or source approvals are introduced.

## Progress
Every generated Markdown output now supplies explicit ownership actions to the configured Material partial. Imported documents, rendered notebooks, PDF overviews and campaigns point to immutable source artifacts or manifests and source correction composers. Website-generated pages reference real templates/producers and website correction routes; ordinary website pages retain configured editing. Seven actual-theme rendering cases and strengthened complete document/notebook/staging integrations pass. No issue submission, source approval or source lock changes.

## Verification
532 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
