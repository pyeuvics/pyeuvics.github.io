from __future__ import annotations


import pytest

from tools.site_assembly import (
    AssemblyError,
)
from tools.site_assembly.pipeline import (
    _scan_text,
)




@pytest.mark.parametrize("text", [r"C:\Users\fixture\private.txt", r"C:\\Users\\fixture\\private.txt", "C:/Users/fixture/private.txt", "github_pat_" + "A" * 30])
def test_artifact_scan_rejects_windows_paths_and_fine_grained_tokens(text: str) -> None:
    with pytest.raises(AssemblyError, match="local absolute path|credential-like"):
        _scan_text(text, "fixture")


def test_artifact_scan_accepts_web_urls_and_drive_name_documentation() -> None:
    _scan_text("https://pyeuvics.github.io/ and device names (c:\\)", "fixture")
