"""
MNT-019: Tests verifying all 7 agent/instruction files reference .jsonl paths
and contain no stale .csv data-file path references.

File: tests/MNT-019/test_mnt019_agent_jsonl_refs.py
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths to the 7 files under test
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]

AGENT_FILES = {
    "developer": REPO_ROOT / ".github" / "agents" / "developer.agent.md",
    "tester": REPO_ROOT / ".github" / "agents" / "tester.agent.md",
    "orchestrator": REPO_ROOT / ".github" / "agents" / "orchestrator.agent.md",
    "planner": REPO_ROOT / ".github" / "agents" / "planner.agent.md",
    "story-writer": REPO_ROOT / ".github" / "agents" / "story-writer.agent.md",
    "maintenance": REPO_ROOT / ".github" / "agents" / "maintenance.agent.md",
    "copilot-instructions": REPO_ROOT / ".github" / "instructions" / "copilot-instructions.md",
}

# ---------------------------------------------------------------------------
# Patterns for data-file CSV references that must NOT appear
# ---------------------------------------------------------------------------
# Matches paths like workpackages.csv, user-stories.csv, bugs.csv,
# test-results.csv, index.csv — but NOT generic words (no path separator check)
FORBIDDEN_CSV_PATH_PATTERN = re.compile(
    r"workpackages\.csv|user-stories\.csv|bugs\.csv|test-results\.csv|index\.csv",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Expected JSONL references that MUST be present in each file
# ---------------------------------------------------------------------------
EXPECTED_JSONL_REFS = {
    "developer": [
        "workpackages.jsonl",
        "user-stories.jsonl",
        "index.jsonl",
        "test-results.jsonl",
    ],
    "tester": [
        "workpackages.jsonl",
        "user-stories.jsonl",
        "test-results.jsonl",
        "bugs.jsonl",
        "index.jsonl",
    ],
    "orchestrator": [
        "workpackages.jsonl",
        "index.jsonl",
    ],
    "planner": [
        "workpackages.jsonl",
        "bugs.jsonl",
        "index.jsonl",
    ],
    "story-writer": [
        "user-stories.jsonl",
        "index.jsonl",
    ],
    "maintenance": [
        "workpackages.jsonl",
        "user-stories.jsonl",
    ],
    "copilot-instructions": [
        "workpackages.jsonl",
        "user-stories.jsonl",
        "bugs.jsonl",
        "test-results.jsonl",
    ],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def read_file(key: str) -> str:
    path = AGENT_FILES[key]
    assert path.exists(), f"Expected file not found: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# No stale CSV path references
# ---------------------------------------------------------------------------

def test_developer_no_csv_path_refs():
    content = read_file("developer")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"developer.agent.md still contains CSV path refs: {matches}"


def test_tester_no_csv_path_refs():
    content = read_file("tester")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"tester.agent.md still contains CSV path refs: {matches}"


def test_orchestrator_no_csv_path_refs():
    content = read_file("orchestrator")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"orchestrator.agent.md still contains CSV path refs: {matches}"


def test_planner_no_csv_path_refs():
    content = read_file("planner")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"planner.agent.md still contains CSV path refs: {matches}"


def test_story_writer_no_csv_path_refs():
    content = read_file("story-writer")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"story-writer.agent.md still contains CSV path refs: {matches}"


def test_maintenance_no_csv_path_refs():
    content = read_file("maintenance")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"maintenance.agent.md still contains CSV path refs: {matches}"


def test_copilot_instructions_no_csv_path_refs():
    content = read_file("copilot-instructions")
    matches = FORBIDDEN_CSV_PATH_PATTERN.findall(content)
    assert not matches, f"copilot-instructions.md still contains CSV path refs: {matches}"


# ---------------------------------------------------------------------------
# Expected JSONL references are present
# ---------------------------------------------------------------------------

def test_developer_has_jsonl_refs():
    content = read_file("developer")
    for ref in EXPECTED_JSONL_REFS["developer"]:
        assert ref in content, f"developer.agent.md missing expected JSONL ref: {ref}"


def test_tester_has_jsonl_refs():
    content = read_file("tester")
    for ref in EXPECTED_JSONL_REFS["tester"]:
        assert ref in content, f"tester.agent.md missing expected JSONL ref: {ref}"


def test_orchestrator_has_jsonl_refs():
    content = read_file("orchestrator")
    for ref in EXPECTED_JSONL_REFS["orchestrator"]:
        assert ref in content, f"orchestrator.agent.md missing expected JSONL ref: {ref}"


def test_planner_has_jsonl_refs():
    content = read_file("planner")
    for ref in EXPECTED_JSONL_REFS["planner"]:
        assert ref in content, f"planner.agent.md missing expected JSONL ref: {ref}"


def test_story_writer_has_jsonl_refs():
    content = read_file("story-writer")
    for ref in EXPECTED_JSONL_REFS["story-writer"]:
        assert ref in content, f"story-writer.agent.md missing expected JSONL ref: {ref}"


def test_maintenance_has_jsonl_refs():
    content = read_file("maintenance")
    for ref in EXPECTED_JSONL_REFS["maintenance"]:
        assert ref in content, f"maintenance.agent.md missing expected JSONL ref: {ref}"


def test_copilot_instructions_has_jsonl_refs():
    content = read_file("copilot-instructions")
    for ref in EXPECTED_JSONL_REFS["copilot-instructions"]:
        assert ref in content, f"copilot-instructions.md missing expected JSONL ref: {ref}"
