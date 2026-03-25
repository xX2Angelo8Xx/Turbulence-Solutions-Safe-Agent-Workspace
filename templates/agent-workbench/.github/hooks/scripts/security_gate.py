from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import os
import posixpath
import re
import unicodedata
import shlex
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

# SAF-002: zone classification is delegated to the dedicated module.
# FIX-069: The Python embeddable distribution (ts-python shim) ships with a
# ._pth file that restricts sys.path and does NOT add the script directory.
# Insert the script directory explicitly so zone_classifier is always importable
# regardless of whether security_gate.py is invoked via standard or embedded Python.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import zone_classifier

# ---------------------------------------------------------------------------
# Tool classification sets
# ---------------------------------------------------------------------------

_ALWAYS_ALLOW_TOOLS: frozenset = frozenset({
    "vscode_ask_questions", "ask_questions",
    "TodoWrite", "TodoRead", "todo_write", "manage_todo_list",
    # SAF-044: search_subagent removed — validated by validate_search_subagent() in decide()
    "runSubagent", "Agent", "agent",
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
    "get_errors",  # SAF-023: handled early in decide(); listed here to pass unknown-tool guard
    # SAF-038: memory and create_directory — handled early in decide(); zone-checked to project folder
    "memory", "create_directory",
    # SAF-039: VS Code LSP tools — handled early in decide(); zone-checked to project folder
    "vscode_listCodeUsages", "vscode_renameSymbol",
    # FIX-035: VS Code/Copilot deferred development tools — safe to allow;
    # handled early in decide() before the path-check block.
    "install_python_packages", "configure_python_environment", "fetch_webpage",
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


# ---------------------------------------------------------------------------
# SAF-008: File integrity verification constants
# ---------------------------------------------------------------------------
# Known-good SHA256 of templates/coding/.vscode/settings.json.
# Updated by running .github/hooks/scripts/update_hashes.py after any
# intentional admin change to settings.json.
_KNOWN_GOOD_SETTINGS_HASH: str = "c75f433e700610db8d5531cb8a9c499ed75e28d8aeb15014cdfb40cf69d156b4"

# Known-good SHA256 of security_gate.py in canonical form.
# Canonical form: the file content with the value portion of this constant
# replaced by 64 zeros before hashing.  This makes the hash independent of
# the stored value while detecting all other modifications.
# Updated by running .github/hooks/scripts/update_hashes.py.
_KNOWN_GOOD_GATE_HASH: str = "ef030b7f6621993751cefcb2df0378b7850e146744772dfae9d91e25fd52e2b3"

_INTEGRITY_WARNING: str = (
    "SECURITY ALERT: Integrity verification failed. A safety-critical file "
    "(.vscode/settings.json or security_gate.py) has been modified or "
    "corrupted. All tool calls are blocked. An administrator must review the "
    "changes and run update_hashes.py to re-approve the security files."
)

_DENY_REASON = "Access denied. This action has been blocked by the workspace security policy."


# ---------------------------------------------------------------------------
# SAF-035: Session denial counter constants
# ---------------------------------------------------------------------------

# Default maximum denials before a session is locked.
_DENY_THRESHOLD_DEFAULT: int = 20

# Default: counter is active unless config disables it.
_COUNTER_ENABLED_DEFAULT: bool = True

# File names (relative to the scripts directory)
_STATE_FILE_NAME: str = ".hook_state.json"
_OTEL_JSONL_NAME: str = "copilot-otel.jsonl"
_COUNTER_CONFIG_NAME: str = "counter_config.json"


# ---------------------------------------------------------------------------
# SAF-005: Terminal command sanitization constants
# ---------------------------------------------------------------------------

# Stage 3 — 28 obfuscation pre-scan patterns (Section 6 + Section 10)
# Applied against the LOWERCASED command string.  Any match → immediate deny.
_OBFUSCATION_PATTERNS: list[re.Pattern[str]] = [
    # P-01 to P-09: interpreter chaining flags
    # SAF-017: P-01 (python -c) removed — allowed when cwd is inside project folder
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
# NOTE: rm, del, erase, rmdir, remove-item, ri are intentionally absent —
# they are now in _COMMAND_ALLOWLIST (Category N) with path_args_restricted=True
# and are zone-checked there rather than hard-denied here.
_EXPLICIT_DENY_PATTERNS: list[re.Pattern[str]] = [
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
    re.compile(r"update_hashes"),  # SAF-033: block any command containing 'update_hashes' (substring, case-insensitive via lowered_segment)
]


# FIX-034: Pre-scan pattern for venv activation commands.
# Detected BEFORE Stage 3 obfuscation patterns so that `source` (P-22) and
# POSIX dot-source (P-23) false-positives on legitimate activations are avoided.
# Also handles the PowerShell call-operator form (& path\Activate.ps1) whose
# verb would otherwise reach the unknown-verb deny path.
# Matches both forward-slash and back-slash path separators (re.IGNORECASE).
_VENV_ACTIVATION_SEG_RE: re.Pattern[str] = re.compile(
    r'^(?:&\s+|source\s+|\.\s+)?'           # optional: & / source / POSIX dot (with space)
    r'(?P<path>'
    r'(?:[^\s]*[/\\])?'                       # optional directory prefix ending with separator
    r'\.?venv'                                # .venv or venv directory name
    r'[/\\]'                                  # separator after venv dir
    r'(?:scripts?[/\\]activate(?:\.(?:bat|ps1))?'   # Windows/PS: Scripts/activate[.bat|.ps1]
    r'|bin[/\\]activate)'                            # Unix: bin/activate
    r')'
    r'\s*$',
    re.IGNORECASE,
)


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
        # SAF-017: -c removed from denied_flags; python -c "..." allowed inside project folder
        denied_flags=frozenset({"-i", "--interactive"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="python3.x aliases normalized to python; -m restricted to approved modules",
    ),
    "python3": CommandRule(
        # SAF-017: -c removed from denied_flags; python3 -c "..." allowed inside project folder
        denied_flags=frozenset({"-i", "--interactive"}),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="python3.x aliases normalized to python3",
    ),
    "py": CommandRule(
        # SAF-017: -c removed from denied_flags; py -c "..." allowed inside project folder
        denied_flags=frozenset({"-i", "--interactive"}),
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
            "fetch", "pull", "push", "checkout", "switch", "stash", "tag",
            "show", "remote", "blame", "config", "init", "clone", "merge",
            "rebase", "describe", "shortlog", "rev-parse", "ls-files",
        }),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="push --force denied; filter-branch/gc --force/reset --hard/clean -f denied",
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
    # SAF-040: additional read-only commands completing AC 1 of US-036
    "diff": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix diff; path args zone-checked",
    ),
    "fc": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows file compare; path args zone-checked",
    ),
    "comp": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows binary compare; path args zone-checked",
    ),
    "sort": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Sort input/file; path args zone-checked",
    ),
    "uniq": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Filter duplicate lines; path args zone-checked",
    ),
    "awk": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Awk text processing; file path args zone-checked",
    ),
    "sed": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Sed stream editor (read mode); file path args zone-checked",
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
    # SAF-047: Get-Location prints CWD; no path args needed
    "get-location": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="PowerShell Get-Location; prints CWD",
    ),
    "gl": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=False,
        allow_arbitrary_paths=True,
        notes="Alias for Get-Location",
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
    # SAF-041: shell utility commands completing ACs 2-4 of US-036
    "touch": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Create/update files inside project folder; path args zone-checked",
    ),
    "chmod": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Non-Windows permission change; target path zone-checked",
    ),
    "ln": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Symbolic/hard links; both source and target path args zone-checked",
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
    # Category L — Read-only file inspection commands (SAF-014)
    "get-content": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Get-Content; path args zone-checked",
    ),
    "gc": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Get-Content; path args zone-checked",
    ),
    "select-string": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Select-String; path args zone-checked",
    ),
    "findstr": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows findstr; path args zone-checked",
    ),
    "grep": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix grep; path args zone-checked",
    ),
    "wc": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix word/line count; path args zone-checked",
    ),
    "file": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix file type detection; path args zone-checked",
    ),
    "stat": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix/Windows file info; path args zone-checked",
    ),
    # Category M — Write file commands (SAF-015)
    "set-content": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Set-Content; path args zone-checked",
    ),
    "sc": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Set-Content; path args zone-checked",
    ),
    "add-content": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Add-Content; path args zone-checked",
    ),
    "ac": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Add-Content; path args zone-checked",
    ),
    "out-file": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Out-File; path args zone-checked",
    ),
    "rename-item": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Rename-Item; source and dest zone-checked",
    ),
    "ren": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Rename-Item; path args zone-checked",
    ),
    "tee-object": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Tee-Object; output file path zone-checked",
    ),
    "tee": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix tee; output file path zone-checked",
    ),
    "ni": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for New-Item; path args zone-checked",
    ),
    # Category N — Delete commands (SAF-016)
    # path_args_restricted=True: ALL path args must be inside project folder.
    # When ANY path arg resolves outside, _validate_args returns False → deny.
    "remove-item": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="PowerShell Remove-Item; all path args zone-checked",
    ),
    "ri": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Alias for Remove-Item; all path args zone-checked",
    ),
    "rm": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix/POSIX rm; all path args zone-checked",
    ),
    "del": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows del; all path args zone-checked",
    ),
    "erase": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Windows erase (alias for del); all path args zone-checked",
    ),
    "rmdir": CommandRule(
        denied_flags=frozenset(),
        allowed_subcommands=frozenset(),
        path_args_restricted=True,
        allow_arbitrary_paths=False,
        notes="Unix/Windows rmdir; all path args zone-checked",
    ),
}

