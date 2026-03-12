from __future__ import annotations

import dataclasses
import json
import os
import posixpath
import re
import shlex
import sys
from typing import Optional

# SAF-002: zone classification is delegated to the dedicated module.
# zone_classifier.py lives in the same scripts directory; it is on
# sys.path both when the script runs directly (Python adds the script's
# own directory) and in tests (the test fixture inserts the scripts dir).
import zone_classifier

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

# SAF-007: Tool names that perform file write operations.
# These are restricted to Project/ only — writes outside Project/ are denied.
_WRITE_TOOLS: frozenset = frozenset({
    "create_file", "write_file", "Write",
    "edit_file", "Edit",
    "replace_string_in_file", "multi_replace_string_in_file",
})

# query and pattern are search-content fields, not file-system paths.
# Extracting them for zone classification causes false positives on
# legitimate grep_search / semantic_search calls.
# Search parameter validation is handled in SAF-003.
_PATH_FIELDS: tuple = ("filePath", "file_path", "path", "directory", "target")

_STDIN_MAX_BYTES: int = 1_048_576  # 1 MiB hard limit — fail closed if exceeded

_DENY_REASON = (
    "BLOCKED: .github, .vscode, and NoAgentZone are permanently restricted. "
    "This denial is enforced by a PreToolUse hook and cannot be bypassed. "
    "Do NOT retry this action or attempt alternative paths to access these folders."
)
_ASK_REASON = "Turbulence Solutions Safety: Approval required for this action."


# ---------------------------------------------------------------------------
# SAF-005: Terminal command sanitization constants
# ---------------------------------------------------------------------------

# Stage 3 — 28 obfuscation pre-scan patterns (Section 6 + Section 10)
# Applied against the LOWERCASED command string.  Any match → immediate deny.
_OBFUSCATION_PATTERNS: list[re.Pattern[str]] = [
    # P-01 to P-09: interpreter chaining flags
    re.compile(r"\bpython[23]?\s+(-u\s+)?-c\b"),
    re.compile(r"\bpython[23]?\s+(-u\s+)?-m\s+code\b"),
    re.compile(r"\bperl\s+-e\b"),
    re.compile(r"\bruby\s+-e\b"),
    re.compile(r"\bnode\s+-e\b"),
    re.compile(r"\bphp\s+-r\b"),
    re.compile(r"\b(bash|sh|zsh|fish|dash|ksh)\s+-c\b"),
    re.compile(r"\bcmd(\.exe)?\s+/[ck]\b"),
    re.compile(r"\bipython\s+-c\b"),
    # P-10: PowerShell encoded command (covers -e, -en, -enc, -EncodedCommand)
    re.compile(r"(?:powershell|pwsh)[^\n]*?-e(?:nc(?:odedcommand)?)?\s+[A-Za-z0-9+/=]{10,}"),
    # P-11 to P-15: PowerShell dynamic execution
    re.compile(r"\biex\b"),
    re.compile(r"\binvoke-expression\b"),
    re.compile(r"\bstart-process\b"),
    re.compile(r"&\s*\$\w+"),
    re.compile(r"(\[convert\]::|frombase64string|\[system\.text\.encoding\])"),
    # P-16 to P-17: pipe-to-interpreter
    re.compile(r"\|\s*(bash|sh|zsh|fish|pwsh|powershell|python[23]?|perl|ruby|node|php)\b"),
    re.compile(r"\|\s*iex\b"),
    # P-18 to P-19: subshell execution
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\("),
    # P-20 to P-23: dynamic evaluation keywords
    re.compile(r"\beval\b"),
    re.compile(r"\bexec\b"),
    re.compile(r"\bsource\s+"),
    re.compile(r"\.\s+\S"),  # POSIX dot-source
    # P-24 to P-27: Windows-specific
    re.compile(r"-executionpolicy\s+bypass"),
    re.compile(r"\binvoke-item\b"),
    re.compile(r"\bset-alias\b"),
    re.compile(r"\bnew-alias\b"),
    # P-28: process substitution <(...) or >(...)
    re.compile(r"[<>]\("),
]

# Stage 5 fallback — explicit destructive patterns applied after allowlist passes
_EXPLICIT_DENY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\brm\s"),
    re.compile(r"\bdel\b"),
    re.compile(r"\berase\b"),
    re.compile(r"\brmdir\b"),
    re.compile(r"\bremove-item\b"),
    re.compile(r"\bri\b"),
    re.compile(r"\bformat\b"),
    re.compile(r"\bfdisk\b"),
    re.compile(r"\bdiskpart\b"),
    re.compile(r"\bdd\s+(if|of)="),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\brestart-computer\b"),
    re.compile(r"\breg\s+(add|delete)\b"),
    re.compile(r"set-itemproperty\s+(hklm|hkcu|hkcr):"),
    re.compile(r"\bsudo\b"),
    re.compile(r"\brunas\b"),
    re.compile(r"-enc(?:odedcommand)?\s+[A-Za-z0-9+/=]{20,}"),
]


