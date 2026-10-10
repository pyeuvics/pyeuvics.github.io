from __future__ import annotations

from pathlib import Path

import pytest

from tools.verify_runner_credentials import (
    CredentialResidueError,
    verify_no_private_keys,
)


def test_runner_temp_scan_accepts_noncredential_files(tmp_path: Path) -> None:
    (tmp_path / "known_hosts").write_text("github.com ssh-ed25519 public-key\n", encoding="utf-8")
    verify_no_private_keys(tmp_path)


def test_runner_temp_scan_rejects_private_key_without_exposing_it(tmp_path: Path) -> None:
    key = tmp_path / "checkout-key"
    key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nsecret\n", encoding="utf-8")
    with pytest.raises(CredentialResidueError, match="private key material remains") as caught:
        verify_no_private_keys(tmp_path)
    assert "secret" not in str(caught.value)
