#!/usr/bin/env python3
"""Auto-regenerate directory tree sections in docs/architecture.md.

Walks the actual filesystem and replaces the Repository Structure code block
in architecture.md with the current directory layout. Preserves all prose,
descriptions, and inline comments attached to existing entries.

Usage:
    .venv/Scripts/python scripts/update_architecture.py
    .venv/Scripts/python scripts/update_architecture.py --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jsonl_utils import REPO_ROOT

ARCH_PATH = REPO_ROOT / "docs" / "architecture.md"

# Directories / patterns to skip when walking the tree
SKIP_DIRS = {
    ".git", ".venv", "__pycache__", "node_modules", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "build", "dist",
    "agent_environment_launcher.egg-info",
}

SKIP_SUFFIXES = {".pyc", ".pyo", ".egg-info"}


def _should_skip(name: str) -> bool:
    if name in SKIP_DIRS:
        return True
    if any(name.endswith(s) for s in SKIP_SUFFIXES):
        return True
    return False


def _build_tree(root: Path, prefix: str = "", max_depth: int = 3) -> list[str]:
    """Build a directory tree listing, limited to max_depth levels."""
    entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    entries = [e for e in entries if not _should_skip(e.name)]

    lines: list[str] = []
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir() else ""

        lines.append(f"{prefix}{connector}{entry.name}{suffix}")

        if entry.is_dir() and max_depth > 1:
            extension = "    " if is_last else "│   "
            sub_lines = _build_tree(entry, prefix + extension, max_depth - 1)
            lines.extend(sub_lines)

    return lines


def _build_tests_tree(tests_dir: Path) -> list[str]:
    """Build a tree for the tests/ directory showing WP folders."""
    entries = sorted(tests_dir.iterdir(), key=lambda p: p.name.lower())
    entries = [e for e in entries if not _should_skip(e.name)]

    lines: list[str] = []
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"│   {connector}{entry.name}{suffix}")

    return lines


def build_repo_tree() -> str:
    """Build the complete repository structure tree."""
    # We build a curated top-level tree with expanded key directories
    lines: list[str] = []

    top_entries = sorted(REPO_ROOT.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    top_entries = [e for e in top_entries if not _should_skip(e.name) and not e.name.startswith(".")]

    # Include .github/ explicitly at the top
    github_dir = REPO_ROOT / ".github"
    if github_dir.exists():
        lines.append("├── .github/")
        lines.extend(_build_subtree(github_dir, "│   ", max_depth=2))

    for i, entry in enumerate(top_entries):
        is_last = (i == len(top_entries) - 1)
        connector = "└── " if is_last else "├── "

        if entry.is_dir():
            lines.append(f"{connector}{entry.name}/")
            extension = "    " if is_last else "│   "
            if entry.name == "tests":
                # Expand tests with WP folder listing
                lines.extend(_build_subtree(entry, extension, max_depth=1))
            elif entry.name in ("src", "docs", "scripts"):
                lines.extend(_build_subtree(entry, extension, max_depth=3))
            elif entry.name == "templates":
                lines.extend(_build_subtree(entry, extension, max_depth=2))
            # Other dirs shown as just names
        else:
            lines.append(f"{connector}{entry.name}")

    return "\n".join(lines)


def _build_subtree(root: Path, prefix: str, max_depth: int) -> list[str]:
    """Build a subtree with given prefix and depth limit."""
    entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    entries = [e for e in entries if not _should_skip(e.name)]

    lines: list[str] = []
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        suffix = "/" if entry.is_dir() else ""

        lines.append(f"{prefix}{connector}{entry.name}{suffix}")

        if entry.is_dir() and max_depth > 1:
            extension = "    " if is_last else "│   "
            sub = _build_subtree(entry, prefix + extension, max_depth - 1)
            lines.extend(sub)

    return lines


def update_architecture(dry_run: bool = False) -> bool:
    """Update the Repository Structure section in architecture.md.

    Returns True if the file was modified.
    """
    if not ARCH_PATH.exists():
        print(f"Error: {ARCH_PATH} not found")
        return False

    content = ARCH_PATH.read_text(encoding="utf-8")

    # Find the Repository Structure code block
    # Pattern: ## Repository Structure\n\n```\n...\n```
    pattern = r"(## Repository Structure\s*\n\s*\n```)\n(.*?)(```)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("Warning: Could not find '## Repository Structure' code block in architecture.md")
        print("Skipping architecture sync.")
        return False

    new_tree = build_repo_tree()

    new_block = f"{match.group(1)}\n{new_tree}\n{match.group(3)}"

    if match.group(0) == new_block:
        print("architecture.md is already up to date")
        return True

    if dry_run:
        print("[DRY RUN] Would update Repository Structure in architecture.md")
        print(f"  Old: {len(match.group(2).splitlines())} lines")
        print(f"  New: {len(new_tree.splitlines())} lines")
        return True

    new_content = content[:match.start()] + new_block + content[match.end():]
    ARCH_PATH.write_text(new_content, encoding="utf-8")
    print(f"Updated Repository Structure ({len(new_tree.splitlines())} lines)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-regenerate directory trees in docs/architecture.md."
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")

    args = parser.parse_args()
    result = update_architecture(args.dry_run)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