@dataclasses.dataclass(frozen=True)
class CommandRule:
    denied_flags: frozenset[str]
    allowed_subcommands: frozenset[str]
    path_args_restricted: bool
    allow_arbitrary_paths: bool
    notes: str


# Command allowlist — keyed by lowercase primary verb (Sections 7.2, Categories A–J)
# Version aliases (python3.x, pip3.x) are normalized before lookup.
_COMMAND_ALLOWLIST: dict[str, CommandRule] = {
    # Category A — Python Runtime
    "python": CommandRule(
        denied_flags=frozenset({"-c", "-i", "--interactive"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="python3.x aliases normalized to python; -m restricted to approved modules",
    ),
    "python3": CommandRule(
        denied_flags=frozenset({"-c", "-i", "--interactive"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="python3.x aliases normalized to python3",
    ),
    "py": CommandRule(
        denied_flags=frozenset({"-c", "-i", "--interactive"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows py launcher",
    ),
    # Category B — Package Management
    "pip": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "install", "uninstall", "list", "show", "freeze",
            "check", "download", "config",
        }),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="pip3.x aliases normalized to pip",
    ),
    "pip3": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "install", "uninstall", "list", "show", "freeze",
            "check", "download", "config",
        }),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="pip3.x aliases normalized to pip3",
    ),
    # Category C — Testing
    "pytest": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="All standard pytest flags allowed; path args zone-checked",
    ),
    # Category D — Build Tools
    "pyinstaller": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Spec files and .py entry points zone-checked",
    ),
    "hatch": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({"build", "run", "env", "dep", "version", "publish"}),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "build": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="python -m build invocation or standalone",
    ),
    "twine": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({"check", "upload"}),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="",
    ),
    # Category E — Version Control
    "git": CommandRule(
        denied_flags=frozenset({"--force", "-f"}),
        allowed_subcommands=frozenset({
            "status", "log", "diff", "branch", "add", "commit",
            "fetch", "pull", "push", "checkout", "stash", "tag",
            "show", "remote", "config", "init", "clone", "merge",
            "rebase", "describe", "shortlog", "rev-parse", "ls-files",
        }),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="push --force denied; filter-branch/gc --force denied",
    ),
    # Category F — Node / NPM Ecosystem
    "npm": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "install", "ci", "run", "test", "build", "start",
            "pack", "publish", "list", "ls", "outdated", "update", "audit",
        }),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "yarn": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "install", "add", "remove", "run", "test",
            "build", "upgrade", "list", "audit",
        }),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "node": CommandRule(
        denied_flags=frozenset({"-e", "--eval", "--interactive", "-i"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Only .js file arguments; no inline code",
    ),
    "npx": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="Always returns ask — package name unknown to allowlist",
    ),
    "pnpm": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "install", "ci", "run", "test", "build", "start",
            "pack", "publish", "list", "ls", "outdated", "update", "audit",
        }),
        path_args_restricted=False,
        allow_arbitrary_paths=False,
        notes="",
    ),
    # Category G — Read-only File Inspection
    "cat": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Path args zone-checked",
    ),
    "type": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows read equivalent; path zone-checked",
    ),
    "head": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "tail": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "less": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "more": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="",
    ),
    "ls": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="-R/--recursive handled by SAF-006 ancestor check",
    ),
    "dir": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows listing; /s handled by SAF-006 ancestor check",
    ),
    "get-childitem": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell; -Recurse handled by SAF-006 ancestor check",
    ),
    "gci": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Get-ChildItem; -Recurse handled by SAF-006 ancestor check",
    ),
    "echo": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Free form; no path validation needed",
    ),
    "write-host": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="PowerShell echo equivalent",
    ),
    "write-output": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="PowerShell echo equivalent",
    ),
    # Category H — Navigation and Environment
    "pwd": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="No args needed",
    ),
    "cd": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Path zone-checked; deny if targets restricted zone",
    ),
    "set-location": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell cd; path zone-checked",
    ),
    "sl": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell alias for Set-Location",
    ),
    "which": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Command lookup; no zone risk",
    ),
    "where": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Windows which equivalent",
    ),
    "get-command": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="PowerShell command lookup",
    ),
    "gcm": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Alias for Get-Command",
    ),
    "env": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Read env vars; no-arg is safe",
    ),
    "printenv": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="POSIX read env vars",
    ),
    # Category I — VS Code CLI
    "code": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset({
            "--version", "--list-extensions",
            "--install-extension", "--uninstall-extension",
        }),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="VS Code CLI; subcommand restricted",
    ),
    # Category J — Shell Utilities (Create / Copy / Move only)
    "mkdir": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Targets zone-checked; -p allowed",
    ),
    "new-item": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell; file/dir creation; path zone-checked",
    ),
    "cp": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Source and dest zone-checked",
    ),
    "copy": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows copy; both paths zone-checked",
    ),
    "copy-item": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Copy-Item",
    ),
    "mv": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Source and dest zone-checked",
    ),
    "move": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows move; both paths zone-checked",
    ),
    "move-item": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Move-Item",
    ),
    # Category K — Recursive directory listing (SAF-006)
    "tree": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Inherently recursive; ancestor-of-deny-zone check in SAF-006",
    ),
    "find": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Inherently recursive; ancestor-of-deny-zone check in SAF-006",
    ),
}

