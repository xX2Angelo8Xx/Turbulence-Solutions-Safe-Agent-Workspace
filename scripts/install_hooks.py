#!/usr/bin/env python3
"""Install Git hooks by pointing core.hooksPath to scripts/hooks/.

The hooks directory is tracked by Git, so after pulling on any device
you just run this script once and hooks are immediately active.

Usage:
    .venv/Scripts/python scripts/install_hooks.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    hooks_dir = REPO_ROOT / "scripts" / "hooks"
    if not hooks_dir.exists():
        print(f"Error: {hooks_dir} does not exist")
        return 1

    # Set git to use our tracked hooks directory
    result = subprocess.run(
        ["git", "config", "core.hooksPath", "scripts/hooks"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"Error setting core.hooksPath: {result.stderr}")
        return 1

    # Verify
    verify = subprocess.run(
        ["git", "config", "core.hooksPath"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    print(f"Git hooks installed successfully.")
    print(f"  core.hooksPath = {verify.stdout.strip()}")
    print(f"  Hooks directory: {hooks_dir}")
    print(f"\nPre-commit validation is now active. Every commit will run")
    print(f"scripts/validate_workspace.py --full automatically.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
