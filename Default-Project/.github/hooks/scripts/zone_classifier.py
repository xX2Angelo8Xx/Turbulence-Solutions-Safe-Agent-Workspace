"""SAF-002 — Zone Enforcement Logic

Standalone 3-tier zone classifier using pathlib for path operations.

Zones
-----
allow  — Project/
deny   — .github/, .vscode/, NoAgentZone/
ask    — everything else  (default / fail-safe)

Design
------
Method 1 uses pathlib.PurePosixPath.relative_to() to extract the
first path segment relative to the workspace root.  Unlike string
startswith(), relative_to() rejects sibling-prefix paths  (e.g.
"project-evil/" does NOT match root/"project").

Method 2 is a regex fallback that catches paths from different roots,
UNC paths, and any case where Method 1 cannot determine the zone.

The default return value is "ask" — no path accidentally receives
"allow".  All decisions fail closed.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import PurePosixPath
from typing import Literal

ZoneDecision = Literal["allow", "deny", "ask"]

# Deny-zone folder names (lowercase — all comparisons are case-insensitive)
_DENY_DIRS: frozenset[str] = frozenset({".github", ".vscode", "noagentzone"})
_ALLOW_DIR: str = "project"

# Method 2 compiled patterns — anchored on a "/" to avoid mid-segment matches
_BLOCKED_PATTERN = re.compile(r"/(\.github|\.vscode|noagentzone)(/|$)")
_ALLOW_PATTERN = re.compile(r"/project(/|$)")


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


def classify(raw_path: str, ws_root: str) -> ZoneDecision:
    """Classify *raw_path* against the 3-tier zone system.

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
    'allow'  — path is inside Project/
    'deny'   — path is inside .github/, .vscode/, or NoAgentZone/
    'ask'    — path is anywhere else  (default / fail-safe)
    """
    norm = normalize_path(raw_path)

    # Resolve relative paths against the workspace root before any zone check.
    # This prevents traversal sequences like "../.github/" from bypassing
    # prefix checks when the path appears to be relative.
    if not re.match(r"^[a-z]:", norm) and not norm.startswith("/"):
        norm = posixpath.normpath(ws_root.rstrip("/") + "/" + norm)

    ws_clean = ws_root.rstrip("/")

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
        if first == _ALLOW_DIR:
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
    # Only grant "allow" for paths that genuinely reside inside the workspace root.
    # Matching _ALLOW_PATTERN anywhere in the string would return "allow" for a UNC
    # path like \\server\share\project\... that is on a foreign network host (BUG-011).
    if _ALLOW_PATTERN.search(full_with_slash) and (
        norm.startswith(ws_clean + "/") or norm == ws_clean
    ):
        return "allow"

    return "ask"