# Allowed Python -m modules (Section 7.2 Category A sub-rules)
_PYTHON_ALLOWED_MODULES: frozenset[str] = frozenset({
    "pytest", "build", "pip", "setuptools", "hatchling",
})

# Destructive git subcommand+flag combinations that must be denied
_GIT_DENIED_COMBOS: list[tuple[str, str]] = [
    ("push", "--force"),
    ("push", "-f"),
    ("reset", "--hard"),
    ("clean", "-f"),
    ("clean", "-fd"),
    ("filter-branch", ""),
    ("gc", "--force"),
]


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
    """Backward-compatible wrapper — delegates to zone_classifier.classify().

    Callers may pass an already-normalized absolute path; classify()
    normalizes its input, so double-normalization is idempotent.
    """
    return zone_classifier.classify(path, ws_root)


# ---------------------------------------------------------------------------
# SAF-005: Terminal command sanitization helpers
# ---------------------------------------------------------------------------

# Regex to identify environment-variable assignment tokens (VAR=value)
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Segments separator — split command on these shell chain operators
_CHAIN_RE = re.compile(r";|&&|\|\|")

# What looks like a file-system path argument:
# - contains a forward or back slash, OR
# - starts with . (relative path like ./file or ../dir)
_PATH_LIKE_RE = re.compile(r"[/\\]|\.\.")


def _is_path_like(token: str) -> bool:
    """Return True if *token* looks like a file-system path argument."""
    return bool(_PATH_LIKE_RE.search(token)) or token.startswith(".")


def _normalize_terminal_command(raw: str) -> str:
    """Stage 2: strip leading/trailing whitespace; collapse internal runs."""
    return " ".join(raw.split())


def _split_segments(command: str) -> list[str]:
    """Stage 4 (first half): split on ;, &&, || into independent segments."""
    return [s.strip() for s in _CHAIN_RE.split(command) if s.strip()]


