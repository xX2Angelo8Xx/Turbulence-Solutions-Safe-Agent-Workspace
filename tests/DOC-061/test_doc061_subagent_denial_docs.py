"""
Tests for DOC-061: Document subagent denial budget sharing.

Verifies that both AGENT-RULES.md copies contain the required
subagent denial budget sharing warning in the §6 denial counter section,
and that both copies are in sync.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"
MIRROR_RULES = REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- Section presence ---

def test_primary_has_denial_counter_section():
    content = _load(PRIMARY_RULES)
    assert "## 6. Session-Scoped Denial Counter" in content


def test_mirror_has_denial_counter_section():
    content = _load(MIRROR_RULES)
    assert "## 6. Session-Scoped Denial Counter" in content


# --- Subagent warning heading ---

def test_primary_has_subagent_budget_sharing_heading():
    content = _load(PRIMARY_RULES)
    assert "### Subagent Budget Sharing" in content


def test_mirror_has_subagent_budget_sharing_heading():
    content = _load(MIRROR_RULES)
    assert "### Subagent Budget Sharing" in content


# --- Key concepts documented ---

def test_primary_warning_mentions_parent_session_budget():
    content = _load(PRIMARY_RULES)
    assert "parent session" in content.lower() or "parent session's" in content


def test_mirror_warning_mentions_parent_session_budget():
    content = _load(MIRROR_RULES)
    assert "parent session" in content.lower() or "parent session's" in content


def test_primary_warning_instructs_not_to_probe_denied_zones():
    content = _load(PRIMARY_RULES)
    # Must mention that subagents should not probe denied zones
    assert "denied zones" in content or "denied zone" in content


def test_mirror_warning_instructs_not_to_probe_denied_zones():
    content = _load(MIRROR_RULES)
    assert "denied zones" in content or "denied zone" in content


def test_primary_warning_mentions_subagent():
    content = _load(PRIMARY_RULES)
    assert "subagent" in content.lower()


def test_mirror_warning_mentions_subagent():
    content = _load(MIRROR_RULES)
    assert "subagent" in content.lower()


# --- Warning callout present ---

def test_primary_has_warning_callout():
    content = _load(PRIMARY_RULES)
    assert "> **Warning:**" in content


def test_mirror_has_warning_callout():
    content = _load(MIRROR_RULES)
    assert "> **Warning:**" in content


# --- Rules for agents that spawn subagents ---

def test_primary_has_explicit_instruction_rules():
    content = _load(PRIMARY_RULES)
    assert "Explicitly instruct subagents not to probe denied zones" in content


def test_mirror_has_explicit_instruction_rules():
    content = _load(MIRROR_RULES)
    assert "Explicitly instruct subagents not to probe denied zones" in content


def test_primary_mentions_coordinator_orchestrator_risk():
    content = _load(PRIMARY_RULES)
    assert "Coordinator" in content or "Orchestrator" in content


def test_mirror_mentions_coordinator_orchestrator_risk():
    content = _load(MIRROR_RULES)
    assert "Coordinator" in content or "Orchestrator" in content


# --- Sync check ---

def _extract_section_6(content: str) -> str:
    """Extract §6 content from the first ## 6. heading up to the next ## heading."""
    match = re.search(r"(## 6\. Session-Scoped Denial Counter.*?)(?=\n## \d+\.|\Z)", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def test_both_copies_section_6_are_identical():
    primary_content = _load(PRIMARY_RULES)
    mirror_content = _load(MIRROR_RULES)
    primary_s6 = _extract_section_6(primary_content)
    mirror_s6 = _extract_section_6(mirror_content)
    assert primary_s6 != "", "Primary §6 section not found"
    assert mirror_s6 != "", "Mirror §6 section not found"
    assert primary_s6 == mirror_s6, (
        "§6 sections are out of sync between primary and mirror AGENT-RULES.md.\n"
        f"PRIMARY:\n{primary_s6}\n\nMIRROR:\n{mirror_s6}"
    )


# --- Tester edge-case tests ---


def test_primary_warning_mentions_bypass():
    """Rule 2 must state that subagents cannot be used as a bypass."""
    content = _load(PRIMARY_RULES)
    assert "bypass" in content.lower()


def test_mirror_warning_mentions_bypass():
    content = _load(MIRROR_RULES)
    assert "bypass" in content.lower()


def test_primary_warning_mentions_specific_zones():
    """The warning must name specific denied zones so agents know what to tell subagents."""
    content = _load(PRIMARY_RULES)
    assert ".github/hooks/" in content or "NoAgentZone" in content


def test_mirror_warning_mentions_specific_zones():
    content = _load(MIRROR_RULES)
    assert ".github/hooks/" in content or "NoAgentZone" in content


def test_primary_warning_mentions_runsubagent():
    """Warning must reference the runSubagent tool so agents know which invocation path is affected."""
    content = _load(PRIMARY_RULES)
    assert "runSubagent" in content


def test_mirror_warning_mentions_runsubagent():
    content = _load(MIRROR_RULES)
    assert "runSubagent" in content


def test_subagent_warning_is_inside_section_6(tmp_path):
    """The Subagent Budget Sharing heading must appear inside §6 (before §7 starts)."""
    for path in (PRIMARY_RULES, MIRROR_RULES):
        content = _load(path)
        s6_start = content.find("## 6. Session-Scoped Denial Counter")
        s7_start = content.find("## 7.")
        subagent_pos = content.find("### Subagent Budget Sharing")
        assert s6_start != -1, f"§6 not found in {path.name}"
        assert subagent_pos != -1, f"Subagent Budget Sharing not found in {path.name}"
        if s7_start != -1:
            assert s6_start < subagent_pos < s7_start, (
                f"Subagent Budget Sharing heading is not inside §6 in {path.name}"
            )
        else:
            assert s6_start < subagent_pos, (
                f"Subagent Budget Sharing heading appears before §6 in {path.name}"
            )
