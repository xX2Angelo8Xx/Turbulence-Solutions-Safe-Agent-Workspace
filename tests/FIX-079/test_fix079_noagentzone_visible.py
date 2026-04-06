"""tests/FIX-079/test_fix079_noagentzone_visible.py

Tests for FIX-079: Show NoAgentZone in VS Code file explorer.

Verifies that:
- settings.json is valid JSON
- **/NoAgentZone is removed from files.exclude (folder visible in explorer)
- **/NoAgentZone is still present in search.exclude (agent search still blocked)
- .github and .vscode remain in files.exclude (unchanged sentinel)
- Security gate integrity hashes match the actual files on disk
- zone_classifier still denies agent access to NoAgentZone paths
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SETTINGS = REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"
GATE = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
SCRIPTS_DIR = GATE.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_settings() -> dict:
    return json.loads(SETTINGS.read_bytes())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _compute_canonical_gate_hash(content_bytes: bytes) -> str:
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content_bytes,
    )
    return hashlib.sha256(canonical).hexdigest()


def _extract_hash(constant_name: str) -> str:
    content = GATE.read_text(encoding="utf-8")
    pattern = rf'{re.escape(constant_name)}: str = "([0-9a-fA-F]{{64}})"'
    m = re.search(pattern, content)
    assert m is not None, f"{constant_name} not found in {GATE}"
    return m.group(1)


# ---------------------------------------------------------------------------
# Tests — settings.json validity
# ---------------------------------------------------------------------------


def test_settings_json_is_valid_json():
    """settings.json must be parseable as valid JSON."""
    raw = SETTINGS.read_bytes()
    parsed = json.loads(raw)
    assert isinstance(parsed, dict), "settings.json root must be a JSON object"


# ---------------------------------------------------------------------------
# Tests — files.exclude
# ---------------------------------------------------------------------------


def test_noagentzone_not_in_files_exclude():
    """**/NoAgentZone must NOT appear in files.exclude — its presence hides the folder
    from human users in the VS Code file explorer."""
    settings = _read_settings()
    files_exclude = settings.get("files.exclude", {})
    assert "**/NoAgentZone" not in files_exclude, (
        "**/NoAgentZone found in files.exclude — folder is hidden from VS Code explorer"
    )


def test_github_still_in_files_exclude():
    """.github must remain in files.exclude (this fix must not disturb it)."""
    settings = _read_settings()
    assert settings.get("files.exclude", {}).get(".github") is True, (
        ".github missing from files.exclude — unintended side-effect of FIX-079"
    )


def test_vscode_still_in_files_exclude():
    """.vscode must remain in files.exclude (this fix must not disturb it)."""
    settings = _read_settings()
    assert settings.get("files.exclude", {}).get(".vscode") is True, (
        ".vscode missing from files.exclude — unintended side-effect of FIX-079"
    )


# ---------------------------------------------------------------------------
# Tests — search.exclude
# ---------------------------------------------------------------------------


def test_noagentzone_in_search_exclude():
    """**/NoAgentZone must still be in search.exclude with value true.
    Removing it would let VS Code search (and agent grep_search) index the folder."""
    settings = _read_settings()
    search_exclude = settings.get("search.exclude", {})
    assert "**/NoAgentZone" in search_exclude, (
        "**/NoAgentZone missing from search.exclude — agents could index content via VS Code search"
    )
    assert search_exclude["**/NoAgentZone"] is True


# ---------------------------------------------------------------------------
# Tests — integrity hashes
# ---------------------------------------------------------------------------


def test_security_gate_settings_hash_absent():
    """_KNOWN_GOOD_SETTINGS_HASH constant must NOT be declared in security_gate.py (removed by FIX-115)."""
    content = GATE.read_text(encoding="utf-8")
    assert "_KNOWN_GOOD_SETTINGS_HASH: str =" not in content, (
        "_KNOWN_GOOD_SETTINGS_HASH constant still declared in security_gate.py — it should have been removed by FIX-115"
    )


def test_security_gate_gate_hash_valid():
    """_KNOWN_GOOD_GATE_HASH in security_gate.py must match the canonical hash of the file."""
    embedded = _extract_hash("_KNOWN_GOOD_GATE_HASH")
    content = GATE.read_bytes()
    actual = _compute_canonical_gate_hash(content)
    assert embedded == actual, (
        f"_KNOWN_GOOD_GATE_HASH mismatch — run update_hashes.py\n"
        f"  embedded: {embedded}\n"
        f"  actual:   {actual}"
    )


# ---------------------------------------------------------------------------
# Tests — security gate zone enforcement (unchanged)
# ---------------------------------------------------------------------------


def test_noagentzone_zone_deny_direct_path():
    """zone_classifier must deny a direct path into NoAgentZone."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import zone_classifier  # noqa: PLC0415

    ws_root = "/workspace/myproject"
    result = zone_classifier.classify(f"{ws_root}/NoAgentZone/secret.txt", ws_root)
    assert result == "deny", (
        f"zone_classifier allowed access to NoAgentZone path — expected 'deny', got {result!r}"
    )


def test_noagentzone_zone_deny_nested_path():
    """zone_classifier must deny a deeply nested path inside NoAgentZone."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    import zone_classifier  # noqa: PLC0415

    ws_root = "/workspace/myproject"
    result = zone_classifier.classify(
        f"{ws_root}/NoAgentZone/subdir/confidential/data.json", ws_root
    )
    assert result == "deny", (
        f"zone_classifier allowed nested NoAgentZone access — expected 'deny', got {result!r}"
    )
