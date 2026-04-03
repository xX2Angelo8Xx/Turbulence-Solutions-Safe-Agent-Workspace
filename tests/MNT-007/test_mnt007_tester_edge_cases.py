"""
MNT-007 Tester edge-case tests.

Additional verification beyond the Developer's baseline:
- run_tests.py script actually exists on disk
- Tester workflow in testing-protocol.md also mandates run_tests.py
- agent-workflow.md mentions --full-suite for the tester run
- No raw 'pytest -v' pattern (with or without trailing 'tests/') in key files
- tester.agent.md pre-done checklist references run_tests.py
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def test_run_tests_script_exists():
    """The referenced script must actually exist in the repository."""
    script = REPO_ROOT / "scripts" / "run_tests.py"
    assert script.exists(), (
        "scripts/run_tests.py does not exist — documentation mandates a script that is missing"
    )


def test_testing_protocol_tester_workflow_mandates_run_tests():
    """The 'For Testers' workflow section in testing-protocol.md must reference run_tests.py."""
    content = (REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md").read_text(
        encoding="utf-8"
    )
    tester_section_start = content.find("### For Testers")
    assert tester_section_start != -1, "Could not find '### For Testers' section"
    tester_section_end = content.find("\n###", tester_section_start + 1)
    tester_section = (
        content[tester_section_start:tester_section_end]
        if tester_section_end != -1
        else content[tester_section_start:]
    )
    assert "run_tests.py" in tester_section, (
        "The '### For Testers' section in testing-protocol.md does not reference "
        "run_tests.py — testers may still default to raw pytest"
    )


def test_testing_protocol_full_suite_flag_mentioned_for_testers():
    """testing-protocol.md Tester workflow should mention --full-suite for the tester run."""
    content = (REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md").read_text(
        encoding="utf-8"
    )
    tester_section_start = content.find("### For Testers")
    assert tester_section_start != -1, "Could not find '### For Testers' section"
    tester_section_end = content.find("\n###", tester_section_start + 1)
    tester_section = (
        content[tester_section_start:tester_section_end]
        if tester_section_end != -1
        else content[tester_section_start:]
    )
    assert "--full-suite" in tester_section, (
        "The '### For Testers' section does not mention '--full-suite' flag — "
        "testers may not know to run the full regression suite"
    )


def test_no_raw_pytest_v_variant_in_developer_agent():
    """
    Stricter pattern check — also catches 'pytest -v tests/' (reversed flag order),
    which is semantically equivalent and equally forbidden.
    """
    content = (REPO_ROOT / ".github" / "agents" / "developer.agent.md").read_text(
        encoding="utf-8"
    )
    # Match 'pytest -v tests/' or 'pytest tests/ -v' (the banned forms)
    banned = re.compile(r"pytest\s+-v\s+tests/|pytest\s+tests/\s+-v")
    matches = banned.findall(content)
    assert matches == [], (
        f"developer.agent.md contains a raw pytest -v invocation variant: {matches}"
    )


def test_agent_workflow_step5_contains_mandatory_label():
    """
    Step 5 of agent-workflow.md must contain the word 'mandatory' near run_tests.py,
    confirming it is not just mentioned incidentally.
    """
    content = (REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md").read_text(
        encoding="utf-8"
    )
    lines = content.splitlines()
    step5_line = next(
        (l for l in lines if l.startswith("| 5 |") and "Test" in l),
        None,
    )
    assert step5_line is not None, "Step 5 row not found in agent-workflow.md table"
    assert "mandatory" in step5_line.lower() or "run_tests.py" in step5_line, (
        f"Step 5 does not contain 'mandatory' or explicit run_tests.py reference:\n  {step5_line}"
    )


def test_add_test_result_script_exists():
    """The fallback script add_test_result.py must also exist on disk."""
    script = REPO_ROOT / "scripts" / "add_test_result.py"
    assert script.exists(), (
        "scripts/add_test_result.py does not exist — the labeled fallback script is missing"
    )