def _tokenize_segment(segment: str) -> list[str]:
    """Stage 4 (second half): split one segment into tokens respecting quotes.

    Returns an empty list if the segment cannot be parsed (treat as deny).
    """
    try:
        lex = shlex.shlex(segment, posix=True)
        lex.whitespace_split = True
        lex.whitespace = " \t"
        return list(lex)
    except ValueError:
        return []


def _extract_verb(tokens: list[str]) -> str:
    """Stage 4: return the primary verb — first non-env-assignment token."""
    for tok in tokens:
        if not _ENV_ASSIGN_RE.match(tok):
            return tok
    return ""


def _check_path_arg(token: str, ws_root: str) -> bool:
    """Return True if *token* is a safe path argument, False to deny.

    Denies if:
    - Token contains '$' (variable reference — runtime value unknown)
    - Resolved path zone returns 'deny'
    """
    if "$" in token:
        return False
    if not _is_path_like(token):
        return True  # not a path; no zone concern
    # Resolve relative paths against workspace root, then zone-check
    norm = posixpath.normpath(
        token.replace("\\", "/")
    )
    zone = zone_classifier.classify(norm, ws_root)
    return zone != "deny"


def _validate_args(rule: CommandRule, verb: str, tokens: list[str],
                   ws_root: str) -> bool:
    """Stage 5 argument validation.  Returns True (safe) or False (deny).

    tokens is the full token list of the segment including the verb.
    """
    # Tokens after the verb
    args = tokens[1:]

    # 1. Check denied flags
    for tok in args:
        tok_lower = tok.lower().strip("\"'")
        if tok_lower in rule.denied_flags:
            return False

    # 2. For git: check specific subcommand+flag combos
    if verb == "git" and args:
        subcmd = args[0].lower()
        remaining_lower = {a.lower() for a in args[1:]}
        for denied_sub, denied_flag in _GIT_DENIED_COMBOS:
            if subcmd == denied_sub:
                if not denied_flag or denied_flag in remaining_lower:
                    return False

    # 3. Check allowed subcommands (if non-empty, first non-flag arg must be one of them)
    if rule.allowed_subcommands:
        # Find first non-flag token
        first_arg = next(
            (a.lower() for a in args if not a.startswith("-")),
            None,
        )
        if first_arg is None:
            # No subcommand provided; allowed only if the verb doesn't require one
            # (e.g. git without subcommand is acceptable as a partial check)
            pass
        elif first_arg not in rule.allowed_subcommands:
            return False

    # 4. Python -m module check
    if verb in ("python", "python3", "py"):
        # Walk args; if -m is found, the next token must be an approved module
        for i, tok in enumerate(args):
            if tok.lower() == "-m" and i + 1 < len(args):
                module = args[i + 1].lower()
                if module not in _PYTHON_ALLOWED_MODULES:
                    return False
                break

    # 5. Path argument zone checks
    # Enforce when path_args_restricted=True OR allow_arbitrary_paths=False (BUG-015).
    # Commands like npm/yarn/pnpm with allow_arbitrary_paths=False will zone-check
    # any path-like argument even though path_args_restricted is False.
    if rule.path_args_restricted or not rule.allow_arbitrary_paths:
        for tok in args:
            stripped = tok.strip("\"'")
            # Skip pure flags
            if stripped.startswith("-"):
                continue
            # Skip environment assignment tokens
            if _ENV_ASSIGN_RE.match(stripped):
                continue
            # Dollar sign in any arg → unknown runtime value → deny
            if "$" in stripped:
                return False
            if _is_path_like(stripped):
                if not _check_path_arg(stripped, ws_root):
                    return False

    # 6. Shell redirect zone check (BUG-013 / BUG-016).
    # Three redirect forms are handled:
    #   a) standalone ">" / ">>"            → next token is the destination
    #   b) fd-prefixed operator "1>" / "2>" → next token is the destination
    #   c) embedded "evil>.github/f" or "1>.github/f" → right side of ">"
    _REDIRECT_OP_RE = re.compile(r'^[0-9]*>>?$')
    _EMBEDDED_REDIRECT_RE = re.compile(r'>>?(.+)$')
    for i, tok in enumerate(args):
        if _REDIRECT_OP_RE.match(tok):
            # Standalone redirect operator (plain or fd-prefixed); target is next token.
            if i + 1 < len(args):
                target = args[i + 1].strip("\"'")
                if "$" in target:
                    return False
                if _is_path_like(target):
                    if not _check_path_arg(target, ws_root):
                        return False
        else:
            # Embedded redirect: ">>" or ">" is part of the token itself.
            m = _EMBEDDED_REDIRECT_RE.search(tok)
            if m:
                target = m.group(1).strip("\"'")
                if "$" in target:
                    return False
                if _is_path_like(target):
                    if not _check_path_arg(target, ws_root):
                        return False

    # Step 7 — SAF-006: Recursive enumeration ancestor check
    is_recursive = (
        verb in _INHERENTLY_RECURSIVE_COMMANDS
        or _has_recursive_flag(verb, tokens)
    )
    if is_recursive:
        # Collect path arguments
        path_args = []
        for tok in args:
            stripped = tok.strip("\"'")
            if stripped.startswith("-"):
                continue
            if _ENV_ASSIGN_RE.match(stripped):
                continue
            path_args.append(stripped)

        # If no explicit path args, implied target is cwd (workspace root)
        if not path_args:
            path_args = ["."]

        for pa in path_args:
            if _is_ancestor_of_deny_zone(pa, ws_root):
                return False

    return True


