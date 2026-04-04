"""
MNT-020: Verify no stale .csv path references remain in the 9 work-rules and architecture docs.

Each test checks a specific file for the absence of stale .csv operational path references
and (where applicable) the presence of expected .jsonl references.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The 9 target files
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

# Patterns that constitute stale CSV path references (not ADR filenames, not tree listings)
# We look for specific known-bad strings that should have been updated.
STALE_PATTERNS = [
    r"workpackages\.csv",
    r"user-stories\.csv",
    r"bugs\.csv",
    r"test-results\.csv",
    r"decisions/index\.csv",
]

# Allowed exceptions: patterns that are OK to stay (historical, ADR filenames, directory trees)
ALLOWED_EXCEPTIONS = [
    r"ADR-007-csv-to-jsonl-migration",   # ADR filename — historical
    r"csv_utils\.py",                    # deprecated script listing in directory tree
    r"migrate_csv_to_jsonl",             # migration script listing
]


def _has_stale_csv_ref(file_path: Path) -> list[str]:
    """Return list of matching stale lines in the file."""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    bad_lines = []
    for lineno, line in enumerate(lines, 1):
        for pattern in STALE_PATTERNS:
            if re.search(pattern, line):
                # Check if this line is an allowed exception
                is_exception = any(re.search(exc, line) for exc in ALLOWED_EXCEPTIONS)
                if not is_exception:
                    bad_lines.append(f"  Line {lineno}: {line.strip()}")
    return bad_lines


def test_index_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["index.md"])
    assert not bad, f"Stale .csv references in index.md:\n" + "\n".join(bad)


def test_agent_workflow_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["agent-workflow.md"])
    assert not bad, f"Stale .csv references in agent-workflow.md:\n" + "\n".join(bad)


def test_workpackage_rules_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["workpackage-rules.md"])
    assert not bad, f"Stale .csv references in workpackage-rules.md:\n" + "\n".join(bad)


def test_bug_tracking_rules_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["bug-tracking-rules.md"])
    assert not bad, f"Stale .csv references in bug-tracking-rules.md:\n" + "\n".join(bad)


def test_user_story_rules_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["user-story-rules.md"])
    assert not bad, f"Stale .csv references in user-story-rules.md:\n" + "\n".join(bad)


def test_testing_protocol_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["testing-protocol.md"])
    assert not bad, f"Stale .csv references in testing-protocol.md:\n" + "\n".join(bad)


def test_maintenance_protocol_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["maintenance-protocol.md"])
    assert not bad, f"Stale .csv references in maintenance-protocol.md:\n" + "\n".join(bad)


def test_recovery_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["recovery.md"])
    assert not bad, f"Stale .csv references in recovery.md:\n" + "\n".join(bad)


def test_architecture_md_no_stale_csv():
    bad = _has_stale_csv_ref(TARGET_FILES["architecture.md"])
    assert not bad, f"Stale .csv references in architecture.md:\n" + "\n".join(bad)


# --- Positive checks: expected .jsonl references are present ---

def test_index_md_has_jsonl_references():
    text = TARGET_FILES["index.md"].read_text(encoding="utf-8")
    assert "workpackages.jsonl" in text, "index.md missing workpackages.jsonl reference"
    assert "user-stories.jsonl" in text, "index.md missing user-stories.jsonl reference"
    assert "bugs.jsonl" in text, "index.md missing bugs.jsonl reference"
    assert "test-results.jsonl" in text, "index.md missing test-results.jsonl reference"
    assert "index.jsonl" in text, "index.md missing decisions/index.jsonl reference"


def test_workpackage_rules_md_has_jsonl_fields_section():
    text = TARGET_FILES["workpackage-rules.md"].read_text(encoding="utf-8")
    assert "## JSONL Fields" in text, "workpackage-rules.md missing '## JSONL Fields' section"
    assert "workpackages.jsonl" in text, "workpackage-rules.md missing workpackages.jsonl reference"


def test_bug_tracking_rules_md_has_jsonl_fields_section():
    text = TARGET_FILES["bug-tracking-rules.md"].read_text(encoding="utf-8")
    assert "## JSONL Fields" in text, "bug-tracking-rules.md missing '## JSONL Fields' section"
    assert "bugs.jsonl" in text, "bug-tracking-rules.md missing bugs.jsonl reference"


def test_user_story_rules_md_has_jsonl_fields_section():
    text = TARGET_FILES["user-story-rules.md"].read_text(encoding="utf-8")
    assert "## JSONL Fields" in text, "user-story-rules.md missing '## JSONL Fields' section"
    assert "user-stories.jsonl" in text, "user-story-rules.md missing user-stories.jsonl reference"


def test_testing_protocol_md_has_jsonl_section():
    text = TARGET_FILES["testing-protocol.md"].read_text(encoding="utf-8")
    assert "test-results.jsonl" in text, "testing-protocol.md missing test-results.jsonl reference"
    assert "## Test Result JSONL" in text, "testing-protocol.md missing '## Test Result JSONL' section"


def test_maintenance_protocol_md_has_jsonl_integrity_section():
    text = TARGET_FILES["maintenance-protocol.md"].read_text(encoding="utf-8")
    assert "### 3. JSONL Integrity" in text, "maintenance-protocol.md missing '### 3. JSONL Integrity' section"


def test_recovery_md_has_jsonl_section():
    text = TARGET_FILES["recovery.md"].read_text(encoding="utf-8")
    assert "## Corrupt JSONL File" in text, "recovery.md missing '## Corrupt JSONL File' section"
    assert "jsonl_utils.py" in text, "recovery.md missing jsonl_utils.py reference"


def test_agent_workflow_md_has_jsonl_references():
    text = TARGET_FILES["agent-workflow.md"].read_text(encoding="utf-8")
    assert "workpackages.jsonl" in text, "agent-workflow.md missing workpackages.jsonl reference"
    assert "index.jsonl" in text, "agent-workflow.md missing decisions/index.jsonl reference"


def test_architecture_md_has_jsonl_reference():
    text = TARGET_FILES["architecture.md"].read_text(encoding="utf-8")
    assert "workpackages.jsonl" in text, "architecture.md missing workpackages.jsonl reference"
