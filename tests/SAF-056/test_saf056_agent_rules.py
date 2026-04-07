"""
SAF-056 — Tests for AGENT-RULES.md and copilot-instructions.md correctness.

Verifies:
- AGENT-RULES.md documents system Python as acceptable fallback when no .venv exists
- AGENT-RULES.md still shows .venv as preferred
- copilot-instructions.md references AGENT-RULES.md as the comprehensive reference
- copilot-instructions.md is reasonably short (not a duplicate rule book)
- Both files exist and are non-empty
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AGENT_RULES = (
    REPO_ROOT / "templates" / "agent-workbench" / "Project" / "AgentDocs" / "AGENT-RULES.md"
)
COPILOT_INSTRUCTIONS = (
    REPO_ROOT
    / "templates"
    / "agent-workbench"
    / ".github"
    / "instructions"
    / "copilot-instructions.md"
)


# ---------------------------------------------------------------------------
# AGENT-RULES.md tests
# ---------------------------------------------------------------------------


def test_agent_rules_exists():
    assert AGENT_RULES.exists(), "AGENT-RULES.md must exist in the template"
    assert AGENT_RULES.stat().st_size > 0, "AGENT-RULES.md must not be empty"


def test_agent_rules_system_python_acceptable():
    """AGENT-RULES.md must document that system Python is acceptable when no .venv."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    # Check for language that makes system Python acceptable
    acceptable = (
        "system Python" in content
        or "no .venv" in content
        or "no `.venv`" in content
        or "when no .venv" in content
        or "when no `.venv`" in content
        or "acceptable when" in content
    )
    assert acceptable, (
        "AGENT-RULES.md §4 must contain language about system Python being acceptable "
        "when no .venv exists (e.g. 'system Python', 'no .venv', 'acceptable when')"
    )


def test_agent_rules_venv_preferred():
    """.venv\\Scripts\\python must still be documented as the preferred command."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert r".venv\Scripts\python" in content, (
        "AGENT-RULES.md must still document .venv\\Scripts\\python as the preferred command"
    )


def test_agent_rules_section4_has_python_examples():
    """Section 4 (Terminal Rules) must contain Python command examples."""
    content = AGENT_RULES.read_text(encoding="utf-8")
    assert "## 4." in content or "## 4 " in content or "## 4\n" in content or "## 4." in content
    # The Python block should be present
    assert "python" in content.lower(), "Section 4 must contain Python command examples"


# ---------------------------------------------------------------------------
# copilot-instructions.md tests
# ---------------------------------------------------------------------------


def test_copilot_instructions_exists():
    assert COPILOT_INSTRUCTIONS.exists(), "copilot-instructions.md must exist in template"
    assert COPILOT_INSTRUCTIONS.stat().st_size > 0, "copilot-instructions.md must not be empty"


def test_copilot_instructions_references_agent_rules():
    """copilot-instructions.md must reference AGENT-RULES.md."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "AGENT-RULES.md" in content, (
        "copilot-instructions.md must reference AGENT-RULES.md as the rule source"
    )


def test_copilot_instructions_reasonably_short():
    """copilot-instructions.md must be reasonably short — not a duplicate rule book."""
    lines = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 80, (
        f"copilot-instructions.md has {len(lines)} lines — exceeds the 80-line limit. "
        "Trim duplicated rules and keep it as a pointer to AGENT-RULES.md."
    )


def test_copilot_instructions_comprehensive_reference_note():
    """copilot-instructions.md must note that AGENT-RULES.md is the comprehensive reference."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    has_reference = (
        "comprehensive" in content.lower()
        or "complete" in content.lower()
        or "full" in content.lower()
    )
    assert has_reference, (
        "copilot-instructions.md must note that AGENT-RULES.md is the comprehensive/complete reference"
    )


def test_copilot_instructions_not_just_empty_pointer():
    """copilot-instructions.md must have at least the security denied-actions section."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "Denied" in content or "denied" in content, (
        "copilot-instructions.md must retain the Security — Denied Actions section"
    )