def load_terminal_exceptions(hooks_dir: str) -> list[re.Pattern[str]]:
    """Load and compile exception patterns from terminal-exceptions.json.

    Returns a list of compiled patterns.  On any error (file absent,
    invalid JSON, invalid pattern), returns an empty list and logs to
    stderr so the hook continues safely.
    """
    exc_path = os.path.join(hooks_dir, "terminal-exceptions.json")
    if not os.path.isfile(exc_path):
        return []
    try:
        with open(exc_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[security_gate] terminal-exceptions.json load error: {exc}",
              file=sys.stderr)
        return []

    if not isinstance(data, dict):
        return []

    patterns: list[re.Pattern[str]] = []
    for entry in data.get("allowedPatterns", []):
        if not isinstance(entry, dict):
            continue
        raw_pattern = entry.get("pattern", "")
        if not isinstance(raw_pattern, str):
            continue
        # Security: patterns must be fully anchored (Section 12.3)
        if not (raw_pattern.startswith("^") and raw_pattern.endswith("$")):
            print(
                f"[security_gate] Skipping exception pattern without anchors: {raw_pattern!r}",
                file=sys.stderr,
            )
            continue
        try:
            patterns.append(re.compile(raw_pattern))
        except re.error as exc:
            print(
                f"[security_gate] Skipping invalid exception pattern {raw_pattern!r}: {exc}",
                file=sys.stderr,
            )
    return patterns


