from __future__ import annotations

import json
import os
import posixpath
import re
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Tool classification sets
# ---------------------------------------------------------------------------

_ALWAYS_ALLOW_TOOLS: frozenset = frozenset({
    "vscode_ask_questions", "ask_questions",
    "TodoWrite", "TodoRead", "todo_write", "manage_todo_list",
    "runSubagent", "search_subagent", "Agent", "agent",
})

_TERMINAL_TOOLS: frozenset = frozenset({
    "run_in_terminal", "terminal", "run_command",
})

_EXEMPT_TOOLS: frozenset = frozenset({
    "read_file", "Read", "edit_file", "replace_string_in_file",
    "multi_replace_string_in_file", "create_file", "write_file",
    "Edit", "Write", "list_dir", "search", "grep_search",
    "semantic_search", "file_search", "Glob", "agent", "Agent",
    "runSubagent", "search_subagent",
})

# query and pattern are search-content fields, not file-system paths.
# Extracting them for zone classification causes false positives on
# legitimate grep_search / semantic_search calls.
# Search parameter validation is handled in SAF-003.
_PATH_FIELDS: tuple = ("filePath", "file_path", "path", "directory", "target")

_BLOCKED_NAMES: frozenset = frozenset({".github", ".vscode", "noagentzone"})

_BLOCKED_PATTERN = re.compile(r"/(\.github|\.vscode|noagentzone)(/|$)")
_ALLOW_PATTERN = re.compile(r"/project(/|$)")

_STDIN_MAX_BYTES: int = 1_048_576  # 1 MiB hard limit — fail closed if exceeded

_DENY_REASON = (
    "BLOCKED: .github, .vscode, and NoAgentZone are permanently restricted. "
    "This denial is enforced by a PreToolUse hook and cannot be bypassed. "
    "Do NOT retry this action or attempt alternative paths to access these folders."
)
_ASK_REASON = "Turbulence Solutions Safety: Approval required for this action."


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def build_response(decision: str, reason: Optional[str] = None) -> str:
    payload: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
    }
    if reason is not None:
        payload["hookSpecificOutput"]["permissionDecisionReason"] = reason
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_input(raw: str) -> Optional[dict]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------

def extract_tool_name(data: dict) -> str:
    name = data.get("tool_name", "")
    if not isinstance(name, str):
        return ""
    return name


def extract_path(data: dict) -> Optional[str]:
    for field in _PATH_FIELDS:
        value = data.get(field)
        if isinstance(value, str) and value:
            return value
    for key in ("input", "tool_input"):
        nested = data.get(key)
        if isinstance(nested, dict):
            for field in _PATH_FIELDS:
                value = nested.get(field)
                if isinstance(value, str) and value:
                    return value
    return None


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------

def normalize_path(p: str) -> str:
    # Null bytes have no legitimate use in file paths — strip them
    p = p.replace("\x00", "")
    # JSON-escaped double backslashes → forward slash
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
    # Strip trailing slash then resolve ../ components
    p = p.rstrip("/")
    p = posixpath.normpath(p)
    return p


# ---------------------------------------------------------------------------
# Zone classification
# ---------------------------------------------------------------------------

def get_zone(path: str, ws_root: str) -> str:
    ws_root = ws_root.rstrip("/")

    # Strip workspace-root prefix to work with a relative-style path
    rel = path
    if path.startswith(ws_root + "/"):
        rel = path[len(ws_root) + 1:]

    # Method 1: First-segment prefix check (robust when ws_root matches)
    first_segment = rel.split("/")[0] if "/" in rel else rel
    if first_segment in _BLOCKED_NAMES:
        return "deny"
    if first_segment == "project":
        return "allow"

    # Method 2: Pattern-based fallback — catches mismatched roots and edge cases
    # Prepend "/" to guarantee a leading separator for the regex anchor
    full_with_slash = "/" + path
    if _BLOCKED_PATTERN.search(full_with_slash):
        return "deny"
    if _ALLOW_PATTERN.search(full_with_slash):
        return "allow"

    return "ask"


# ---------------------------------------------------------------------------
# Decision engine
# ---------------------------------------------------------------------------

def decide(data: dict, ws_root: str) -> str:
    tool_name = extract_tool_name(data)

    # Always-allow tools bypass all zone checks
    if tool_name in _ALWAYS_ALLOW_TOOLS:
        return "allow"

    # Terminal tools: scan entire serialized input for blocked references
    if tool_name in _TERMINAL_TOOLS:
        serialized = (
            json.dumps(data)
            .replace("\\\\", "/")
            .replace("\\", "/")
            .lower()
        )
        if re.search(r"\.github|\.vscode|noagentzone", serialized):
            return "deny"
        return "ask"

    # Non-exempt tools (non-empty name not in exempt set): always ask
    if tool_name and tool_name not in _EXEMPT_TOOLS:
        return "ask"

    # Exempt tool or unknown tool name: resolve path and check zone
    raw_path = extract_path(data)
    if raw_path is None:
        return "ask"

    norm = normalize_path(raw_path)

    # Resolve relative paths against workspace root
    if not re.match(r"^[a-z]:", norm) and not norm.startswith("/"):
        norm = posixpath.normpath(ws_root + "/" + norm)

    zone = get_zone(norm, ws_root)
    if zone == "deny":
        return "deny"
    if zone == "allow":
        return "allow"
    return "ask"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        raw = sys.stdin.read(_STDIN_MAX_BYTES)
        # If we read exactly the limit the input may be oversized — fail closed
        if len(raw) >= _STDIN_MAX_BYTES:
            print(build_response("deny", _DENY_REASON), flush=True)
            sys.exit(0)

        ws_root = normalize_path(os.getcwd())

        data = parse_input(raw)
        if data is None:
            print(build_response("deny", _DENY_REASON), flush=True)
            sys.exit(0)

        decision = decide(data, ws_root)

        if decision == "allow":
            print(build_response("allow"), flush=True)
        elif decision == "deny":
            print(build_response("deny", _DENY_REASON), flush=True)
        else:
            print(build_response("ask", _ASK_REASON), flush=True)

    except Exception:
        print(build_response("deny", _DENY_REASON), flush=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
