"""
MNT-009 — Tester add_bug.py Mandate
Verifies that tester.agent.md explicitly references scripts/add_bug.py
in the Edit Permissions section, Pre-Done Checklist, and Constraints.
"""

import pathlib
import re

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "tester.agent.md"


def _content() -> str:
    return AGENT_FILE.read_text(encoding="utf-8")


def _section(content: str, heading: str) -> str:
    """Return the text of a section starting at *heading* until the next ## heading."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    assert match, f"Section '## {heading}' not found in {AGENT_FILE}"
    return match.group(1)


# ---------------------------------------------------------------------------
# Edit Permissions
# ---------------------------------------------------------------------------

def test_edit_permissions_mentions_add_bug_py():
    section = _section(_content(), "Edit Permissions")
    assert "add_bug.py" in section, (
        "Edit Permissions section must reference scripts/add_bug.py"
    )


def test_edit_permissions_prohibits_direct_csv_editing():
    section = _section(_content(), "Edit Permissions")
    assert "direct CSV editing prohibited" in section.lower() or (
        "direct" in section.lower() and "prohibited" in section.lower()
    ), "Edit Permissions section must state that direct editing of bugs data is prohibited"


# ---------------------------------------------------------------------------
# Pre-Done Checklist
# ---------------------------------------------------------------------------

def test_pre_done_checklist_mentions_add_bug_py():
    section = _section(_content(), "Pre-Done Checklist")
    assert "add_bug.py" in section, (
        "Pre-Done Checklist must reference scripts/add_bug.py as mandatory"
    )


def test_pre_done_checklist_prohibits_direct_bugs_csv_editing():
    section = _section(_content(), "Pre-Done Checklist")
    lower = section.lower()
    assert "bugs.jsonl" in lower and (
        "prohibited" in lower or "never edit" in lower or "direct" in lower
    ), "Pre-Done Checklist must prohibit direct editing of docs/bugs/bugs.jsonl"


def test_pre_done_checklist_add_bug_is_checkbox():
    section = _section(_content(), "Pre-Done Checklist")
    lines = section.splitlines()
    checkbox_lines = [ln for ln in lines if "- [ ]" in ln and "add_bug.py" in ln]
    assert checkbox_lines, (
        "Pre-Done Checklist must have a checkbox item (- [ ]) referencing add_bug.py"
    )


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

def test_constraints_mentions_add_bug_py():
    section = _section(_content(), "Constraints")
    assert "add_bug.py" in section, (
        "Constraints section must reference scripts/add_bug.py"
    )


def test_constraints_prohibits_direct_bugs_csv_editing():
    section = _section(_content(), "Constraints")
    lower = section.lower()
    assert "bugs.jsonl" in lower and "prohibited" in lower, (
        "Constraints section must state that direct editing of docs/bugs/bugs.jsonl is prohibited"
    )


# ---------------------------------------------------------------------------
# Overall file sanity
# ---------------------------------------------------------------------------

def test_file_exists():
    assert AGENT_FILE.exists(), f"tester.agent.md not found at {AGENT_FILE}"


def test_add_bug_py_appears_in_multiple_sections():
    content = _content()
    count = content.count("add_bug.py")
    assert count >= 3, (
        f"scripts/add_bug.py should appear in at least 3 places in tester.agent.md, found {count}"
    )


# ---------------------------------------------------------------------------
# Tester edge-case additions — full script path must be used everywhere
# ---------------------------------------------------------------------------

def test_edit_permissions_uses_full_script_path():
    """Bare 'add_bug.py' is not actionable — must include the 'scripts/' prefix."""
    section = _section(_content(), "Edit Permissions")
    assert "scripts/add_bug.py" in section, (
        "Edit Permissions must reference 'scripts/add_bug.py' (full path), not just 'add_bug.py'"
    )


def test_pre_done_checklist_uses_full_script_path():
    """Bare 'add_bug.py' is not actionable — must include the 'scripts/' prefix."""
    section = _section(_content(), "Pre-Done Checklist")
    assert "scripts/add_bug.py" in section, (
        "Pre-Done Checklist must reference 'scripts/add_bug.py' (full path), not just 'add_bug.py'"
    )


def test_constraints_uses_full_script_path():
    """Bare 'add_bug.py' is not actionable — must include the 'scripts/' prefix."""
    section = _section(_content(), "Constraints")
    assert "scripts/add_bug.py" in section, (
        "Constraints must reference 'scripts/add_bug.py' (full path), not just 'add_bug.py'"
    )
