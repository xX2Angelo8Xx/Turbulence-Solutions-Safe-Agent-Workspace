"""
MNT-019 edge-case tests (Tester Agent additions).

Supplements the Developer's tests with:
1. Generic "CSV" word checks (not just specific filename patterns)
2. Verify "JSONL" terminology is used consistently in format descriptions
3. Verify planner.agent.md description paragraph has no CSV/CSVs wording
4. Verify all 7 files exist (basic existence pre-condition)
"""

import re
from pathlib import Path

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

# Any standalone "CSV" or "CSVs" word that is not inside a code block or
# ADR/historical context. We use a broad pattern and then filter context lines.
# Matches: "CSV", "CSVs", "csv", "csvs" — as a standalone word
GENERIC_CSV_WORD_PATTERN = re.compile(r"\bCSVs?\b|\bcsvs?\b")

# Lines that are explicitly exempted because they reference historical context
# (e.g., the ADR decision title "Migrate from CSV to JSONL")
EXEMPTED_PATTERNS = re.compile(
    r"ADR.*CSV|Migrate from CSV|csv-to-jsonl|CSV-to-JSONL|csv_utils|\.csv\b",
    re.IGNORECASE,
)


def _find_generic_csv_in_file(key: str) -> list[str]:
    """Return lines containing generic CSV/CSVs word not in exempted context."""
    path = AGENT_FILES[key]
    assert path.exists(), f"File not found: {path}"
    content = path.read_text(encoding="utf-8")
    violations = []
    for line in content.splitlines():
        if GENERIC_CSV_WORD_PATTERN.search(line):
            if not EXEMPTED_PATTERNS.search(line):
                violations.append(line.strip())
    return violations


# ---------------------------------------------------------------------------
# Edge case 1: No generic "CSV"/"CSVs" references (format descriptions)
# ---------------------------------------------------------------------------

def test_developer_no_generic_csv_word():
    violations = _find_generic_csv_in_file("developer")
    assert not violations, f"developer.agent.md has generic CSV word refs: {violations}"


def test_tester_no_generic_csv_word():
    violations = _find_generic_csv_in_file("tester")
    assert not violations, f"tester.agent.md has generic CSV word refs: {violations}"


def test_orchestrator_no_generic_csv_word():
    violations = _find_generic_csv_in_file("orchestrator")
    assert not violations, f"orchestrator.agent.md has generic CSV word refs: {violations}"


def test_planner_no_generic_csv_word():
    """Regression: planner.agent.md description paragraph had 'edit CSVs'."""
    violations = _find_generic_csv_in_file("planner")
    assert not violations, f"planner.agent.md has generic CSV word refs: {violations}"


def test_story_writer_no_generic_csv_word():
    violations = _find_generic_csv_in_file("story-writer")
    assert not violations, f"story-writer.agent.md has generic CSV word refs: {violations}"


def test_maintenance_no_generic_csv_word():
    violations = _find_generic_csv_in_file("maintenance")
    assert not violations, f"maintenance.agent.md has generic CSV word refs: {violations}"


def test_copilot_instructions_no_generic_csv_word():
    violations = _find_generic_csv_in_file("copilot-instructions")
    assert not violations, f"copilot-instructions.md has generic CSV word refs: {violations}"


# ---------------------------------------------------------------------------
# Edge case 2: All 7 files exist
# ---------------------------------------------------------------------------

def test_all_seven_files_exist():
    missing = [key for key, path in AGENT_FILES.items() if not path.exists()]
    assert not missing, f"Missing agent/instruction files: {missing}"


# ---------------------------------------------------------------------------
# Edge case 3: JSONL files referenced actually exist on disk
# ---------------------------------------------------------------------------

REFERENCED_JSONL_FILES = [
    REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl",
    REPO_ROOT / "docs" / "user-stories" / "user-stories.jsonl",
    REPO_ROOT / "docs" / "bugs" / "bugs.jsonl",
    REPO_ROOT / "docs" / "test-results" / "test-results.jsonl",
    REPO_ROOT / "docs" / "decisions" / "index.jsonl",
]


def test_referenced_jsonl_files_exist():
    missing = [str(p) for p in REFERENCED_JSONL_FILES if not p.exists()]
    assert not missing, f"Referenced JSONL files are missing on disk: {missing}"


# ---------------------------------------------------------------------------
# Edge case 4: "direct JSONL editing prohibited" in tester (not CSV)
# ---------------------------------------------------------------------------

def test_tester_prohibits_direct_jsonl_editing():
    """Verify the tester's constraint says JSONL (not CSV) for direct editing prohibition."""
    content = (AGENT_FILES["tester"]).read_text(encoding="utf-8")
    assert "direct JSONL editing prohibited" in content, (
        "tester.agent.md should say 'direct JSONL editing prohibited'"
    )


# ---------------------------------------------------------------------------
# Edge case 5: "tracking JSONL files" in tester constraints (not "tracking CSVs")
# ---------------------------------------------------------------------------

def test_tester_tracking_terminology():
    """Verify tester constraints say 'JSONL files' not 'CSVs' for tracking."""
    content = (AGENT_FILES["tester"]).read_text(encoding="utf-8")
    assert "tracking JSONL files" in content or "JSONL files" in content, (
        "tester.agent.md should use JSONL terminology in tracking constraints"
    )
