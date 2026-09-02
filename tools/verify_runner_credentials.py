#!/usr/bin/env python3
"""Fail when checkout private-key material remains in a runner temp tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


class CredentialResidueError(ValueError):
    """Private credential material remains after a source checkout."""


PRIVATE_KEY_MARKERS = (
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN PRIVATE KEY-----",
)


def verify_no_private_keys(root: Path) -> None:
    """Scan regular files below *root* without reporting credential contents."""

    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise CredentialResidueError(f"credential scan root is not a directory: {resolved}")
    for path in resolved.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise CredentialResidueError(f"cannot inspect runner temporary file: {path}") from exc
        if any(marker in payload for marker in PRIVATE_KEY_MARKERS):
            raise CredentialResidueError(f"private key material remains in runner temp: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verify_no_private_keys(args.root)
    except (OSError, CredentialResidueError) as exc:
        print(f"credential residue error: {exc}", file=sys.stderr)
        return 1
    print("No private-key material remains in the runner temporary directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