# Allowed Python -m modules (Section 7.2 Category A sub-rules)
# SAF-017: added "venv" — path arg is zone-checked in _validate_args
_PYTHON_ALLOWED_MODULES: frozenset[str] = frozenset({
    "pytest", "build", "pip", "setuptools", "hatchling", "venv",
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
# SAF-035: Session denial counter helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.datetime.utcnow().isoformat() + "Z"


def _read_otel_session_id(scripts_dir: str) -> "Optional[str]":
    """Extract session ID from the OTel JSONL export file (last non-empty line).

    Looks for ``session.id`` in resource attributes first; falls back to
    ``gen_ai.conversation.id`` in the first span's attributes.
    Returns None when the file does not exist, is empty, or cannot be parsed.
    """
    otel_path = os.path.join(scripts_dir, _OTEL_JSONL_NAME)
    try:
        if not os.path.isfile(otel_path):
            return None

        # Read the last non-empty line (tail approach — most recent span)
        last_line: "Optional[str]" = None
        with open(otel_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped:
                    last_line = stripped

        if not last_line:
            return None

        span = json.loads(last_line)
        if not isinstance(span, dict):
            return None

        resource_spans = span.get("resourceSpans")
        if not isinstance(resource_spans, list) or not resource_spans:
            return None

        first_rs = resource_spans[0]
        if not isinstance(first_rs, dict):
            return None

        # Attempt 1: session.id from resource attributes
        resource = first_rs.get("resource", {})
        if isinstance(resource, dict):
            for attr in resource.get("attributes", []):
                if (
                    isinstance(attr, dict)
                    and attr.get("key") == "session.id"
                ):
                    value = attr.get("value", {})
                    if isinstance(value, dict):
                        sid = value.get("stringValue", "")
                        if isinstance(sid, str) and sid:
                            return sid

        # Attempt 2: gen_ai.conversation.id from the first span's attributes
        scope_spans = first_rs.get("scopeSpans")
        if isinstance(scope_spans, list) and scope_spans:
            spans = scope_spans[0].get("spans") if isinstance(scope_spans[0], dict) else None
            if isinstance(spans, list) and spans:
                first_span = spans[0]
                if isinstance(first_span, dict):
                    for attr in first_span.get("attributes", []):
                        if (
                            isinstance(attr, dict)
                            and attr.get("key") == "gen_ai.conversation.id"
                        ):
                            value = attr.get("value", {})
                            if isinstance(value, dict):
                                sid = value.get("stringValue", "")
                                if isinstance(sid, str) and sid:
                                    return sid

        return None
    except (OSError, json.JSONDecodeError, IndexError, KeyError,
            AttributeError, TypeError, ValueError):
        return None


def _load_state(state_path: str) -> dict:
    """Load hook state from JSON file.  Returns empty dict on any error."""
    try:
        if not os.path.isfile(state_path):
            return {}
        with open(state_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _load_counter_config(scripts_dir: str) -> dict:
    """Load counter configuration from counter_config.json.

    Returns a dict with keys 'counter_enabled' (bool) and 'lockout_threshold' (int).
    Falls back to defaults on any error (missing file, corrupt JSON, invalid types).
    """
    defaults = {
        "counter_enabled": _COUNTER_ENABLED_DEFAULT,
        "lockout_threshold": _DENY_THRESHOLD_DEFAULT,
    }
    config_path = os.path.join(scripts_dir, _COUNTER_CONFIG_NAME)
    try:
        if not os.path.isfile(config_path):
            return dict(defaults)
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return dict(defaults)
        enabled = data.get("counter_enabled", _COUNTER_ENABLED_DEFAULT)
        threshold = data.get("lockout_threshold", _DENY_THRESHOLD_DEFAULT)
        if not isinstance(enabled, bool):
            enabled = _COUNTER_ENABLED_DEFAULT
        if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
            threshold = _DENY_THRESHOLD_DEFAULT
        return {"counter_enabled": enabled, "lockout_threshold": threshold}
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return dict(defaults)


def _save_state(state_path: str, state: dict) -> None:
    """Save hook state using an atomic write (temp file → rename)."""
    dir_path = os.path.dirname(state_path)
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=dir_path, suffix=".tmp", prefix=".hook_state_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(state, fh, indent=2)
            os.replace(tmp_path, state_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception:
        # Best-effort — counter is non-blocking; silently skip on write failure
        pass


def _get_session_id(scripts_dir: str, state: dict) -> "tuple[str, dict]":
    """Resolve the active session ID.

    Returns the session ID from the OTel JSONL file when available.
    Falls back to a persisted UUID4 stored in the state dict; creates one
    if none exists yet.  The (possibly modified) state dict is returned as
    the second element so the caller can persist it.
    """
    otel_sid = _read_otel_session_id(scripts_dir)
    if otel_sid:
        return otel_sid, state

    # Fallback: reuse or create a UUID4-based session ID
    fallback_id = state.get("_fallback_session_id")
    if not isinstance(fallback_id, str) or not fallback_id:
        fallback_id = str(uuid.uuid4())
        state["_fallback_session_id"] = fallback_id
        state["_fallback_created"] = _utc_now_iso()

    return fallback_id, state


def _increment_deny_counter(
    state: dict, session_id: str, threshold: int
) -> "tuple[int, bool]":
    """Increment the deny counter for *session_id*.

    Returns ``(new_deny_count, now_locked)`` where *now_locked* is True if
    this increment reaches or exceeds *threshold*.
    """
    if session_id not in state or not isinstance(state[session_id], dict):
        state[session_id] = {"deny_count": 0, "locked": False, "timestamp": ""}

    entry = state[session_id]
    entry["deny_count"] = entry.get("deny_count", 0) + 1
    entry["timestamp"] = _utc_now_iso()

    now_locked = entry["deny_count"] >= threshold
    if now_locked:
        entry["locked"] = True

    return entry["deny_count"], now_locked


# ---------------------------------------------------------------------------
# SAF-008: File integrity helpers
# ---------------------------------------------------------------------------

def _compute_file_hash(path: str) -> "Optional[str]":
    """Compute the SHA256 hex digest of a file.  Returns None on any error."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _compute_gate_canonical_hash(gate_path: str) -> "Optional[str]":
    """Compute SHA256 of security_gate.py with the gate-hash constant zeroed.

    The canonical form replaces the 64-char hex value of _KNOWN_GOOD_GATE_HASH
    with 64 zeros before hashing.  This makes the result independent of the
    stored hash value while detecting any other modification to the file.
    """
    try:
        with open(gate_path, "rb") as fh:
            content_bytes = fh.read()
        canonical = re.sub(
            rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
            b"0" * 64,
            content_bytes,
        )
        return hashlib.sha256(canonical).hexdigest()
    except (OSError, re.error):
        return None


def verify_file_integrity() -> bool:
    """SAF-008: Verify SHA256 hashes of security-critical files on startup.

    Checks both .vscode/settings.json and this script against their
    known-good hashes.  Returns True only when both match.  Fails closed -
    returns False on any I/O error or unexpected exception.
    """
    try:
        gate_path = os.path.abspath(__file__)
        scripts_dir = os.path.dirname(gate_path)
        # Path layout: scripts/ -> hooks/ -> .github/ -> workspace_root/
        workspace_root = os.path.dirname(
            os.path.dirname(os.path.dirname(scripts_dir))
        )
        settings_path = os.path.join(workspace_root, ".vscode", "settings.json")

        # 1. Verify settings.json
        settings_hash = _compute_file_hash(settings_path)
        if settings_hash is None or settings_hash != _KNOWN_GOOD_SETTINGS_HASH:
            return False

        # 2. Verify security_gate.py using canonical form
        gate_hash = _compute_gate_canonical_hash(gate_path)
        if gate_hash is None or gate_hash != _KNOWN_GOOD_GATE_HASH:
            return False

        return True
    except Exception:
        # Any unexpected error -> fail closed
        return False


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

# SAF-020: Deny zone names (lowercase) used for wildcard prefix matching.
# A wildcard token whose prefix matches the start of any of these names is denied.
_WILDCARD_DENY_ZONES: tuple[str, ...] = (".github", ".vscode", "noagentzone")


def _is_path_like(token: str) -> bool:
    """Return True if *token* looks like a file-system path argument."""
    # SAF-030: bare tilde and tilde-prefixed paths expand to HOME (outside project)
    if token == "~" or token.startswith("~/") or token.startswith("~\\"):
        return True
    return bool(_PATH_LIKE_RE.search(token)) or token.startswith(".")


def _wildcard_prefix_matches_deny_zone(token: str) -> bool:
    """SAF-020: Return True if a wildcard token could expand to a deny zone.

    Conservative algorithm:
    1. Normalize token to lowercase forward-slash form.
    2. Split into path components.
    3. Walk components; track whether we have entered a non-deny directory.
    4. For the first wildcard component: if no non-deny parent was entered,
       check if any deny zone name starts with the prefix before the wildcard.
       A blank prefix (e.g. *.py at root) matches every deny zone — deny.
    5. If any parent component IS a deny zone, deny.
    6. Wildcards nested inside a non-deny parent (e.g. Project/*.py) are safe.

    .. and empty components are treated as transparent (do not constitute a
    safe parent directory).
    """
    if "*" not in token and "?" not in token and "[" not in token:
        return False

    # Normalize to lowercase forward-slash for consistent matching
    normalized = token.replace("\\", "/").lower()
    parts = normalized.split("/")

    entered_safe_dir = False  # True once we step into a non-deny directory

    for part in parts:
        if "*" not in part and "?" not in part and "[" not in part:
            # Non-wildcard component — classify it
            clean = part.strip()
            if clean in ("", ".", ".."):
                # Transparent: dot, double-dot, or empty — do not mark as safe
                continue
            if clean in _WILDCARD_DENY_ZONES:
                # Explicit deny zone in the path prefix — deny immediately
                return True
            # Entered a non-deny, non-transparent directory
            entered_safe_dir = True
        else:
            # Wildcard component — extract the prefix before the first wildcard
            wc_pos = min(part.find(c) for c in ("*", "?", "[") if c in part)
            comp_prefix = part[:wc_pos]

            if entered_safe_dir:
                # Wildcard is inside a non-deny parent directory — safe
                return False

            # Wildcard is at root level (or after only transparent components).
            # Deny if any deny zone name starts with the component prefix.
            # An empty prefix (e.g. "*.py") matches every deny zone → deny.
            for zone in _WILDCARD_DENY_ZONES:
                if zone.startswith(comp_prefix):
                    return True

            # Prefix does not match any deny zone at this level — safe
            return False

    return False


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
    - SAF-020: Token contains wildcards that could resolve to a deny zone
    - Resolved path zone returns 'deny'
    """
    if "$" in token:
        return False
    # SAF-020: Wildcard bypass prevention (defense in depth)
    if _wildcard_prefix_matches_deny_zone(token):
        return False
    if not _is_path_like(token):
        return True  # not a path; no zone concern
    # Resolve relative paths against workspace root, then zone-check
    norm = posixpath.normpath(
        token.replace("\\", "/")
    )
    zone = zone_classifier.classify(norm, ws_root)
    return zone != "deny"


def _check_workspace_path_arg(token: str, ws_root: str) -> bool:
    """Return True if *token* is a safe path for workspace-scoped terminal commands.

    SAF-047: Terminal commands are workspace-scoped per AGENT-RULES §4.
    Allows paths within the workspace root; denies paths outside or targeting
    protected zones (.github, .vscode, noagentzone at any depth).
    """
    if "$" in token:
        return False
    # SAF-020: Wildcard bypass prevention (defense in depth)
    if _wildcard_prefix_matches_deny_zone(token):
        return False
    if not _is_path_like(token):
        return True  # not a path; no zone concern
    norm = posixpath.normpath(token.replace("\\", "/"))
    # SAF-030: Deny tilde — expands to home directory at shell runtime (outside workspace)
    if norm == "~" or norm.startswith("~/") or re.match(r"^~[^/]", norm):
        return False
    ws_clean = ws_root.rstrip("/")
    # Resolve relative paths against workspace root
    if not (re.match(r"^[a-z]:", norm.lower()) or norm.startswith("/")):
        norm = posixpath.normpath(ws_clean + "/" + norm)
    norm_lower = norm.lower()
    ws_lower = ws_clean.lower()
    # Must be within workspace root (or be the workspace root itself)
    if not (norm_lower.startswith(ws_lower + "/") or norm_lower == ws_lower):
        return False
    # Must not target protected zones at any depth in the path
    rel = norm_lower[len(ws_lower):].strip("/")
    for part in rel.split("/"):
        if part in (".github", ".vscode", "noagentzone"):
            return False
    return True


# FIX-022: Verb category safe for project-folder fallback (read/execute only).
# Destructive commands (rm, del, remove-item, etc.) are intentionally excluded
# to prevent `rm ./root_config.json` from being mis-classified as project-local.
# FIX-032: PS write cmdlets and copy/move cmdlets added — fallback only allows
# paths that resolve inside the project folder, so write access to restricted
# zones cannot be granted via this path.
_PROJECT_FALLBACK_VERBS: frozenset[str] = frozenset({
    "python", "python3", "py", "pip", "pip3",
    "cat", "type", "get-content", "gc", "select-string",
    "findstr", "grep", "wc", "file", "stat",
    "get-childitem", "gci", "ls", "dir",
    "more", "head", "tail", "less",
    "pytest", "mypy", "flake8", "black", "isort", "ruff",
    "code", "dotnet", "node", "npm", "npx",
    # FIX-032: PS write cmdlets — zone-checked, project-folder fallback allowed
    "set-content", "sc", "add-content", "ac", "out-file",
    # FIX-032: Copy/move cmdlets — both source and dest zone-checked
    "copy-item", "cp", "copy", "mv", "move", "move-item",
    # SAF-041: shell utility commands — path args zone-checked
    "touch", "chmod", "ln",
    # SAF-047: git commands are workspace-scoped per AGENT-RULES §4
    "git",
})

# SAF-029: PowerShell delete cmdlets that receive project-folder fallback for
# single-segment dot-prefix paths only (e.g. .venv, .git, .pytest_cache, .env).
# Unix rm/del/erase/rmdir are intentionally excluded — FIX-033 requires
# `rm .env` to be denied and the full rm family must not get path fallback.
_DELETE_DOT_FALLBACK_VERBS: frozenset[str] = frozenset({"remove-item", "ri"})


def _try_project_fallback(norm_relative: str, ws_root: str) -> bool:
    """Try resolving a relative path against the detected project folder.

    When the agent CWD is the project folder, relative paths like
    ``src/app.py`` resolve against ws_root as ``ws_root/src/app.py``
    (outside the project) instead of ``ws_root/<project>/src/app.py``.
    This helper retries classification with the project prefix.

    Returns True only if the path resolves inside the project folder.
    """
    # Only handle truly relative paths
    if re.match(r"^[a-z]:", norm_relative.lower()) or norm_relative.startswith("/"):
        return False
    # SAF-047: Reject URL-like tokens (e.g. https:/evil.com after posixpath.normpath
    # strips the double slash from https://evil.com).  URLs are not filesystem paths.
    if re.match(r"^[a-z][a-z0-9+\-.]*:/", norm_relative):
        return False
    parts = [p for p in norm_relative.split("/") if p and p not in (".", "..")]
    if not parts or parts[0] == "~":
        return False
    # Never fallback into a deny zone
    if any(p.lower() in (".github", ".vscode", "noagentzone") for p in parts):
        return False
    try:
        project_dir = zone_classifier.detect_project_folder(Path(ws_root))
        project_path = posixpath.normpath(
            ws_root.rstrip("/") + "/" + project_dir + "/" + norm_relative
        )
        return zone_classifier.classify(project_path, ws_root) == "allow"
    except (RuntimeError, OSError):
        return False


# SAF-026: Scan inline Python code passed via -c for dangerous patterns.
def _scan_python_inline_code(code_str: str) -> bool:
    """Return True if inline Python code is safe, False if dangerous patterns detected."""
    low = code_str.lower()

    # Category A: Deny-zone paths
    for zone in ("noagentzone", ".github", ".vscode"):
        if zone in low:
            return False

    # Category B: Obfuscation/encoding
    for pat in ("base64", "b64decode", "codecs", "fromhex(", "bytearray(", "chr("):
        if pat in low:
            return False

    # Category C: Network
    for net in ("urllib", "http", "socket", "ftplib", "smtplib", "xmlrpc"):
        if net in low:
            return False
    if re.search(r'\brequests\b', low):
        return False

    # Category D: Filesystem escape
    for esc in ("expanduser", "expandvars"):
        if esc in low:
            return False
    if "../" in low or "..\\" in low or "..\\\\" in code_str:
        return False
    if re.search(r'(?:^|["\x27\s,=(])/(?:etc|usr|home|tmp|var|root|opt|mnt|dev)\b', low):
        return False
    if re.search(r'[A-Za-z]:\\', code_str):
        return False

    # Category E: Infrastructure
    for infra in ("update_hashes", "security_gate", "zone_classifier", "require-approval", "require_approval"):
        if infra in low:
            return False

    # Category F: Dynamic execution
    for dyn in ("__import__", "importlib", "eval(", "exec(", "getattr(", "setattr(", "delattr("):
        if dyn in low:
            return False
    # compile( is dangerous unless it is re.compile(
    if "compile(" in low and not re.search(r're\.compile\(', low):
        return False

    return True


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

    # FIX-023: Track arg indices already validated by step 4 so step 5 skips them
    _step4_validated_indices: set[int] = set()

    # 4. Python -m module check
    if verb in ("python", "python3", "py"):
        # Walk args; if -m is found, the next token must be an approved module
        for i, tok in enumerate(args):
            if tok.lower() == "-m" and i + 1 < len(args):
                module = args[i + 1].lower()
                if module not in _PYTHON_ALLOWED_MODULES:
                    return False
                # SAF-017: for 'venv', zone-check the target path argument
                if module == "venv" and i + 2 < len(args):
                    venv_target = args[i + 2].strip("\"'")
                    if "$" in venv_target:
                        return False
                    if _is_path_like(venv_target) and not _check_path_arg(venv_target, ws_root):
                        # FIX-023: Try project-folder fallback for venv target
                        norm_vt = posixpath.normpath(venv_target.replace("\\", "/"))
                        if not _try_project_fallback(norm_vt, ws_root):
                            return False
                    _step4_validated_indices.add(i + 2)
                # BUG-049: python -m pip install must apply the same VIRTUAL_ENV guard
                if module in ("pip", "pip3"):
                    remaining_args = args[i + 2:]
                    pip_subcmd = next(
                        (a.lower() for a in remaining_args if not a.startswith("-")),
                        None,
                    )
                    if pip_subcmd == "install":
                        virtual_env = os.environ.get("VIRTUAL_ENV", "")
                        if not virtual_env:
                            return False
                        norm_venv = normalize_path(virtual_env)
                        ws_norm = ws_root.rstrip("/")
                        if not norm_venv.startswith(ws_norm + "/") and norm_venv != ws_norm:
                            return False
                break

    # SAF-017: pip install — only allowed when VIRTUAL_ENV is active inside project folder
    if verb in ("pip", "pip3"):
        subcmd = next((a.lower() for a in args if not a.startswith("-")), None)
        if subcmd == "install":
            virtual_env = os.environ.get("VIRTUAL_ENV", "")
            if not virtual_env:
                # No venv active — deny to prevent global installations
                return False
            norm_venv = normalize_path(virtual_env)
            ws_norm = ws_root.rstrip("/")
            if not norm_venv.startswith(ws_norm + "/") and norm_venv != ws_norm:
                # Venv is outside project folder — deny (BUG-050: path-boundary safe)
                return False

    # SAF-017: for python/python3/py with -c, the argument immediately after -c
    # is inline code — not a filesystem path.  Build a skip-set of those indices
    # so step 5 does not zone-check them.
    _code_arg_indices: set[int] = set()
    if verb in ("python", "python3", "py"):
        for _ci, _ctok in enumerate(args):
            if _ctok.lower() == "-c" and _ci + 1 < len(args):
                _code_arg_indices.add(_ci + 1)

    # SAF-026: Scan inline code content for dangerous patterns
    for _ci_idx in _code_arg_indices:
        if _ci_idx < len(args):
            _code_content = args[_ci_idx].strip("\"'")
            if not _scan_python_inline_code(_code_content):
                return False

    # 5. Path argument zone checks
    # Enforce when path_args_restricted=True OR allow_arbitrary_paths=False (BUG-015).
    # Commands like npm/yarn/pnpm with allow_arbitrary_paths=False will zone-check
    # any path-like argument even though path_args_restricted is False.
    if rule.path_args_restricted or not rule.allow_arbitrary_paths:
        _prev_was_flag = False  # SAF-020: track flag-argument position
        for _idx, tok in enumerate(args):
            if _idx in _code_arg_indices or _idx in _step4_validated_indices:
                _prev_was_flag = False
                continue  # already validated or inline code — skip zone check
            stripped = tok.strip("\"'")
            # Skip pure flags; the token that follows is a flag argument, not a
            # standalone file glob — mark it so the wildcard check is skipped.
            if stripped.startswith("-"):
                _prev_was_flag = True
                continue
            # Skip environment assignment tokens
            if _ENV_ASSIGN_RE.match(stripped):
                _prev_was_flag = False
                continue
            # Dollar sign in any arg → unknown runtime value → deny
            if "$" in stripped:
                return False
            # SAF-020: Wildcard bypass — check ALL tokens, not just path-like ones.
            # Tokens like "N*" are not caught by _is_path_like (no slash, no leading dot)
            # but can still expand to deny zone directories.
            # Exception: skip tokens that are flag arguments (e.g. -name '*.py') —
            # these are filter patterns passed to the command, not shell-expanded globs.
            if not _prev_was_flag and ("*" in stripped or "?" in stripped or "[" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
                return False
            _prev_was_flag = False
            if _is_path_like(stripped):
                if not _check_path_arg(stripped, ws_root):
                    # FIX-022: For read/execute verbs, try project-folder fallback.
                    # Guards: no wildcards (already denied by _check_path_arg).
                    # For single-segment paths (e.g. "tests" from "tests/"),
                    # only fallback when the original token ends with "/" to
                    # distinguish directory refs from bare root files like
                    # ./root_config.json. Multi-segment paths (src/app.py)
                    # always get the fallback.
                    if verb.lower() in _PROJECT_FALLBACK_VERBS:
                        if "*" not in stripped and "?" not in stripped and "[" not in stripped:
                            norm_fb = posixpath.normpath(stripped.replace("\\", "/"))
                            parts_fb = [p for p in norm_fb.split("/") if p and p not in (".", "..")]
                            # FIX-033: dot-prefix single-segment names (.venv, .env,
                            # .gitignore) are always filesystem paths — include them
                            # in the project-folder fallback without requiring a
                            # trailing slash.  We test norm_fb (not raw stripped) so
                            # that "./file.txt" (stripped starts with ".", but
                            # norm_fb is "file.txt") is NOT included.
                            # _try_project_fallback already rejects deny-zone names
                            # (.github, .vscode, noagentzone).
                            # SAF-031: bare "." = project root; allowed for pip/python
                            # editable installs (pip install -e .) but denied for
                            # read/list/delete commands (ls ., cat ., rm .).
                            if norm_fb == "." and verb.lower() in ("python", "python3", "py", "pip", "pip3"):
                                _prev_was_flag = False
                                continue
                            if (
                                len(parts_fb) >= 2
                                or (
                                    len(parts_fb) == 1
                                    and (
                                        stripped.rstrip().endswith("/")
                                        or norm_fb.startswith(".")
                                    )
                                )
                            ):
                                if _try_project_fallback(norm_fb, ws_root):
                                    _prev_was_flag = False
                                    continue
                    elif verb.lower() in _DELETE_DOT_FALLBACK_VERBS:
                        # SAF-029: allow single-segment dot-prefix non-deny-zone
                        # paths (e.g. .venv, .git) via project-folder fallback.
                        # Multi-segment paths remain denied (FIX-022 intact).
                        if "*" not in stripped and "?" not in stripped and "[" not in stripped:
                            norm_fb = posixpath.normpath(stripped.replace("\\", "/"))
                            parts_fb = [p for p in norm_fb.split("/") if p and p not in (".", "..")]
                            if len(parts_fb) == 1 and norm_fb.startswith("."):
                                if _try_project_fallback(norm_fb, ws_root):
                                    _prev_was_flag = False
                                    continue
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
                        # FIX-032/033: try project-folder fallback for redirect targets.
                        # Applies the same multi-segment guard as step 5 to prevent
                        # bare single-segment names from resolving project-locally.
                        # FIX-033: dot-prefix names (.env, .gitignore) are always paths.
                        # Use norm_redir (not raw target) so that "./file" does not
                        # incorrectly match the dot-prefix condition.
                        norm_redir = posixpath.normpath(target.replace("\\", "/"))
                        parts_redir = [p for p in norm_redir.split("/") if p and p not in (".", "..")]
                        if len(parts_redir) >= 2 or (
                            len(parts_redir) == 1
                            and (
                                target.rstrip().endswith("/")
                                or norm_redir.startswith(".")
                            )
                        ):
                            if _try_project_fallback(norm_redir, ws_root):
                                continue  # allowed via project-folder fallback
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
                        # FIX-032/033: try project-folder fallback for embedded redirect targets.
                        # FIX-033: dot-prefix names (.env, .gitignore) are always paths.
                        # Use norm_emb (not raw target) so that "./file" does not
                        # incorrectly match the dot-prefix condition.
                        norm_emb = posixpath.normpath(target.replace("\\", "/"))
                        parts_emb = [p for p in norm_emb.split("/") if p and p not in (".", "..")]
                        if len(parts_emb) >= 2 or (
                            len(parts_emb) == 1
                            and (
                                target.rstrip().endswith("/")
                                or norm_emb.startswith(".")
                            )
                        ):
                            if _try_project_fallback(norm_emb, ws_root):
                                continue  # allowed via project-folder fallback
                        return False

    # Step 7 — SAF-006: Recursive enumeration ancestor check
    is_recursive = (
        verb in _INHERENTLY_RECURSIVE_COMMANDS
        or _has_recursive_flag(verb, tokens)
    )
    if is_recursive:
        # Collect path arguments
        _WIN_FLAG_RE = re.compile(r'^/[a-zA-Z0-9]{1,2}$')
        path_args = []
        for tok in args:
            stripped = tok.strip("\"'")
            if stripped.startswith("-"):
                continue
            if _WIN_FLAG_RE.match(stripped):
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

    # Step 8 — SAF-028: Bare listing CWD ancestor check
    # When a bare listing verb (dir, ls, Get-ChildItem, gci, tree, find) is
    # run with no real path argument, the implicit target is the CWD.  If the
    # CWD is an ancestor of any deny zone (e.g. the workspace root), deny it.
    if verb in _BARE_LISTING_VERBS:
        _WIN_FLAG_RE_S8 = re.compile(r'^/[a-zA-Z0-9]{1,2}$')
        path_args_s8 = []
        _prev_was_flag_s8 = False
        for tok in args:
            stripped = tok.strip("\"'")
            if not stripped.strip():  # empty or whitespace-only — not a real path
                _prev_was_flag_s8 = False
                continue
            if stripped.startswith("-"):
                _prev_was_flag_s8 = True
                continue
            if _WIN_FLAG_RE_S8.match(stripped):
                _prev_was_flag_s8 = False  # Windows short flags don't take values
                continue
            if _ENV_ASSIGN_RE.match(stripped):
                _prev_was_flag_s8 = False
                continue
            if _prev_was_flag_s8 and not _is_path_like(stripped):
                # Non-path token immediately following a flag is the flag's
                # value (e.g. -Depth 1, -Include *.py) — not a path argument.
                _prev_was_flag_s8 = False
                continue
            _prev_was_flag_s8 = False
            path_args_s8.append(stripped)

        # BUG-069: bare '.' means CWD — treat as no-path-arg for this check
        path_args_s8 = [p for p in path_args_s8 if p not in (".", "./", ".\\")]

        if not path_args_s8:
            # No explicit path arg — use CWD as implicit target
            cwd = os.getcwd()
            if _is_ancestor_of_deny_zone(cwd, ws_root):
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
        ("allow", None) — command passes all checks; auto-allowed
        ("deny", str)   — command is blocked; str is the human-readable reason
    """
    try:
        # Stage 2 — normalize whitespace
        normalized = _normalize_terminal_command(command)
        if not normalized:
            return ("deny", "Empty command after normalization.")

        # FIX-034: Early venv activation pass — runs BEFORE Stage 3 obfuscation
        # pre-scan to prevent false positives: P-22 (source) fires on
        # `source .venv/bin/activate`; P-23 (POSIX dot-source) fires on
        # `. .venv/Scripts/activate`.  Also handles the PowerShell call-operator
        # form `& .venv/Scripts/Activate.ps1` whose verb (`&`) is not in the
        # allowlist.  Validated venv segments are excluded from Stage 3 and 4.
        all_segments = _split_segments(normalized)
        if not all_segments:
            return ("deny", "No executable segments found.")

        _venv_seg_indices: set[int] = set()
        for _vi, _vseg in enumerate(all_segments):
            _vm = _VENV_ACTIVATION_SEG_RE.match(_vseg.strip())
            if _vm:
                _venv_path = _vm.group("path")
                _norm_venv = posixpath.normpath(
                    _venv_path.replace("\\", "/").lower()
                )
                if zone_classifier.classify(_norm_venv, ws_root) == "allow":
                    _venv_seg_indices.add(_vi)
                elif _try_project_fallback(_norm_venv, ws_root):
                    _venv_seg_indices.add(_vi)
                else:
                    return ("deny", f"Venv activation outside allowed zone: {_DENY_REASON}")

        # All segments are validated venv activations — allow immediately
        if len(_venv_seg_indices) == len(all_segments):
            return ("allow", None)

        # Stage 3 — obfuscation pre-scan on non-venv segments only
        lowered = " ; ".join(
            s for i, s in enumerate(all_segments) if i not in _venv_seg_indices
        ).lower()
        for pattern in _OBFUSCATION_PATTERNS:
            if pattern.search(lowered):
                return ("deny", f"Command blocked by obfuscation pre-scan: {_DENY_REASON}")

        # Stage 4 — split into segments; evaluate each non-venv segment independently
        segments = [s for i, s in enumerate(all_segments) if i not in _venv_seg_indices]
        if not segments:
            return ("allow", None)

        for segment in segments:
            tokens = _tokenize_segment(segment)
            if not tokens:
                # Could not tokenize — fail closed
                return ("deny", f"Command could not be parsed: {_DENY_REASON}")

            verb = _extract_verb(tokens)
            verb_lower = verb.lower()

            # FIX-033: PowerShell $env: variable assignment.
            # Pattern: $env:VAR_NAME = 'value'
            # Allow when value resolves inside the project folder; deny otherwise.
            # This must be checked BEFORE the generic $-verb deny guard below.
            if verb_lower.startswith("$env:") and len(tokens) >= 3 and tokens[1] == "=":
                env_value = tokens[2].strip("\"'")
                if "$" not in env_value:
                    norm_env_val = posixpath.normpath(env_value.replace("\\", "/"))
                    if zone_classifier.classify(norm_env_val, ws_root) == "allow":
                        continue  # value is explicitly inside project folder
                    if _try_project_fallback(norm_env_val, ws_root):
                        continue  # value resolves to project folder via fallback
                return ("deny", f"$env: assignment value is outside allowed zone: {_DENY_REASON}")

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

            # SAF-047: Normalize venv-path-prefixed Python/pip executables so that
            # commands like `.venv/Scripts/python -m pytest tests/` are recognized
            # as the standard "python" verb and validated against the allowlist.
            # The venv directory itself is workspace-scope checked before normalizing.
            _venv_exe_m = re.match(
                r'^(?P<pfx>(?:[^/]*/)*\.?venv/(?:scripts?|bin)/)(?P<exe>python[0-9.]*|pip[0-9.]*)(?:\.exe)?$',
                verb.replace("\\", "/"),
                re.IGNORECASE,
            )
            if _venv_exe_m:
                _venv_dir = _venv_exe_m.group("pfx").rstrip("/")
                _exe_base = _venv_exe_m.group("exe").lower()
                if re.match(r'^python3\.\d+$', _exe_base):
                    _exe_base = "python3"
                elif re.match(r'^pip3\.\d+$', _exe_base):
                    _exe_base = "pip3"
                _norm_venv = posixpath.normpath(_venv_dir.replace("\\", "/"))
                if _check_workspace_path_arg(_norm_venv, ws_root) or _try_project_fallback(_norm_venv, ws_root):
                    verb_lower = _exe_base
                else:
                    return ("deny", f"Venv executable outside allowed zone: {_DENY_REASON}")

            # FIX-022: venv activation scripts (.venv/Scripts/Activate.ps1 etc.)
            if verb_lower.endswith(("activate", "activate.bat", "activate.ps1")):
                if _check_path_arg(verb, ws_root):
                    continue  # Activation script inside allowed zone
                norm_act = posixpath.normpath(verb.replace("\\", "/"))
                if _try_project_fallback(norm_act, ws_root):
                    continue  # Activation script inside project folder
                return ("deny", f"Activation script outside project folder: {_DENY_REASON}")

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
                        # SAF-020: Wildcard bypass prevention for exception-listed commands
                        if ("*" in stripped or "?" in stripped or "[" in stripped) and _wildcard_prefix_matches_deny_zone(stripped):
                            return ("deny", f"Exception-listed command has wildcard targeting restricted zone: {_DENY_REASON}")
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

        return ("allow", None)

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


def _include_pattern_targets_deny_zone(norm_pattern: str, ws_root: str) -> bool:
    """SAF-050: Return True if *norm_pattern* explicitly targets a deny zone.

    Replaces the broad ``zone_classifier.classify()`` check that was used in
    ``_validate_include_pattern``.  ``classify()`` returns ``"deny"`` for any
    path outside the project folder, which incorrectly blocks legitimate general
    glob patterns such as ``*.py`` or workspace-root files such as
    ``pyproject.toml``.

    Rules:
    - **Relative patterns:** deny only if the **first** path component is a deny
      zone name (``.github``, ``.vscode``, ``noagentzone``).  This blocks
      workspace-root references (``.github/**``, ``.vscode/settings.json``)
      while allowing patterns that start inside an allowed folder
      (``project/.github/**``, ``src/.vscode/**``).  General globs (``*.py``,
      ``**/*.ts``) and workspace-root file names (``pyproject.toml``) have no
      deny zone as their first component, so they pass.
    - **Absolute patterns:** use ``zone_classifier.classify()`` (project-folder
      paths are allowed) then ``zone_classifier.is_workspace_root_readable()``
      (workspace-root files are allowed per SAF-046).  Anything else is denied.
    """
    if not norm_pattern:
        return False

    # Absolute path — use zone_classifier + workspace-root readable fallback
    if re.match(r"^[a-z]:", norm_pattern) or norm_pattern.startswith("/"):
        zone = zone_classifier.classify(norm_pattern, ws_root)
        if zone == "allow":
            return False
        # SAF-050: Allow workspace-root-readable paths consistent with SAF-046
        if zone_classifier.is_workspace_root_readable(norm_pattern, ws_root):
            return False
        return True

    # Relative pattern: walk left-to-right.
    # Deny only when a deny-zone component appears before the agent's project
    # folder anchor.  Only the project folder itself (e.g. "project") counts as
    # a protective anchor because it scopes the deny-zone name inside the agent's
    # own work area ("project/.github/**" → allow).
    # Any other concrete directory (e.g. "src", "tests") does NOT anchor: a deny
    # zone inside "src/" is still reachable at workspace root via symlinks or
    # misconfigurations, so we deny conservatively.
    # Wildcards (*, **, or anything starting with *) are NOT anchors because they
    # can expand to reach the workspace-root deny zone.
    # Examples:
    #   ".github/**"             → deny zone, no project anchor → DENY
    #   "**/.github/**"          → wildcard, then deny zone, no project anchor → DENY
    #   "*/.github/**"           → wildcard, then deny zone, no project anchor → DENY
    #   "src/.github/**"         → "src" is not the project folder → DENY
    #   "project/.github/**"     → "project" IS the project folder anchor → ALLOW
    #   "project/src/.vscode/**" → project anchor seen first → ALLOW
    try:
        project_dir = zone_classifier.detect_project_folder(Path(ws_root)) if ws_root else None
    except Exception:
        project_dir = None

    components = [c.lower() for c in norm_pattern.split("/")]
    has_project_anchor = False
    for component in components:
        if component in _WILDCARD_DENY_ZONES:
            if not has_project_anchor:
                return True
            # Scoped inside the project folder — deny-zone name is in the agent's
            # own work area, not the workspace-root deny zone.
            continue
        if component and not component.startswith("*"):
            if project_dir and component == project_dir:
                has_project_anchor = True
    return False


def _validate_include_pattern(pattern: str, ws_root: str) -> str:
    """Validate a grep_search ``includePattern`` glob value.

    Normalizes the pattern, checks for residual ``..`` traversal sequences,
    and uses a targeted deny-zone check (``_include_pattern_targets_deny_zone``)
    to block patterns that explicitly reference a restricted directory.

    SAF-050: The previous implementation used ``zone_classifier.classify()``
    which returns ``"deny"`` for any path outside the project folder.  This
    over-restricted legitimate general globs (``*.py``) and workspace-root file
    patterns (``pyproject.toml``) that ``read_file`` allows after SAF-046.
    The new check only denies patterns whose first path component is a deny zone
    name; VS Code ``search.exclude`` provides defence-in-depth for the rest.

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
        if _include_pattern_targets_deny_zone(expanded_norm, ws_root):
            return "deny"

    # Final check on the normalized original pattern (safety net for non-brace
    # patterns and absolute-path inputs that resolve to a deny zone).
    if _include_pattern_targets_deny_zone(normalized, ws_root):
        return "deny"

    return "allow"


def validate_grep_search(data: dict, ws_root: str) -> str:
    """SAF-003: Validate ``grep_search`` tool parameters prior to execution.

    Inspects ``includePattern`` and ``includeIgnoredFiles`` to close the
    bypass vectors identified in audit findings 2 and 3.

    Supports both the VS Code hook nested format (parameters inside
    ``tool_input``) and the flat test format (parameters at the top level).

    Returns ``"deny"`` or ``"allow"``.
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
        # FIX-021: grep_search has no filePath — VS Code search.exclude hides restricted content
        return "allow"
    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        return "allow"
    # SAF-050: Allow workspace-root-readable paths per SAF-046 (consistent with read_file)
    if zone_classifier.is_workspace_root_readable(raw_path, ws_root):
        return "allow"
    return "deny"


def validate_semantic_search(data: dict, ws_root: str) -> str:
    """SAF-003 / SAF-044: Validate ``semantic_search`` tool call.

    VS Code's search.exclude settings prevent .github/.vscode/NoAgentZone from
    being indexed, so natural language queries (including those that mention
    zone names as text) cannot surface restricted content.  SAF-044 adds
    defence-in-depth:

    - Deny path traversal sequences (``..``) embedded in the query.
    - Deny queries that are absolute paths resolving into a deny zone.
    - Allow all other queries (general natural language is safe).
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    query = tool_input.get("query")
    if not isinstance(query, str) or not query:
        query = data.get("query")

    if not isinstance(query, str):
        # No query — allow; semantic index is already scoped by search.exclude.
        return "allow"

    # Deny path traversal sequences.
    if ".." in query:
        return "deny"

    # Zone-check absolute path references embedded in the query.
    # Use a direct pattern check rather than zone_classifier.classify() so that
    # this validator works correctly in test environments where the workspace
    # root path does not exist on the real filesystem.
    norm_query = zone_classifier.normalize_path(query)
    if norm_query and (
        (len(norm_query) >= 2 and norm_query[1] == ":")  # Windows: C:/...
        or norm_query.startswith("/")                      # Unix/POSIX
    ):
        if re.search(r"/(\.github|\.vscode|noagentzone)(/|$)", "/" + norm_query):
            return "deny"

    return "allow"


# ---------------------------------------------------------------------------
# SAF-044: search_subagent — scope query to project folder
# ---------------------------------------------------------------------------

def validate_search_subagent(data: dict, ws_root: str) -> str:
    """SAF-044: Validate ``search_subagent`` tool calls.

    ``search_subagent`` accepts both natural language queries and path-like
    glob patterns, so stricter controls apply than for ``semantic_search``:

    - Deny queries containing deny-zone directory names (``.github``,
      ``.vscode``, ``NoAgentZone``), checked case-insensitively.
    - Deny queries containing path traversal sequences (``..``).
    - Deny queries whose absolute path prefix resolves into a deny zone.
    - Allow all other queries.

    Supports both the VS Code hook nested format (parameters inside
    ``tool_input``) and the flat test format (parameters at the top level).
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    query = tool_input.get("query")
    if not isinstance(query, str) or not query:
        query = data.get("query")

    if not isinstance(query, str):
        # No query — allow; VS Code search.exclude scopes results.
        return "allow"

    query_lower = query.lower()

    # Deny references to deny-zone directory names (case-insensitive).
    for zone_name in (".github", ".vscode", "noagentzone"):
        if zone_name in query_lower:
            return "deny"

    # Deny path traversal sequences.
    if ".." in query:
        return "deny"

    # Zone-check the non-wildcard path prefix for absolute path queries.
    norm_query = zone_classifier.normalize_path(query)
    if "*" in norm_query or "?" in norm_query:
        wc_pos = len(norm_query)
        for ch in ("*", "?"):
            pos = norm_query.find(ch)
            if pos != -1:
                wc_pos = min(wc_pos, pos)
        path_prefix = norm_query[:wc_pos].rstrip("/")
    else:
        path_prefix = norm_query

    if path_prefix and (
        (len(path_prefix) >= 2 and path_prefix[1] == ":")  # Windows: C:/...
        or path_prefix.startswith("/")                      # Unix/POSIX
    ):
        if re.search(r"/(\.github|\.vscode|noagentzone)(/|$)", "/" + path_prefix):
            return "deny"

    return "allow"


# ---------------------------------------------------------------------------
# SAF-043: file_search — scope validation to project folder
# ---------------------------------------------------------------------------

def validate_file_search(data: dict, ws_root: str) -> str:
    """SAF-043: Validate ``file_search`` tool calls.

    Inspects the ``query`` parameter for unsafe path scope:

    - Deny if the query contains deny-zone directory names (``.github``,
      ``.vscode``, ``NoAgentZone``), checked case-insensitively.
    - Deny if the query contains path traversal sequences (``..``).
    - Deny if the query contains a wildcard that could expand to a deny zone
      (reuses ``_wildcard_prefix_matches_deny_zone``).
    - Deny if the non-wildcard path prefix of the query is an absolute path
      that resolves outside the project folder.
    - Allow otherwise — VS Code ``search.exclude`` settings prevent deny-zone
      files from appearing in ``file_search`` results.

    Supports both the VS Code hook nested format (parameters inside
    ``tool_input``) and the flat test format (parameters at the top level).
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Prefer nested tool_input key (VS Code hook format); fall back to top-level.
    query = tool_input.get("query")
    if not isinstance(query, str) or not query:
        query = data.get("query")

    if not isinstance(query, str):
        # No query present — allow; VS Code search.exclude scopes results.
        return "allow"

    query_lower = query.lower()

    # Deny references to deny-zone directory names (case-insensitive).
    for zone_name in (".github", ".vscode", "noagentzone"):
        if zone_name in query_lower:
            return "deny"

    # Deny path traversal sequences.
    if ".." in query:
        return "deny"

    # Zone-check the non-wildcard path prefix when the query is (or starts with)
    # an absolute path.  Relative globs (e.g. **/*.py, src/**) are scoped by
    # VS Code to the workspace folder and are left to search.exclude filtering.
    norm_query = zone_classifier.normalize_path(query)

    # Extract the path prefix: everything before the first wildcard character.
    if "*" in norm_query or "?" in norm_query:
        wc_pos = len(norm_query)
        for ch in ("*", "?"):
            pos = norm_query.find(ch)
            if pos != -1:
                wc_pos = min(wc_pos, pos)
        path_prefix = norm_query[:wc_pos].rstrip("/")
    else:
        path_prefix = norm_query

    # Only zone-check if the prefix is an absolute path (drive letter or leading /).
    if path_prefix and (
        (len(path_prefix) >= 2 and path_prefix[1] == ":")  # Windows: C:/...
        or path_prefix.startswith("/")                      # Unix/POSIX
    ):
        if zone_classifier.classify(path_prefix, ws_root) == "deny":
            return "deny"

    # Allow — VS Code search.exclude settings prevent deny-zone files from appearing.
    return "allow"


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
        # SAF-032: Block access to .git internals even within the project folder.
        # Covers create_file, replace_string_in_file, edit_file, write_file, etc.
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# SAF-018: multi_replace_string_in_file — validate ALL replacement filePaths
# ---------------------------------------------------------------------------

def validate_multi_replace_tool(data: dict, ws_root: str) -> str:
    """SAF-018: Validate multi_replace_string_in_file tool calls.

    The tool receives a ``replacements`` array where every entry contains a
    ``filePath``.  ALL filePaths must be inside Project/ (zone == "allow").
    If ANY filePath is outside, the entire operation is denied.

    Fallback: when the payload uses the legacy flat ``filePath`` field instead
    of the ``replacements`` array (e.g. in older tests or hand-crafted calls),
    delegates to ``validate_write_tool`` for a single-path zone check.  This
    preserves backward compatibility while keeping the deny-by-default posture.

    Fails closed ("deny") when replacements is absent, not a list, or empty,
    AND no flat filePath fallback is present.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    replacements = tool_input.get("replacements")
    if replacements is None:
        # Fall back to top-level key for test convenience
        replacements = data.get("replacements")

    if replacements is None:
        # No replacements array present — try legacy flat filePath fallback.
        # validate_write_tool will fail closed if filePath is also absent.
        return validate_write_tool(data, ws_root)

    if not isinstance(replacements, list) or not replacements:
        # Replacements key exists but is wrong type or empty — fail closed
        return "deny"

    for entry in replacements:
        if not isinstance(entry, dict):
            return "deny"
        file_path = entry.get("filePath")
        if not isinstance(file_path, str) or not file_path:
            return "deny"
        zone = zone_classifier.classify(file_path, ws_root)
        if zone != "allow":
            return "deny"
        # SAF-032: Block access to .git internals even within the project folder.
        if zone_classifier.is_git_internals(file_path):
            return "deny"

    return "allow"


# ---------------------------------------------------------------------------
# SAF-023: get_errors — filePaths array zone validation
# ---------------------------------------------------------------------------

def validate_get_errors(data: dict, ws_root: str) -> str:
    """SAF-023: Validate get_errors tool calls.

    When filePaths is absent or empty -> allow (VS Code scopes automatically).
    When filePaths is present -> zone-check every path; deny if ANY is in a
    restricted zone.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Prefer nested tool_input key (VS Code hook format); fall back to
    # top-level dict key (test / flat format).
    file_paths = tool_input.get("filePaths")
    if file_paths is None:
        file_paths = data.get("filePaths")

    # No filePaths provided or empty array -> allow
    if not file_paths:
        return "allow"

    if not isinstance(file_paths, list):
        # Unexpected type for filePaths -> fail closed
        return "deny"

    for path in file_paths:
        if not isinstance(path, str) or not path:
            return "deny"
        zone = zone_classifier.classify(path, ws_root)
        if zone == "deny":
            # FIX-026: Try project-folder fallback for relative paths
            norm_p = posixpath.normpath(path.replace("\\", "/"))
            if not _try_project_fallback(norm_p, ws_root):
                return "deny"

    return "allow"


# ---------------------------------------------------------------------------
# SAF-038: memory tool — path must be inside the project folder
# ---------------------------------------------------------------------------

def validate_memory(data: dict, ws_root: str) -> str:
    """SAF-038/SAF-048: Validate memory tool calls.

    Extracts the target file path from the payload (``filePath`` in
    ``tool_input``, then ``filePath`` or ``path`` at the top level).

    SAF-048: Virtual VS Code memory paths (``/memories/`` prefix) are not
    filesystem paths and cannot resolve to denied zones.  They are handled
    before zone classification:
    - Reads on any ``/memories/`` path → allow.
    - Writes are permitted only when the path is under ``/memories/session/``.
      Write operations are detected via the ``command`` field in ``tool_input``
      (any value containing "save", "write", "create", "update", or "delete").

    Non-virtual paths continue through normal zone classification.
    Fails closed — returns "deny" when no path is present.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Prefer nested tool_input key (VS Code hook format)
    raw_path = tool_input.get("filePath")
    if not isinstance(raw_path, str) or not raw_path:
        raw_path = data.get("filePath")
    if not isinstance(raw_path, str) or not raw_path:
        raw_path = data.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        # No path found — fail closed
        return "deny"

    # SAF-048: Virtual VS Code memory paths are not filesystem paths and cannot
    # escape to denied zones — handle them before calling zone_classifier.
    norm_virtual = raw_path.replace("\\", "/")

    # BUG-123: Reject null bytes and Unicode control/format characters before
    # any further processing — they are never legitimate in memory paths.
    _FORBIDDEN_CATS = {"Cc", "Cf"}
    if "\x00" in norm_virtual or any(
        unicodedata.category(ch) in _FORBIDDEN_CATS for ch in norm_virtual
    ):
        return "deny"

    # BUG-121 / BUG-122: Resolve dot-dot segments so traversal paths like
    # /memories/../../.github and /memories/session/../preferences.md can no
    # longer bypass the virtual-path check or the write-protection boundary.
    norm_virtual = posixpath.normpath(norm_virtual)

    # BUG-124: Case-normalize so /MEMORIES/session/ is treated identically to
    # /memories/session/.
    norm_virtual = norm_virtual.lower()

    if norm_virtual == "/memories" or norm_virtual.startswith("/memories/"):
        command = str(tool_input.get("command") or "").lower()
        _WRITE_OPS = ("save", "write", "create", "update", "delete")
        is_write = any(op in command for op in _WRITE_OPS)
        if is_write and not norm_virtual.startswith("/memories/session/"):
            # Writes outside /memories/session/ are not permitted
            return "deny"
        return "allow"

    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# SAF-038: create_directory tool — dirPath must be inside the project folder
# ---------------------------------------------------------------------------

def validate_create_directory(data: dict, ws_root: str) -> str:
    """SAF-038: Validate create_directory tool calls.

    Extracts ``dirPath`` from the payload (``tool_input`` first, then
    top-level data).  Allows the call only when the path resolves inside
    the project folder.  Fails closed — returns "deny" when dirPath is absent.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Prefer nested tool_input key (VS Code hook format)
    raw_path = tool_input.get("dirPath")
    if not isinstance(raw_path, str) or not raw_path:
        raw_path = data.get("dirPath")
    if not isinstance(raw_path, str) or not raw_path:
        # No dirPath found — fail closed
        return "deny"

    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# SAF-039: vscode_listCodeUsages / vscode_renameSymbol — path extraction helper
# ---------------------------------------------------------------------------

def _extract_lsp_file_path(data: dict) -> Optional[str]:
    """Extract the target file path from a VS Code LSP tool payload.

    Tries ``filePath`` first (workspace-relative), then ``uri`` (with
    ``file://`` scheme stripped).  Looks in ``tool_input`` before falling
    back to the top-level data dict.  Returns None when no path is present.
    """
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # 1. Try filePath in tool_input, then top-level
    raw = tool_input.get("filePath")
    if not isinstance(raw, str) or not raw:
        raw = data.get("filePath")
    if isinstance(raw, str) and raw:
        return raw

    # 2. Try uri — strip file:// scheme if present
    uri = tool_input.get("uri")
    if not isinstance(uri, str) or not uri:
        uri = data.get("uri")
    if isinstance(uri, str) and uri:
        # Handle file:///C:/path (Windows) and file:///path (Unix)
        if uri.lower().startswith("file:///"):
            path = unquote(uri[8:])  # strip "file:///" and decode percent-encoding
            # Windows drive letter: C:/path
            if len(path) >= 2 and path[1] == ":":
                return path
            # Unix absolute path: /path
            return "/" + path
        elif uri.lower().startswith("file://"):
            # file://hostname/path — strip scheme and hostname
            remainder = uri[7:]
            slash = remainder.find("/")
            if slash != -1:
                return unquote(remainder[slash:])  # decode percent-encoding
        # Non-file URI scheme — not a file-system path; fail closed
        return None

    return None


# ---------------------------------------------------------------------------
# SAF-039: vscode_listCodeUsages — zone-restricted to project folder
# ---------------------------------------------------------------------------

def validate_vscode_list_code_usages(data: dict, ws_root: str) -> str:
    """SAF-039: Validate vscode_listCodeUsages tool calls.

    Extracts the target file path from ``filePath`` or ``uri`` in the
    payload.  Allows the call only when the path resolves inside the project
    folder.  Fails closed — returns "deny" when no path is present.
    """
    raw_path = _extract_lsp_file_path(data)
    if not isinstance(raw_path, str) or not raw_path:
        # No path found — fail closed
        return "deny"

    # Null bytes have no legitimate use in file paths — deny immediately
    if "\x00" in raw_path:
        return "deny"

    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        # Block .git internals even when inside project folder
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# SAF-039: vscode_renameSymbol — write-like; zone-restricted + .git/ blocked
# ---------------------------------------------------------------------------

def validate_vscode_rename_symbol(data: dict, ws_root: str) -> str:
    """SAF-039: Validate vscode_renameSymbol tool calls.

    vscode_renameSymbol modifies source files in-place, so it is treated as
    a write-like operation.  Extracts the target file path from ``filePath``
    or ``uri`` in the payload.  Allows the call only when the path resolves
    inside the project folder.  Explicitly blocks ``.git/`` internals.
    Fails closed — returns "deny" when no path is present.
    """
    raw_path = _extract_lsp_file_path(data)
    if not isinstance(raw_path, str) or not raw_path:
        # No path found — fail closed
        return "deny"

    # Null bytes have no legitimate use in file paths — deny immediately
    if "\x00" in raw_path:
        return "deny"

    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        # Write-like: always block .git internals (SAF-032 extension)
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
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

# SAF-028: All bare listing verbs subject to CWD ancestor check (Step 8)
_BARE_LISTING_VERBS: frozenset = frozenset({"dir", "ls", "get-childitem", "gci", "tree", "find"})


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
    # SAF-044: search_subagent — scope query to project folder.
    if tool_name == "search_subagent":
        return validate_search_subagent(data, ws_root)

    # SAF-023: get_errors carries an optional filePaths array; each path must
    # be zone-checked.  Handled before the _EXEMPT_TOOLS fallback so the array
    # field is inspected rather than a single filePath.
    if tool_name == "get_errors":
        return validate_get_errors(data, ws_root)

    # SAF-038: memory tool — filePath must be inside the project folder.
    # Handled before the _EXEMPT_TOOLS fallback to ensure explicit path extraction.
    if tool_name == "memory":
        return validate_memory(data, ws_root)

    # SAF-038: create_directory tool — dirPath must be inside the project folder.
    # Handled before the _EXEMPT_TOOLS fallback because dirPath is not in
    # _PATH_FIELDS and would not be found by the generic extract_path() helper.
    if tool_name == "create_directory":
        return validate_create_directory(data, ws_root)

    # SAF-039: vscode_listCodeUsages — filePath/uri must be inside project folder.
    if tool_name == "vscode_listCodeUsages":
        return validate_vscode_list_code_usages(data, ws_root)

    # SAF-039: vscode_renameSymbol — write-like; filePath/uri must be inside project folder.
    if tool_name == "vscode_renameSymbol":
        return validate_vscode_rename_symbol(data, ws_root)

    # SAF-043: file_search — scope query to project folder.
    if tool_name == "file_search":
        return validate_file_search(data, ws_root)

    # FIX-035: Deferred development tools — safe to allow unconditionally.
    # These VS Code/Copilot tools carry no file-system path argument and do not
    # execute arbitrary commands; they are needed for standard dev workflows.
    if tool_name in ("install_python_packages", "configure_python_environment", "fetch_webpage"):
        return "allow"

    # SAF-007: Write tools are restricted to Project/ only.  Any write
    # targeting a path outside Project/ is denied, even if zone would be "ask".
    # SAF-018: multi_replace_string_in_file carries an array of replacements —
    # each entry has its own filePath; all must be inside Project/.
    if tool_name == "multi_replace_string_in_file":
        return validate_multi_replace_tool(data, ws_root)
    if tool_name in _WRITE_TOOLS:
        return validate_write_tool(data, ws_root)

    # Non-exempt tools (non-empty name not in exempt set): deny.
    # In the 2-tier model, agents must only use approved tools.
    if tool_name and tool_name not in _EXEMPT_TOOLS:
        return "deny"

    # Exempt tool or unknown tool name: resolve path and check zone.
    raw_path = extract_path(data)
    if raw_path is None:
        # No path — cannot verify zone; fail closed.
        return "deny"

    # SAF-002: zone_classifier.classify() handles normalization and
    # relative-path resolution internally.
    zone = zone_classifier.classify(raw_path, ws_root)
    if zone == "allow":
        # SAF-032: Block file tools from accessing .git internals even when the
        # path is inside the project folder (allow zone).  Covers read_file,
        # list_dir, edit_notebook_file, and any other exempt tool.
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    # SAF-046: Allow read-only access to the workspace root itself and its
    # direct non-denied children (e.g. pyproject.toml, README.md) per
    # AGENT-RULES §1 and §3.  Write tools use validate_write_tool() which
    # only allows the project folder, so workspace root remains write-denied.
    if zone_classifier.is_workspace_root_readable(raw_path, ws_root):
        if zone_classifier.is_git_internals(raw_path):
            return "deny"
        return "allow"
    return "deny"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        # SAF-008: Integrity check -- deny all tool calls if files are tampered
        if not verify_file_integrity():
            print(build_response("deny", _INTEGRITY_WARNING), flush=True)
            print(_INTEGRITY_WARNING, file=sys.stderr)
            sys.exit(0)

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

        # SAF-035: Session denial counter — check lock status before deciding
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        # SAF-036: Load counter configuration
        counter_cfg = _load_counter_config(scripts_dir)
        counter_enabled = counter_cfg["counter_enabled"]
        threshold = counter_cfg["lockout_threshold"]

        if counter_enabled:
            state_path = os.path.join(scripts_dir, _STATE_FILE_NAME)
            state = _load_state(state_path)
            session_id, state = _get_session_id(scripts_dir, state)
            session_data = state.get(session_id, {})
            if isinstance(session_data, dict) and session_data.get("locked", False):
                _lockout_msg = (
                    f"Session locked — {threshold} denied actions reached. "
                    "Start a new chat session to continue working."
                )
                print(build_response("deny", _lockout_msg), flush=True)
                sys.exit(0)

        decision = decide(data, ws_root)

        if decision == "allow":
            print(build_response("allow"), flush=True)
        else:
            if counter_enabled:
                # SAF-035: Increment deny counter and build progressive deny message
                deny_count, now_locked = _increment_deny_counter(
                    state, session_id, threshold
                )
                _save_state(state_path, state)
                if now_locked:
                    deny_reason = (
                        f"Session locked — {threshold} denied actions reached. "
                        "Start a new chat session to continue working."
                    )
                else:
                    deny_reason = f"Block {deny_count} of {threshold}. {_DENY_REASON}"
            else:
                deny_reason = _DENY_REASON
            print(build_response("deny", deny_reason), flush=True)

    except Exception:
        print(build_response("deny", _DENY_REASON), flush=True)

    sys.exit(0)


if __name__ == "__main__":
    main()
