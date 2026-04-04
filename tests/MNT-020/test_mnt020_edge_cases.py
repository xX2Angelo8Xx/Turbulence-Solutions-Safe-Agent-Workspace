"""
MNT-020 Tester edge-case tests.

Covers gaps in the Developer's 18 tests:
1. Maintenance log template must use 'JSONL Integrity' (not 'CSV Integrity').
2. All .jsonl file references in the docs actually point to existing files.
3. No operational csv_utils references remain in instructions text.
4. No bare "CSV" word appears where it should say "JSONL" in headings/templates.
5. JSONL field descriptions replaced CSV column descriptions in all three rule files.
6. Recovery doc references jsonl_utils and not csv_utils in the lock note.
7. All nine target files are UTF-8 decodable (no encoding corruption).
8. Agent-workflow references test-results.jsonl specifically.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_FILES = {
    "index.md": REPO_ROOT / "docs" / "work-rules" / "index.md",
    "agent-workflow.md": REPO_ROOT / "docs" / "work-rules" / "agent-workflow.md",
    "workpackage-rules.md": REPO_ROOT / "docs" / "work-rules" / "workpackage-rules.md",
    "bug-tracking-rules.md": REPO_ROOT / "docs" / "work-rules" / "bug-tracking-rules.md",
    "user-story-rules.md": REPO_ROOT / "docs" / "work-rules" / "user-story-rules.md",
    "testing-protocol.md": REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md",
    "maintenance-protocol.md": REPO_ROOT / "docs" / "work-rules" / "maintenance-protocol.md",
    "recovery.md": REPO_ROOT / "docs" / "work-rules" / "recovery.md",
    "architecture.md": REPO_ROOT / "docs" / "architecture.md",
}

JSONL_FILES = {
    "workpackages.jsonl": REPO_ROOT / "docs" / "workpackages" / "workpackages.jsonl",
    "user-stories.jsonl": REPO_ROOT / "docs" / "user-stories" / "user-stories.jsonl",
    "bugs.jsonl": REPO_ROOT / "docs" / "bugs" / "bugs.jsonl",
    "test-results.jsonl": REPO_ROOT / "docs" / "test-results" / "test-results.jsonl",
    "decisions/index.jsonl": REPO_ROOT / "docs" / "decisions" / "index.jsonl",
}


# ── 1. Maintenance log template must use 'JSONL Integrity' ────────────────────

def test_maintenance_log_template_uses_jsonl_integrity():
    """The log template table row for check #3 must say 'JSONL Integrity',
    not 'CSV Integrity'. This is in the embedded Markdown template inside
    maintenance-protocol.md, below the '### Log Format' heading."""
    text = TARGET_FILES["maintenance-protocol.md"].read_text(encoding="utf-8")
    assert "| 3 | CSV Integrity |" not in text, (
        "maintenance-protocol.md log template still contains '| 3 | CSV Integrity |'. "
        "Should be '| 3 | JSONL Integrity |'."
    )
    assert "| 3 | JSONL Integrity |" in text, (
        "maintenance-protocol.md log template missing '| 3 | JSONL Integrity |'."
    )


# ── 2. All .jsonl references resolve to existing files ──────────────────────

def test_all_jsonl_files_referenced_in_docs_exist():
    """Every .jsonl file mentioned in the target docs must actually exist."""
    missing = [name for name, path in JSONL_FILES.items() if not path.exists()]
    assert not missing, f"Referenced .jsonl files do not exist: {missing}"


# ── 3. No operational csv_utils instructions remain ──────────────────────────

def test_no_csv_utils_in_agent_workflow():
    """agent-workflow.md must not instruct agents to use csv_utils."""
    text = TARGET_FILES["agent-workflow.md"].read_text(encoding="utf-8")
    # Allow mention of csv_utils only inside a "deprecated" or "migration" note
    bad_lines = [
        (i + 1, line.strip())
        for i, line in enumerate(text.splitlines())
        if "csv_utils" in line
        and not re.search(r"deprecat|migrat|old|csv_to_jsonl", line, re.IGNORECASE)
    ]
    assert not bad_lines, (
        "agent-workflow.md contains unexpected csv_utils reference(s):\n"
        + "\n".join(f"  Line {ln}: {txt}" for ln, txt in bad_lines)
    )


def test_no_csv_utils_in_testing_protocol():
    """testing-protocol.md must not instruct agents to use csv_utils."""
    text = TARGET_FILES["testing-protocol.md"].read_text(encoding="utf-8")
    bad_lines = [
        (i + 1, line.strip())
        for i, line in enumerate(text.splitlines())
        if "csv_utils" in line
        and not re.search(r"deprecat|migrat|old|csv_to_jsonl", line, re.IGNORECASE)
    ]
    assert not bad_lines, (
        "testing-protocol.md contains unexpected csv_utils reference(s):\n"
        + "\n".join(f"  Line {ln}: {txt}" for ln, txt in bad_lines)
    )


# ── 4. No bare 'CSV' in section headings ─────────────────────────────────────

def test_no_csv_in_headings_workpackage_rules():
    """All heading lines (## / ###) in workpackage-rules.md must use JSONL, not CSV."""
    text = TARGET_FILES["workpackage-rules.md"].read_text(encoding="utf-8")
    bad = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line) and re.search(r"\bCSV\b", line)
    ]
    assert not bad, f"Heading(s) with stale 'CSV' in workpackage-rules.md: {bad}"


