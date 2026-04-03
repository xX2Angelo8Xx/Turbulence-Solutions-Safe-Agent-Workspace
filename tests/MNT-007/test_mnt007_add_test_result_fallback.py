"""
MNT-007 verification tests — add_test_result.py labeled as fallback in developer checklist.

After MNT-007, the developer checklist must not present add_test_result.py as the primary
mandatory tool. It must be labeled as fallback for when run_tests.py cannot be used.
"""

import pathlib

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DEVELOPER_AGENT = REPO_ROOT / ".github" / "agents" / "developer.agent.md"


def _checklist_lines(path: pathlib.Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [l for l in content.splitlines() if l.startswith("- [ ]")]


def test_add_test_result_not_primary_checklist_item():
    """
    The add_test_result.py checklist bullet must indicate it's a fallback,
    not the primary test execution tool.
    """
    lines = _checklist_lines(DEVELOPER_AGENT)
    # Find the item referencing add_test_result.py
    add_test_result_items = [l for l in lines if "add_test_result.py" in l]
    for item in add_test_result_items:
        # The item must contain a qualifier like "fallback" or "If run_tests.py was not used"
        assert "fallback" in item.lower() or "if" in item.lower(), (
            f"add_test_result.py checklist item does not indicate it is a fallback:\n  {item}"
        )


def test_run_tests_appears_before_add_test_result_in_checklist():
    """
    run_tests.py must appear as a checklist item before add_test_result.py
    (primary before fallback).
    """
    content = DEVELOPER_AGENT.read_text(encoding="utf-8")
    lines = content.splitlines()
    checklist_lines_with_index = [
        (i, l) for i, l in enumerate(lines) if l.startswith("- [ ]")
    ]

    run_tests_idx = next(
        (i for i, l in checklist_lines_with_index if "run_tests.py" in l), None
    )
    add_result_idx = next(
        (i for i, l in checklist_lines_with_index if "add_test_result.py" in l), None
    )

    assert run_tests_idx is not None, (
        "No checklist item referencing 'run_tests.py' found in developer.agent.md"
    )
    assert add_result_idx is not None, (
        "No checklist item referencing 'add_test_result.py' found in developer.agent.md"
    )
    assert run_tests_idx < add_result_idx, (
        "run_tests.py checklist item should appear before the add_test_result.py fallback item"
    )


def test_testing_protocol_add_test_result_labeled_fallback():
    """testing-protocol.md TST-ID Uniqueness section must label add_test_result as fallback."""
    content = (REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md").read_text(
        encoding="utf-8"
    )
    # The section should say something like "fallback" near add_test_result.py
    # Find the TST-ID Uniqueness section
    section_start = content.find("## TST-ID Uniqueness")
    assert section_start != -1, "Could not find '## TST-ID Uniqueness' section in testing-protocol.md"
    section_end = content.find("\n## ", section_start + 1)
    section = content[section_start:section_end] if section_end != -1 else content[section_start:]
    assert "fallback" in section.lower(), (
        "The TST-ID Uniqueness section in testing-protocol.md does not describe "
        "add_test_result.py as a fallback tool."
    )