def sanitize_terminal_command(command: str, ws_root: str = "") -> tuple[str, Optional[str]]:
    """Analyze a terminal command string through the 5-stage pipeline.

    Returns:
        ("ask",  None)  — command passes all checks; requires human approval
        ("deny", str)   — command is blocked; str is the human-readable reason
    """
    try:
        # Stage 2 — normalize whitespace
        normalized = _normalize_terminal_command(command)
        if not normalized:
            return ("deny", "Empty command after normalization.")

        lowered = normalized.lower()

        # Stage 3 — obfuscation pre-scan (all 28 patterns, lowercased input)
        for pattern in _OBFUSCATION_PATTERNS:
            if pattern.search(lowered):
                return ("deny", f"Command blocked by obfuscation pre-scan: {_DENY_REASON}")

        # Stage 4 — split into segments; evaluate each independently
        segments = _split_segments(normalized)
        if not segments:
            return ("deny", "No executable segments found.")

        for segment in segments:
            tokens = _tokenize_segment(segment)
            if not tokens:
                # Could not tokenize — fail closed
                return ("deny", f"Command could not be parsed: {_DENY_REASON}")

            verb = _extract_verb(tokens)
            verb_lower = verb.lower()

            # Stage 4 — deny variable-substitution primary verbs
            if verb.startswith("$") or "${" in verb or "$(" in verb:
                return ("deny", f"Dynamic primary verb blocked: {_DENY_REASON}")

            # Stage 4 — normalize version aliases before allowlist lookup
            if re.match(r"^python3\.\d+$", verb_lower):
                verb_lower = "python3"
            elif re.match(r"^python\d+$", verb_lower) and verb_lower != "python3":
                # e.g. python2, python27 — not in allowlist
                pass
            elif re.match(r"^pip3\.\d+$", verb_lower):
                verb_lower = "pip3"

            # Lowercase the ls -R flag variant: ls -R vs ls -r both denied
            lowered_segment = segment.lower()

            # Stage 5 — allowlist lookup
            rule = _COMMAND_ALLOWLIST.get(verb_lower)

            if rule is None:
                # Verb not in allowlist — try escape hatch before denying
                hooks_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__))
                ) if ws_root == "" else os.path.join(ws_root, ".github", "hooks")

                try:
                    hooks_search = os.path.join(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                    exception_patterns = load_terminal_exceptions(hooks_search)
                except Exception:
                    exception_patterns = []

                matched_exception = any(
                    p.search(lowered_segment) for p in exception_patterns
                )
                if matched_exception:
                    # Residual checks still apply (Section 12.4)
                    for pat in _OBFUSCATION_PATTERNS:
                        if pat.search(lowered):
                            return ("deny", f"Exception-listed command blocked by obfuscation pre-scan: {_DENY_REASON}")
                    # Zone-check path args in the segment
                    for tok in tokens[1:]:
                        stripped = tok.strip("\"'")
                        if stripped.startswith("-"):
                            continue
                        if "$" in stripped:
                            return ("deny", f"Exception-listed command has variable path arg: {_DENY_REASON}")
                        if _is_path_like(stripped):
                            zone = zone_classifier.classify(stripped, ws_root)
                            if zone == "deny":
                                return ("deny", f"Exception-listed command targets restricted zone: {_DENY_REASON}")
                    continue  # this segment passes exception check; proceed to next segment

                return ("deny", f"Command '{verb}' is not on the approved allowlist. {_DENY_REASON}")

            # Stage 5 — argument validation
            # For ls, handle -R (capital) by lowercasing tokens
            lowered_tokens = [verb_lower] + [t.lower() for t in tokens[1:]]
            if not _validate_args(rule, verb_lower, lowered_tokens, ws_root):
                return ("deny", f"Command '{verb}' argument validation failed. {_DENY_REASON}")

            # Stage 5 fallback — explicit deny patterns
            for pat in _EXPLICIT_DENY_PATTERNS:
                if pat.search(lowered_segment):
                    return ("deny", f"Command blocked by destructive-pattern check: {_DENY_REASON}")

        return ("ask", None)

    except Exception:
        # Any unexpected error → fail closed
        return ("deny", _DENY_REASON)


# ---------------------------------------------------------------------------
# SAF-003: Search tool parameter validation
# ---------------------------------------------------------------------------

def _is_truthy_flag(value: object) -> bool:
    """Return True if *value* represents an enabled boolean flag.

    Handles bool True, the string "true" (any case), and integer 1.
    All other values — including None, False, "false", 0 — return False.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    if isinstance(value, int):
        return value == 1
    return False


def _expand_braces(pattern: str) -> list[str]:
    """Expand shell-style brace groups {a,b,c} into all permutations."""
    match = re.search(r'\{([^{}]+)\}', pattern)
    if not match:
        return [pattern]
    prefix = pattern[:match.start()]
    suffix = pattern[match.end():]
    alternatives = match.group(1).split(',')
    results = []
    for alt in alternatives:
        results.extend(_expand_braces(prefix + alt + suffix))
    return results


def _validate_include_pattern(pattern: str, ws_root: str) -> str:
    """Validate a grep_search ``includePattern`` glob value.

    Normalizes the pattern, checks for residual ``..`` traversal sequences,
    and delegates zone membership to ``zone_classifier.classify()``.

    Returns ``"deny"`` if the pattern targets a deny zone or encodes a path
    traversal attempt.  Returns ``"allow"`` otherwise.
    """
    # Normalize using zone_classifier's implementation (strips control chars,
    # handles backslashes, resolves '..' sequences where possible).
    normalized = zone_classifier.normalize_path(pattern)

    # If '..' remains after normpath the sequence escapes the workspace root —
    # this is always a traversal attempt regardless of the destination.
    if ".." in normalized:
        return "deny"

    # Expand brace groups and check each expansion for deny zone access
    for expanded in _expand_braces(pattern):
        expanded_norm = zone_classifier.normalize_path(expanded)
        if ".." in expanded_norm:
            return "deny"
        if zone_classifier.classify(expanded, ws_root) == "deny":
            return "deny"

    # Delegate zone membership: covers both Method 1 (relative_to) and
    # Method 2 (regex pattern scan) inside zone_classifier.
    if zone_classifier.classify(pattern, ws_root) == "deny":
        return "deny"

    return "allow"


def validate_grep_search(data: dict, ws_root: str) -> str:
    """SAF-003: Validate ``grep_search`` tool parameters prior to execution.

    Inspects ``includePattern`` and ``includeIgnoredFiles`` to close the
    bypass vectors identified in audit findings 2 and 3.

    Supports both the VS Code hook nested format (parameters inside
    ``tool_input``) and the flat test format (parameters at the top level).

    Returns ``"deny"``, ``"ask"``, or ``"allow"``.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Prefer nested tool_input key (VS Code hook format); fall back to
    # top-level dict key (test / legacy hook format).
    def _param(key: str) -> object:
        val = tool_input.get(key)
        if val is None:
            val = data.get(key)
        return val

    # includeIgnoredFiles=true bypasses normal file-hiding mechanisms — deny
    # to prevent access to files that are intentionally kept from indexing.
    if _is_truthy_flag(_param("includeIgnoredFiles")):
        return "deny"

    # includePattern is a glob path filter that constrains which files are
    # searched.  Deny if it targets a protected zone or encodes a traversal.
    include_pattern = _param("includePattern")
    if isinstance(include_pattern, str) and include_pattern:
        if _validate_include_pattern(include_pattern, ws_root) == "deny":
            return "deny"

    # Standard path zone check on any explicit file-path field present in
    # the payload (e.g. a filePath passed alongside the query).
    raw_path = extract_path(data)
    if raw_path is None:
        return "ask"
    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "deny":
        return "deny"
    if zone == "allow":
        return "allow"
    return "ask"


def validate_semantic_search(data: dict, ws_root: str) -> str:
    """SAF-003: Validate ``semantic_search`` tool call.

    ``semantic_search`` indexes the entire workspace with no path-restriction
    parameter.  Every call is returned as ``"ask"`` so that a human must
    review and approve it before execution, preventing automated leakage of
    protected file content.

    The ``data`` and ``ws_root`` parameters are accepted for API consistency
    but are not used in the current policy.
    """
    return "ask"


# ---------------------------------------------------------------------------
# SAF-007: Write restriction — file write tools outside Project/ are denied
# ---------------------------------------------------------------------------

def validate_write_tool(data: dict, ws_root: str) -> str:
    """SAF-007: Validate file write tool calls.

    Only allows writes to paths inside Project/ (zone == "allow").
    All other zones — including "ask" (src/, docs/, tests/) and "deny"
    (.github/, .vscode/, NoAgentZone/) — are denied.

    When no path is found in the payload, fails closed and returns "deny".
    """
    raw_path = extract_path(data)
    if raw_path is None:
        # No path field → fail closed
        return "deny"

    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# SAF-006: Recursive enumeration protection
# ---------------------------------------------------------------------------

# Commands that are inherently recursive (always enumerate subdirectories)
_INHERENTLY_RECURSIVE_COMMANDS: frozenset = frozenset({"tree", "find"})

# Commands that become recursive when specific flags are present
_RECURSIVE_FLAG_MAP: dict[str, frozenset[str]] = {
    "ls": frozenset({"-r", "--recursive"}),
    "dir": frozenset({"/s"}),
    "get-childitem": frozenset({"-recurse", "-r"}),
    "gci": frozenset({"-recurse", "-r"}),
}


def _is_ancestor_of_deny_zone(path: str, ws_root: str) -> bool:
    """Return True if *path* is an ancestor of any deny zone.

    A path is an ancestor of a deny zone if the deny zone path starts with
    the given path. The workspace root itself is an ancestor since deny zones
    (.github/, .vscode/, NoAgentZone/) are direct children of the root.
    """
    norm = normalize_path(path) if path else ws_root
    # Handle relative paths
    if not norm or norm == ".":
        norm = ws_root
    elif not (len(norm) >= 2 and norm[1] == ":") and not norm.startswith("/"):
        # Relative path — join with workspace root
        norm = posixpath.normpath(f"{ws_root}/{norm}")

    ws = ws_root.rstrip("/")
    deny_zones = [
        f"{ws}/.github",
        f"{ws}/.vscode",
        f"{ws}/noagentzone",
    ]

    # Check if norm is an ancestor of any deny zone
    # A is ancestor of B if B starts with A/ or A == B
    norm_stripped = norm.rstrip("/")
    for dz in deny_zones:
        if dz.startswith(norm_stripped + "/") or dz == norm_stripped:
            return True
        # Also check if norm IS a deny zone or inside one
        if norm_stripped.startswith(dz + "/") or norm_stripped == dz:
            return True

    return False


def _has_recursive_flag(verb_lower: str, tokens: list[str]) -> bool:
    """Check if the command has recursive flags, including combined POSIX flags.

    Handles combined short flags like 'ls -lR' where -R is embedded.
    """
    flags = _RECURSIVE_FLAG_MAP.get(verb_lower)
    if not flags:
        return False

    for tok in tokens[1:]:
        tok_lower = tok.lower().strip("\"'")
        # Direct match
        if tok_lower in flags:
            return True
        # Combined POSIX short flag check (e.g., -lR, -alR, -Rl)
        if verb_lower in ("ls",) and tok_lower.startswith("-") and not tok_lower.startswith("--"):
            flag_chars = tok_lower[1:]
            if "r" in flag_chars:
                return True
        if verb_lower in ("get-childitem", "gci") and tok_lower.startswith("-") and not tok_lower.startswith("--"):
            flag_chars = tok_lower[1:]
            if "r" in flag_chars:
                return True

    return False


# ---------------------------------------------------------------------------
# Decision engine
# ---------------------------------------------------------------------------

def decide(data: dict, ws_root: str) -> str:
    tool_name = extract_tool_name(data)

    # Always-allow tools bypass all zone checks
    if tool_name in _ALWAYS_ALLOW_TOOLS:
        return "allow"

    # Terminal tools: full command allowlist sanitization (SAF-005)
    if tool_name in _TERMINAL_TOOLS:
        tool_input = data.get("tool_input") or {}
        if not isinstance(tool_input, dict):
            tool_input = {}
        # Look for command in tool_input first (VS Code hook format), then
        # fall back to the top-level data dict (supports older test structures).
        command = tool_input.get("command") or data.get("command") or ""
        if not isinstance(command, str) or not command.strip():
            # No command field, or empty command → fail closed
            return "deny"
        decision, _reason = sanitize_terminal_command(command, ws_root)
        return decision

    # SAF-003: Search tool parameter validation — must run before the
    # _EXEMPT_TOOLS block so that includePattern / includeIgnoredFiles are
    # inspected even though both tools appear in _EXEMPT_TOOLS.
    if tool_name == "semantic_search":
        return validate_semantic_search(data, ws_root)
    if tool_name == "grep_search":
        return validate_grep_search(data, ws_root)

    # SAF-007: Write tools are restricted to Project/ only.  Any write
    # targeting a path outside Project/ is denied, even if zone would be "ask".
    if tool_name in _WRITE_TOOLS:
        return validate_write_tool(data, ws_root)

    # Non-exempt tools (non-empty name not in exempt set): always ask
    if tool_name and tool_name not in _EXEMPT_TOOLS:
        return "ask"

    # Exempt tool or unknown tool name: resolve path and check zone
    raw_path = extract_path(data)
    if raw_path is None:
        return "ask"

    # SAF-002: zone_classifier.classify() handles normalization and
    # relative-path resolution internally.
    zone = zone_classifier.classify(raw_path, ws_root)
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
