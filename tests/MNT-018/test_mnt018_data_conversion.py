"""MNT-018: Verification that CSV-to-JSONL data conversion completed successfully."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

EXPECTED_JSONL_FILES = [
    ("docs/workpackages/workpackages.jsonl", 300),   # at least 300 rows
    ("docs/user-stories/user-stories.jsonl", 70),
    ("docs/bugs/bugs.jsonl", 150),
    ("docs/test-results/test-results.jsonl", 2000),
    ("docs/decisions/index.jsonl", 5),
    ("docs/maintenance/orchestrator-runs.jsonl", 0),
]

DELETED_CSV_FILES = [
    "docs/workpackages/workpackages.csv",
    "docs/user-stories/user-stories.csv",
    "docs/bugs/bugs.csv",
    "docs/test-results/test-results.csv",
    "docs/decisions/index.csv",
    "docs/maintenance/orchestrator-runs.csv",
]


def test_jsonl_files_exist_with_minimum_rows():
    for rel_path, min_rows in EXPECTED_JSONL_FILES:
        fp = REPO / rel_path
        assert fp.exists(), f"{rel_path} missing"
        lines = [l for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) >= min_rows, f"{rel_path}: expected >= {min_rows} rows, got {len(lines)}"


def test_csv_files_deleted():
    for rel_path in DELETED_CSV_FILES:
        fp = REPO / rel_path
        assert not fp.exists(), f"{rel_path} should have been deleted"


def test_jsonl_rows_are_valid_json():
    for rel_path, _ in EXPECTED_JSONL_FILES:
        fp = REPO / rel_path
        for i, line in enumerate(fp.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    raise AssertionError(f"{rel_path} line {i}: invalid JSON")
