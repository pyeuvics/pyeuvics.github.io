#!/usr/bin/env python3
"""Command-line entry point for deterministic EUVICS website source assembly."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.site_assembly import AssemblyError, assemble_site


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--euvics-source", type=Path, required=True)
    parser.add_argument("--pyeuvics-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=Path("sources.lock.yml"))
    parser.add_argument("--website-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        result = assemble_site(
            args.website_root,
            args.lock,
            args.euvics_source,
            args.pyeuvics_source,
            args.output,
        )
    except AssemblyError as exc:
        print(f"assembly error: {exc}", file=sys.stderr)
        return 1
    print(f"assembled {len(result.inventory)} approved files")
    print(f"inventory: {result.output_root / 'staged-content-inventory.json'}")
    print(f"site: {result.site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
