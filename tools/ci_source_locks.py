#!/usr/bin/env python3
"""Emit safe GitHub Actions outputs derived from the reviewed source lock."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.site_assembly.contracts import ContractError, load_locks, verify_checkout


def _slug(repository: str) -> str:
    prefix = "https://github.com/"
    if not repository.startswith(prefix):
        raise ContractError(f"unsupported repository URL: {repository}")
    return repository.removeprefix(prefix)


def resolve(lock_path: Path) -> tuple[str, ...]:
    """Return checkout outputs without exposing credentials or mutable refs."""

    locks = load_locks(lock_path)
    return tuple(
        value
        for name in ("euvics", "pyeuvics")
        for value in (
            f"{name}_repository={_slug(locks[name].repository)}",
            f"{name}_commit={locks[name].commit}",
        )
    )


def inspect_euvics(lock_path: Path, source: Path) -> tuple[str, ...]:
    """Report whether the exact locked EUVICS manifest approves any PDF."""

    lock = load_locks(lock_path)["euvics"]
    verify_checkout(lock, source)
    try:
        manifest = json.loads((source / lock.manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot inspect locked EUVICS manifest: {exc}") from exc
    allowlist = manifest.get("allowlist")
    if not isinstance(allowlist, list):
        raise ContractError("locked EUVICS manifest allowlist must be an array")
    has_pdf = any(isinstance(item, dict) and item.get("kind") == "pdf" for item in allowlist)
    return (f"approved_pdf={'true' if has_pdf else 'false'}",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, default=Path("sources.lock.yml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("resolve")
    inspect_parser = subparsers.add_parser("inspect-euvics")
    inspect_parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        lines = (
            resolve(args.lock)
            if args.command == "resolve"
            else inspect_euvics(args.lock, args.source)
        )
    except ContractError as exc:
        print(f"CI source-lock error: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
