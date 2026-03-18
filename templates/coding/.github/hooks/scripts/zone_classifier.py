"""SAF-012 — Zone Enforcement Logic (2-Tier Deny-by-Default)

Standalone 2-tier zone classifier using pathlib for path operations.

Zones
-----
allow  — detected project folder (the one non-system subfolder of the workspace root)
deny   — everything else  (default / fail-safe)

The "ask" zone has been removed. All paths outside the project folder
are denied — no path accidentally receives "allow".

Design
------
Method 1 uses pathlib.PurePosixPath.relative_to() to extract the
first path segment relative to the workspace root.  Unlike string
startswith(), relative_to() rejects sibling-prefix paths  (e.g.
"project-evil/" does NOT match root/"project").

Method 2 is a regex fallback that catches paths from different roots,
UNC paths, and any case where Method 1 cannot determine the zone.

Project folder detection is performed at classification time by scanning
immediate subdirectories of the workspace root and selecting the first
non-system folder alphabetically.  This removes the dependency on any
hardcoded folder name.

Security: all decisions fail closed (deny).  .github/, .vscode/, and
NoAgentZone/ are kept as explicit denies (defense in depth) in addition
to the blanket deny-by-default for any path outside the project folder.
"""
from __future__ import annotations

import os
import posixpath
import re
from pathlib import Path, PurePosixPath
from typing import Literal

ZoneDecision = Literal["allow", "deny"]

# Deny-zone folder names (lowercase — all comparisons are case-insensitive)
_DENY_DIRS: frozenset[str] = frozenset({".github", ".vscode", "noagentzone"})

# Method 2 compiled pattern — anchored on a "/" to avoid mid-segment matches
_BLOCKED_PATTERN = re.compile(r"/(\.github|\.vscode|noagentzone)(/|$)")


def detect_project_folder(workspace_root: Path) -> str:
    """Return the name of the project folder inside *workspace_root*.

    Scans the immediate subdirectories of *workspace_root* and returns the
    first entry (alphabetically, case-insensitive) whose lowercase name is
    NOT in ``_DENY_DIRS``.  This allows the project folder to have any name
    (e.g. "Project", "MatlabDemo", "MyApp") without requiring a hardcoded
    constant.

    Parameters
    ----------
    workspace_root : Path
        Absolute path to the workspace root directory.

    Returns
    -------
    str
        Lowercase name of the detected project folder.

    Raises
    ------
    RuntimeError
        If no non-system subfolder is found under *workspace_root*.
    """
    entries = sorted(
        (e for e in os.listdir(workspace_root) if os.path.isdir(os.path.join(workspace_root, e))),
        key=str.lower,
    )
    for entry in entries:
        if entry.lower() not in _DENY_DIRS:
            return entry.lower()
    raise RuntimeError(
        f"No project folder detected under {workspace_root}. "
        "All immediate subdirectories are system-reserved folders."
    )


def normalize_path(p: str) -> str:
    """Canonicalize a raw path string to lowercase forward-slash POSIX form.

    Handles:
    - Null bytes (stripped — no valid use in file paths)
    - JSON-escaped double backslashes (\\\\  → /)
    - Single backslashes (\\  → /)
    - WSL /mnt/c/... prefix  → c:/...
    - Git Bash /c/... prefix → c:/...
    - Trailing slashes
    - '..' traversal sequences (via posixpath.normpath)
    """
    # C0 control characters (\x00–\x1f) have no legitimate use in file paths — strip all of them.
    # Stripping only null bytes (\x00) leaves tab, newline, CR etc. which can be injected
    # immediately before a deny-zone directory name to bypass the deny check (BUG-010).
    p = re.sub(r'[\x00-\x1f]', '', p)
    # JSON double-escaped backslash → forward slash
    p = p.replace("\\\\", "/")
    # Remaining single backslashes → forward slash
    p = p.replace("\\", "/")
    # Lowercase for case-insensitive comparison
    p = p.lower()
    # WSL mount prefix: /mnt/c/Users/... → c:/Users/...
    m = re.match(r"^/mnt/([a-z])/(.*)", p)
    if m:
        p = f"{m.group(1)}:/{m.group(2)}"
    else:
        # Git Bash / MSYS2 prefix: /c/Users/... → c:/Users/...
        m = re.match(r"^/([a-z])/(.*)", p)
        if m:
            p = f"{m.group(1)}:/{m.group(2)}"
    # Resolve '..' components after stripping trailing slash
    p = p.rstrip("/")
    p = posixpath.normpath(p)
    return p


