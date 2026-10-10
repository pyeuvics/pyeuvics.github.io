"""Suite-wide isolation for synthetic Git repositories."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    # Explicit fixture identities must not inherit user/CI overrides.
    import os
    for name in tuple(os.environ):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")) or name in {
            "GIT_CONFIG_COUNT", "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
            "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_DIR",
            "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CONFIG_PARAMETERS",
        }:
            monkeypatch.delenv(name)
