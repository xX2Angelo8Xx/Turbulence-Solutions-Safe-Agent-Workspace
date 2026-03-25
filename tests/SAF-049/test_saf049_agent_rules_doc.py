"""
SAF-049: Tests verifying that AGENT-RULES.md accurately documents
zone restrictions for grep_search and file_search tools.

BUG-114: The old docs said "no zone restriction" for both tools,
which contradicted the actual enforcement behavior.
"""

import pathlib

AGENT_RULES_PATH = pathlib.Path(__file__).parents[2] / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"


def _load_agent_rules() -> str:
    return AGENT_RULES_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Old misleading text must be gone
# ---------------------------------------------------------------------------

def test_grep_search_no_longer_says_no_zone_restriction():
    """grep_search must not claim 'no zone restriction' (BUG-114 regression)."""
    content = _load_agent_rules()
    # Find the grep_search table row and check it no longer contains the old label
    lines = content.splitlines()
    grep_lines = [ln for ln in lines if "grep_search" in ln and "|" in ln]
    assert grep_lines, "grep_search row not found in Tool Permission Matrix"
    for line in grep_lines:
        assert "no zone restriction" not in line.lower(), (
            f"grep_search row still contains 'no zone restriction': {line}"
        )


def test_file_search_no_longer_says_no_zone_restriction():
    """file_search must not claim 'no zone restriction' (BUG-114 regression)."""
    content = _load_agent_rules()
    lines = content.splitlines()
    file_search_lines = [ln for ln in lines if "file_search" in ln and "|" in ln]
    assert file_search_lines, "file_search row not found in Tool Permission Matrix"
    for line in file_search_lines:
        assert "no zone restriction" not in line.lower(), (
            f"file_search row still contains 'no zone restriction': {line}"
        )


# ---------------------------------------------------------------------------
# 2. includePattern restriction must be documented
# ---------------------------------------------------------------------------

def test_grep_search_documents_include_pattern_restriction():
    """grep_search row must mention that includePattern targeting denied zones is blocked."""
    content = _load_agent_rules()
    lines = content.splitlines()
    grep_lines = [ln for ln in lines if "grep_search" in ln and "|" in ln]
    assert grep_lines, "grep_search row not found"
    combined = " ".join(grep_lines)
    assert "includePattern" in combined, (
        "grep_search row must document the includePattern zone restriction"
    )
    assert "blocked" in combined.lower(), (
        "grep_search row must state that restricted usage is blocked"
    )


def test_file_search_documents_include_pattern_restriction():
    """file_search row must mention that targeting denied zones is blocked."""
    content = _load_agent_rules()
    lines = content.splitlines()
    file_search_lines = [ln for ln in lines if "file_search" in ln and "|" in ln]
    assert file_search_lines, "file_search row not found"
    combined = " ".join(file_search_lines)
    assert "blocked" in combined.lower(), (
        "file_search row must state that restricted usage is blocked"
    )
    # Must mention denied zones (NoAgentZone or 'denied zone')
    assert "NoAgentZone" in combined or "denied zone" in combined.lower(), (
        "file_search row must reference denied zone restriction"
    )


# ---------------------------------------------------------------------------
# 3. includeIgnoredFiles restriction must be documented
# ---------------------------------------------------------------------------

def test_grep_search_documents_include_ignored_files_restriction():
    """grep_search row must mention that includeIgnoredFiles: true is blocked."""
    content = _load_agent_rules()
    lines = content.splitlines()
    grep_lines = [ln for ln in lines if "grep_search" in ln and "|" in ln]
    assert grep_lines, "grep_search row not found"
    combined = " ".join(grep_lines)
    assert "includeIgnoredFiles" in combined, (
        "grep_search row must document that includeIgnoredFiles: true is blocked"
    )


def test_file_search_documents_include_ignored_files_restriction():
    """file_search row must mention that includeIgnoredFiles: true is blocked."""
    content = _load_agent_rules()
    lines = content.splitlines()
    file_search_lines = [ln for ln in lines if "file_search" in ln and "|" in ln]
    assert file_search_lines, "file_search row not found"
    combined = " ".join(file_search_lines)
    assert "includeIgnoredFiles" in combined, (
        "file_search row must document that includeIgnoredFiles: true is blocked"
    )


# ---------------------------------------------------------------------------
# 4. General (non-denied-zone) search must still be documented as allowed
# ---------------------------------------------------------------------------

def test_grep_search_still_allowed_for_general_use():
    """grep_search row must indicate that general use is still allowed."""
    content = _load_agent_rules()
    lines = content.splitlines()
    grep_lines = [ln for ln in lines if "grep_search" in ln and "|" in ln]
    assert grep_lines, "grep_search row not found"
    combined = " ".join(grep_lines)
    assert "allowed" in combined.lower(), (
        "grep_search row must indicate that general pattern search is allowed"
    )


def test_file_search_still_allowed_for_general_use():
    """file_search row must indicate that general use is still allowed."""
    content = _load_agent_rules()
    lines = content.splitlines()
    file_search_lines = [ln for ln in lines if "file_search" in ln and "|" in ln]
    assert file_search_lines, "file_search row not found"
    combined = " ".join(file_search_lines)
    assert "allowed" in combined.lower(), (
        "file_search row must indicate that general search is still allowed"
    )


# ---------------------------------------------------------------------------
# 5. semantic_search must remain unchanged (no zone restriction is correct)
# ---------------------------------------------------------------------------

def test_semantic_search_unchanged():
    """semantic_search should still say 'no zone restriction' — it was never restricted."""
    content = _load_agent_rules()
    lines = content.splitlines()
    semantic_lines = [ln for ln in lines if "semantic_search" in ln and "|" in ln]
    assert semantic_lines, "semantic_search row not found in Tool Permission Matrix"
    combined = " ".join(semantic_lines)
    assert "no zone restriction" in combined.lower(), (
        "semantic_search row must still document 'no zone restriction' (it was not changed)"
    )


# ---------------------------------------------------------------------------
# 6. Permission column updated for grep_search and file_search
# ---------------------------------------------------------------------------

def test_grep_search_permission_is_zone_checked():
    """grep_search permission column should be 'Zone-checked', not 'Allowed'."""
    content = _load_agent_rules()
    lines = content.splitlines()
    grep_lines = [ln for ln in lines if "grep_search" in ln and "|" in ln]
    assert grep_lines, "grep_search row not found"
    combined = " ".join(grep_lines)
    assert "zone-checked" in combined.lower(), (
        "grep_search permission should be 'Zone-checked' to reflect actual enforcement"
    )


def test_file_search_permission_is_zone_checked():
    """file_search permission column should be 'Zone-checked', not 'Allowed'."""
    content = _load_agent_rules()
    lines = content.splitlines()
    file_search_lines = [ln for ln in lines if "file_search" in ln and "|" in ln]
    assert file_search_lines, "file_search row not found"
    combined = " ".join(file_search_lines)
    assert "zone-checked" in combined.lower(), (
        "file_search permission should be 'Zone-checked' to reflect actual enforcement"
    )