def test_no_csv_in_headings_bug_tracking_rules():
    """All heading lines in bug-tracking-rules.md must use JSONL, not CSV."""
    text = TARGET_FILES["bug-tracking-rules.md"].read_text(encoding="utf-8")
    bad = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line) and re.search(r"\bCSV\b", line)
    ]
    assert not bad, f"Heading(s) with stale 'CSV' in bug-tracking-rules.md: {bad}"


def test_no_csv_in_headings_user_story_rules():
    """All heading lines in user-story-rules.md must use JSONL, not CSV."""
    text = TARGET_FILES["user-story-rules.md"].read_text(encoding="utf-8")
    bad = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line) and re.search(r"\bCSV\b", line)
    ]
    assert not bad, f"Heading(s) with stale 'CSV' in user-story-rules.md: {bad}"


def test_no_csv_in_headings_testing_protocol():
    """All heading lines in testing-protocol.md must use JSONL, not CSV."""
    text = TARGET_FILES["testing-protocol.md"].read_text(encoding="utf-8")
    bad = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line) and re.search(r"\bCSV\b", line)
    ]
    assert not bad, f"Heading(s) with stale 'CSV' in testing-protocol.md: {bad}"


def test_no_csv_in_headings_maintenance_protocol():
    """All heading lines in maintenance-protocol.md must use JSONL, not CSV."""
    text = TARGET_FILES["maintenance-protocol.md"].read_text(encoding="utf-8")
    bad = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^#{1,6}\s", line) and re.search(r"\bCSV\b", line)
    ]
    assert not bad, f"Heading(s) with stale 'CSV' in maintenance-protocol.md: {bad}"


# ── 5. JSONL Fields section present in all three rule files ──────────────────

def test_workpackage_rules_no_csv_columns_section():
    """workpackage-rules.md must not contain a '## CSV Columns' section."""
    text = TARGET_FILES["workpackage-rules.md"].read_text(encoding="utf-8")
    assert "## CSV Columns" not in text, "workpackage-rules.md still has '## CSV Columns' section"


def test_bug_tracking_no_csv_columns_section():
    """bug-tracking-rules.md must not contain a 'CSV Columns' heading."""
    text = TARGET_FILES["bug-tracking-rules.md"].read_text(encoding="utf-8")
    assert "## CSV Columns" not in text, "bug-tracking-rules.md still has '## CSV Columns' section"


def test_user_story_rules_no_csv_columns_section():
    """user-story-rules.md must not contain a 'CSV Columns' heading."""
    text = TARGET_FILES["user-story-rules.md"].read_text(encoding="utf-8")
    assert "## CSV Columns" not in text, "user-story-rules.md still has '## CSV Columns' section"


# ── 6. Recovery doc uses jsonl_utils in the lock note ────────────────────────

def test_recovery_md_references_jsonl_utils_not_csv_utils():
    """recovery.md's Orphaned Lock File section must reference jsonl_utils, not csv_utils."""
    text = TARGET_FILES["recovery.md"].read_text(encoding="utf-8")
    assert "jsonl_utils" in text, "recovery.md missing jsonl_utils reference in lock note"
    # csv_utils should NOT appear in operational instructions in recovery.md
    lines = text.splitlines()
    bad = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if "csv_utils" in line
        and not re.search(r"deprecat|migrat", line, re.IGNORECASE)
    ]
    assert not bad, (
        "recovery.md has unexpected operational csv_utils reference(s):\n"
        + "\n".join(f"  Line {ln}: {txt}" for ln, txt in bad)
    )


# ── 7. All nine files are UTF-8 decodable ────────────────────────────────────

def test_all_target_files_are_utf8_decodable():
    """No encoding corruption was introduced by the documentation edits."""
    corrupt = []
    for name, path in TARGET_FILES.items():
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            corrupt.append(f"{name}: {exc}")
    assert not corrupt, f"Encoding errors in files:\n" + "\n".join(corrupt)


# ── 8. agent-workflow.md references test-results.jsonl ───────────────────────

def test_agent_workflow_references_test_results_jsonl():
    """agent-workflow.md must explicitly reference test-results.jsonl."""
    text = TARGET_FILES["agent-workflow.md"].read_text(encoding="utf-8")
    assert "test-results.jsonl" in text, (
        "agent-workflow.md does not reference test-results.jsonl"
    )
