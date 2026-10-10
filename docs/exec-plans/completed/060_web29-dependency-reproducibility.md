# WEB-29 — Explicit dependency layers and fresh environments

## Scope
Classify direct site, notebook, test and numerical dependencies. Move the core
PyYAML import to docs dependencies without changing its version. Add reviewed
transitive constraints from the already installed environment and fresh-install
validation. Bind dependency policy inputs in environment/staging evidence.
Record available document tool versions and TeX/font package reports.

## Decisions
Both source-only tests and full validation use the same Python declaration:
source-only tests include real synthetic notebooks and PDFs. Full approved PDF
builds additionally require the external document toolchain. The separate writer
uses docs dependencies plus the same constraints. Constraints restrict resolver
choices; they do not install inactive platform packages or promise a hermetic OS,
permanent package availability or permanent security. pip bootstrap is recorded
but not upgraded. Numerical pins and source policies are unchanged.

## Progress
Classified all direct dependencies, constrained 96 baseline packages, moved PyYAML into core docs requirements, and bound the five dependency declarations in staging and validation evidence. Fresh full and writer environments install successfully and pass pip check; writer imports and strict typing pass independently. Document tools report bounded version evidence before and after builds, withholding private paths and failing on drift. All 657 tests and shared quality checks pass in the fresh full environment. Actionlint passes workflow changes. No dependency upgrades, source policy changes, or remote operations occurred.

## Verification
657 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
