# WEB-35 — Bounded lint, typing and local-file hygiene

## Scope
Add exact Ruff tooling for import order and a small correctness rule set, retain
strict tool/test-support typing, use module invocation and non-executable file
modes, and consolidate cache/output ignores. No broad formatting or numerical
upgrades. Bind the project policy in quality/staging evidence.

## Progress
Added Ruff 0.17.0 with only I/E9/F63/F7/F82/EXE001 rules, Python 3.13 strict typing for tools/test support, and explicit pytest targets. Shared quality policy v3 includes a required lint gate; two regressions prove lint failures stop later stages. Bound pyproject.toml in dependency/staging inputs. Sorted imports and removed CLI shebangs while retaining mode 100644; 55 import/shebang-only files have identical non-import ASTs. Cache-ignore probes preserve intended website downloads, assets and review notes. Existing local historical exclusions were narrowed to exact docs paths without editing or staging those files. Full and writer isolated environments satisfy declarations and pip check (97/85 constrained packages). All 657 Python tests, 15 Chromium checks, lint, strict typing/build and whitespace checks pass. No numerical/source-policy upgrades or remote operations.

## Verification
657 passed; strict mypy and strict MkDocs build passed.
Whitespace checks passed. No push or source-lock update.
