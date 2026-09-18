#!/usr/bin/env python3
"""Safely link one workspace skill into ~/.agents/skills."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Skill folder containing SKILL.md")
    parser.add_argument("--replace", action="store_true", help="Replace an existing symbolic-link target")
    parser.add_argument("--dry-run", action="store_true", help="Show the planned action only")
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    # The installer lives at <workspace>/local-skill-install/scripts/.
    # Derive the workspace root so this repository can be relocated safely.
    workspace_root = Path(__file__).resolve().parents[2]
    destination = (Path.home() / ".agents" / "skills").resolve()

    if not source.is_dir() or not (source / "SKILL.md").is_file():
        fail("source must be a skill directory containing SKILL.md")
    if source.parent != workspace_root:
        fail(f"source must be a direct child of {workspace_root}")
    if destination == source or source in destination.parents:
        fail("destination cannot be inside the source skill directory")

    target = destination / source.name
    if target.exists() or target.is_symlink():
        if target.is_symlink() and target.resolve() == source:
            print(f"Already installed: {target} -> {source}")
            return
        if not args.replace:
            fail(f"target already exists: {target}; inspect it and rerun with --replace if approved")
        if not target.is_symlink():
            fail(f"refusing to replace a non-link target: {target}")

    action = f"link {source} -> {target}"
    if args.dry_run:
        print(f"Would {action}")
        return

    destination.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    target.symlink_to(source, target_is_directory=True)
    print(f"Installed: {target} (link)")


if __name__ == "__main__":
    main()