def is_git_internals(path: str) -> bool:
    """Return True if the path is inside or is the .git directory.

    Accepts a raw or already-normalized path string.
    The path is normalized before the check so that:
    - Case variations (.GIT/ on Windows) are lowercased → caught
    - Backslashes (.git\\config) are converted → caught
    - Path traversal (src/../../.git/config) is resolved → caught

    Parameters
    ----------
    path : str
        Raw or normalized path string to test.

    Returns
    -------
    bool
        True if the path IS the .git directory or resides inside it.
    """
    norm = normalize_path(path)
    # After normalize_path:
    #   - all slashes are forward slashes
    #   - path is lowercase
    #   - '..' sequences are resolved
    #   - trailing slashes are stripped
    # Match either "/.git/" (inside .git subdir) or ending "/.git" (the dir itself)
    return "/.git/" in norm or norm.endswith("/.git")


def classify(raw_path: str, ws_root: str) -> ZoneDecision:
    """Classify *raw_path* against the 2-tier zone system.

    Parameters
    ----------
    raw_path : str
        Path from the VS Code hook payload.  May be relative or absolute,
        Windows or Unix-style, and may contain traversal sequences.
    ws_root : str
        Workspace root as reported by the hook process — typically
        normalize_path(os.getcwd()).  Must use forward slashes and be
        lowercase.

    Returns
    -------
    'allow'  — path is inside the detected project folder
    'deny'   — path is anywhere else (default / fail-safe)
    """
    norm = normalize_path(raw_path)

    # Resolve relative paths against the workspace root before any zone check.
    # This prevents traversal sequences like "../.github/" from bypassing
    # prefix checks when the path appears to be relative.
    if not re.match(r"^[a-z]:", norm) and not norm.startswith("/"):
        norm = posixpath.normpath(ws_root.rstrip("/") + "/" + norm)

    ws_clean = ws_root.rstrip("/")

    # Detect the project folder at classification time using the real filesystem.
    # Fail closed: if detection fails, deny immediately — no path is allowed.
    try:
        project_dir = detect_project_folder(Path(ws_clean))
    except (RuntimeError, OSError):
        return "deny"

    # ------------------------------------------------------------------
    # Method 1: pathlib relative_to() for structured first-segment check
    # ------------------------------------------------------------------
    # PurePosixPath.relative_to() raises ValueError when the path is not
    # a genuine subdirectory of the root, which rejects sibling-prefix
    # attacks that str.startswith() would pass (e.g. "project-evil/").
    path = PurePosixPath(norm)
    root = PurePosixPath(ws_clean)
    try:
        rel = path.relative_to(root)
        first = rel.parts[0] if rel.parts else ""
        if first in _DENY_DIRS:
            return "deny"
        if first == project_dir:
            return "allow"
        # First segment is neither deny nor allow — fall through to Method 2.
        # This is intentional: a path like "project-evil/.github/x" must still
        # be caught by the pattern scan below.
    except ValueError:
        # path is not under ws_root — fall through to Method 2
        pass

    # ------------------------------------------------------------------
    # Method 2: pattern-based fallback
    # ------------------------------------------------------------------
    # Catches paths from different roots, UNC paths, and cross-root edge
    # cases where Method 1's relative_to() cannot determine the zone.
    # A leading "/" is prepended to guarantee the regex anchor works even
    # when norm starts with a drive letter (e.g. "c:/...").
    full_with_slash = "/" + norm
    if _BLOCKED_PATTERN.search(full_with_slash):
        return "deny"
    # Build allow pattern dynamically from the detected project folder name.
    # Only grant "allow" for paths that genuinely reside inside the workspace root
    # (BUG-011: prevents UNC path \\server\share\<project>\... from matching).
    allow_pattern = re.compile(r"/" + re.escape(project_dir) + r"(/|$)")
    if allow_pattern.search(full_with_slash) and (
        norm.startswith(ws_clean + "/") or norm == ws_clean
    ):
        return "allow"

    # Default: deny everything outside the project folder.
    return "deny"
