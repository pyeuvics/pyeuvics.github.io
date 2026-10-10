# Bounded code quality and local files

Invoke Python CLIs as modules: `python -m tools.<name>`. Python tooling files
remain Git mode 100644 and have no executable-script shebang. Documentation and
workflows follow this convention. There is no package/runtime build change.

`pyproject.toml` fixes Python 3.13 typing for `tools` and `tests/support`, and
Ruff 0.17.0 checks only import ordering (`I`), syntax errors (`E9`), invalid
comparisons/flow (`F63`, `F7`), undefined-name families (`F82`), and shebang/mode
consistency (`EXE001`). The shared
`python -m tools.quality` command checks these exact targets with no Ruff cache.
Strict mypy covers the same maintained typed boundary. Test bodies deliberately
construct malformed data; this task does not impose strict typing on every test.
No all-rules lint policy, broad formatter, line-length rewrite, or scientific
calculation cleanup is included.

Ruff is an exact development dependency with a matching transitive constraint.
Changing quality policy invalidates reusable quality receipts. All tracked
website bytes bind a receipt; the project configuration is additionally part
of declared dependency/staging inputs. See [Ruff configuration](https://docs.astral.sh/ruff/configuration/)
and [dependency policy](dependency-policy.md) when reviewing updates.

Virtual environments, Python/tool caches, Node dependencies, coverage reports,
site output, staging and external source checkouts stay untracked. The root
`/downloads/` build-output rule does not ignore `content/downloads/`. Existing
local historical exclusions were narrowed to their exact `docs/` paths; their
files are preserved and are not part of this refactoring commit. Dated review notes are never hidden by a new ignore rule. Do not broaden
patterns to hide source assets, intended downloads, or unexplained files.
