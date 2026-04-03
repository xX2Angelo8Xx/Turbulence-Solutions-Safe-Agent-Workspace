"""
MNT-007 verification tests — no raw 'pytest tests/ -v' in agent/work-rules files.

Goal: grep for the banned pattern returns 0 matches across all agent files
and work-rules markdown files.
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

BANNED_PATTERN = re.compile(r"pytest tests/ -v")

AGENT_FILES = [
    REPO_ROOT / ".github" / "agents" / "developer.agent.md",
    REPO_ROOT / ".github" / "agents" / "tester.agent.md",
    REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md",
]

WORK_RULES_FILES = list((REPO_ROOT / "docs" / "work-rules").glob("*.md"))


def _search_file(path: pathlib.Path) -> list[int]:
    """Return line numbers where the banned pattern appears."""
    lines_found = []
    if not path.exists():
        return lines_found
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if BANNED_PATTERN.search(line):
            lines_found.append(i)
    return lines_found


def test_developer_agent_no_raw_pytest():
    developer_md = REPO_ROOT / ".github" / "agents" / "developer.agent.md"
    hits = _search_file(developer_md)
    assert hits == [], (
        f"developer.agent.md still contains banned pattern 'pytest tests/ -v' "
        f"at line(s): {hits}"
    )


def test_tester_agent_no_raw_pytest():
    tester_md = REPO_ROOT / ".github" / "agents" / "tester.agent.md"
    hits = _search_file(tester_md)
    assert hits == [], (
        f"tester.agent.md still contains banned pattern 'pytest tests/ -v' "
        f"at line(s): {hits}"
    )


def test_agent_workflow_no_raw_pytest():
    workflow_md = REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md"
    hits = _search_file(workflow_md)
    assert hits == [], (
        f"agent-workflow.md still contains banned pattern 'pytest tests/ -v' "
        f"at line(s): {hits}"
    )


def test_testing_protocol_no_raw_pytest():
    protocol_md = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"
    hits = _search_file(protocol_md)
    assert hits == [], (
        f"testing-protocol.md still contains banned pattern 'pytest tests/ -v' "
        f"at line(s): {hits}"
    )


def test_all_work_rules_no_raw_pytest():
    """Exhaustive check — no work-rules file contains the banned pattern."""
    failures = {}
    for path in WORK_RULES_FILES:
        hits = _search_file(path)
        if hits:
            failures[path.name] = hits
    assert failures == {}, (
        f"The following work-rules files still contain the banned pattern: {failures}"
    )
