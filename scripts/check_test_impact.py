"""
check_test_impact.py — Cross-WP test impact advisor.

Accepts a list of staged source files (from git diff --cached --name-only -- src/)
on the command line, scans tests/ for references to the changed modules, and
outputs advisory warnings listing test files from OTHER workpackages that may
be affected by the change.

Exit code is always 0 (advisory only — never blocks a commit).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _module_variants(src_path: str) -> list[str]:
    """Return search terms derived from a src/ path.

    For ``src/launcher/core/shim_config.py`` this returns:
      - ``launcher.core.shim_config``   (dotted import path)
      - ``launcher/core/shim_config``   (slash path fragment)
      - ``shim_config``                 (bare module name)
    """
    p = Path(src_path)
    # Strip leading src/ component
    parts = list(p.parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    # Drop .py suffix from the last part
    if parts and parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    # __init__ represents the package itself — drop it and use the parent name
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    bare_name = parts[-1] if parts else ""
    dotted = ".".join(parts)
    slashed = "/".join(parts)
    variants: list[str] = []
    if dotted:
        variants.append(dotted)
    if slashed and slashed != dotted:
        variants.append(slashed)
    if bare_name and bare_name not in variants:
        variants.append(bare_name)
    return variants


def _wp_id_from_test_path(test_file: Path, tests_root: Path) -> str:
    """Return the WP-ID directory name a test file lives under, or '' if ambiguous."""
    try:
        rel = test_file.relative_to(tests_root)
        parts = rel.parts
        if parts:
            return parts[0]
    except ValueError:
        pass
    return ""


def _file_references_module(content: str, variants: list[str]) -> bool:
    """Return True if *content* contains any reference to any of *variants*."""
    for variant in variants:
        escaped = re.escape(variant)
        # import launcher.core.shim_config  /  from launcher.core.shim_config import
        if re.search(rf"\b(?:import|from)\s+{escaped}\b", content):
            return True
        # patch("launcher.core.shim_config...") — dotted/slashed variant inside a string
        # Only apply the broad substring match for non-bare variants to avoid false positives.
        if variant != variants[-1]:
            if re.search(rf'["\'].*?{escaped}.*?["\']', content):
                return True
        # plain string mention  e.g. "shim_config"  (bare name only to avoid noise)
        if variant == variants[-1]:  # bare name is always last
            if re.search(rf'["\'].*?\b{escaped}\b.*?["\']', content):
                return True
    return False


def scan(staged_src_files: list[str], repo_root: Path) -> dict[str, list[str]]:
    """Scan tests/ for references to modules derived from *staged_src_files*.

    Returns a dict mapping test-file-path → list[matched_variant].
    Only returns files where a reference was found.
    """
    tests_root = repo_root / "tests"
    if not tests_root.is_dir():
        return {}

    # Collect all (variant_list, src_path) pairs
    targets: list[tuple[list[str], str]] = []
    for src in staged_src_files:
        src = src.replace("\\", "/")
        if not src.startswith("src/") or not src.endswith(".py"):
            continue
        variants = _module_variants(src)
        if variants:
            targets.append((variants, src))

    if not targets:
        return {}

    results: dict[str, list[str]] = {}

    for test_file in sorted(tests_root.rglob("*.py")):
        try:
            content = test_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matched: list[str] = []
        for variants, src in targets:
            if _file_references_module(content, variants):
                matched.append(src)
        if matched:
            results[str(test_file)] = matched

    return results


def format_warnings(
    impacts: dict[str, list[str]],
    staged_src_files: list[str],
    repo_root: Path,
) -> str:
    """Format advisory output grouped by WP directory."""
    if not impacts:
        return ""

    tests_root = repo_root / "tests"
    # Group by WP
    by_wp: dict[str, list[tuple[str, list[str]]]] = {}
    for test_path, srcs in impacts.items():
        wp = _wp_id_from_test_path(Path(test_path), tests_root)
        by_wp.setdefault(wp, []).append((test_path, srcs))

    lines: list[str] = [
        "",
        "============================================================",
        "ADVISORY: Cross-WP test impact detected",
        "The following test files in OTHER workpackages reference",
        "modules you are changing. Review them and update assertions",
        "in this commit if the behavior changes (see ADR-008).",
        "============================================================",
    ]
    for wp in sorted(by_wp):
        label = wp if wp else "(unknown WP)"
        lines.append(f"\n  [{label}]")
        for test_path, srcs in by_wp[wp]:
            rel = os.path.relpath(test_path, repo_root)
            lines.append(f"    {rel}")
            for src in srcs:
                lines.append(f"      ← changes in {src}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        # No files passed — nothing to do
        return 0

    repo_root = Path(__file__).resolve().parent.parent

    impacts = scan(argv, repo_root)
    if impacts:
        print(format_warnings(impacts, argv, repo_root), file=sys.stderr)

    return 0  # always advisory


if __name__ == "__main__":
    sys.exit(main())
