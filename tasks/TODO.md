# TODO

Outstanding, non-blocking cleanup items. None of these affect
`pytest`, `mkdocs build --strict`, or `mypy tools`, which all pass.

- [ ] Sort imports in `tests/test_ci_validation.py` and
      `tests/test_source_assembly.py` (`ruff check --fix`).
- [ ] Resolve `EXE001` (shebang present but file not executable) on
      `tools/assemble_site.py`, `tools/ci_source_locks.py`,
      `tools/source_update.py`, `tools/validate_ci.py`, and
      `tools/verify_runner_credentials.py` — either `chmod +x` each file or
      drop the shebang line, since these are invoked via `python -m tools.x`,
      not executed directly.
