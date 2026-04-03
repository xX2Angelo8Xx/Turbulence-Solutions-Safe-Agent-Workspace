"""
MNT-007 verification tests — all three target files mandate run_tests.py.

Asserts that each of the three files edited by MNT-007 contains a reference
to 'run_tests.py' as the mandatory pre-handoff test tool.
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

TARGET_FILES = {
    "agent-workflow.md": REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md",
    "developer.agent.md": REPO_ROOT / ".github" / "agents" / "developer.agent.md",
    "testing-protocol.md": REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md",
}

REQUIRED_PHRASE = "run_tests.py"


def _file_mentions(path: pathlib.Path, phrase: str) -> bool:
    return phrase in path.read_text(encoding="utf-8")


def test_agent_workflow_mentions_run_tests():
    path = TARGET_FILES["agent-workflow.md"]
    assert _file_mentions(path, REQUIRED_PHRASE), (
        "agent-workflow.md does not reference 'run_tests.py' — Step 5 is still contradictory"
    )


def test_developer_agent_mentions_run_tests():
    path = TARGET_FILES["developer.agent.md"]
    assert _file_mentions(path, REQUIRED_PHRASE), (
        "developer.agent.md does not reference 'run_tests.py' in the pre-handoff checklist"
    )


def test_testing_protocol_mentions_run_tests_mandatory():
    path = TARGET_FILES["testing-protocol.md"]
    content = path.read_text(encoding="utf-8")
    assert "run_tests.py" in content, (
        "testing-protocol.md does not reference 'run_tests.py'"
    )
    # The mandatory section must explicitly call it the primary tool
    assert "scripts/run_tests.py" in content, (
        "testing-protocol.md does not contain 'scripts/run_tests.py'"
    )


def test_agent_workflow_step5_mentions_run_tests():
    """Step 5 specifically (not just elsewhere in the file) must reference run_tests.py."""
    path = TARGET_FILES["agent-workflow.md"]
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    step5_line = next(
        (l for l in lines if l.startswith("| 5 |") and "Test" in l),
        None,
    )
    assert step5_line is not None, "Could not find Step 5 row in agent-workflow.md table"
    assert "run_tests.py" in step5_line, (
        f"Step 5 in agent-workflow.md does not mention 'run_tests.py'.\nRow: {step5_line}"
    )


def test_developer_agent_checklist_references_run_tests():
    """The pre-handoff checklist item must explicitly reference run_tests.py."""
    path = TARGET_FILES["developer.agent.md"]
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    checklist_items = [l for l in lines if l.startswith("- [ ]")]
    run_tests_items = [l for l in checklist_items if "run_tests.py" in l]
    assert run_tests_items, (
        "No pre-handoff checklist item in developer.agent.md references 'run_tests.py'.\n"
        f"Checklist items found: {checklist_items}"
    )
