"""
FIX-009: Test that required fields in test-results.jsonl are non-empty.
"""
import json
import os
import pytest

JSONL_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.jsonl'
)

REQUIRED_FIELDS = ['ID', 'Test Name', 'Test Type', 'WP Reference', 'Status',
                   'Run Date', 'Environment', 'Result']


def _load_rows():
    rows = []
    with open(JSONL_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_required_fields_not_empty():
    """No required field may be blank in any row of test-results.jsonl."""
    rows = _load_rows()

    violations = []
    for i, row in enumerate(rows, start=1):
        for field in REQUIRED_FIELDS:
            if not row.get(field, '').strip():
                violations.append(f"Row {i} (ID={row.get('ID', '?')}): field '{field}' is empty")

    assert violations == [], "Empty required fields found:\n" + "\n".join(violations[:20])
