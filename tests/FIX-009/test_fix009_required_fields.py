"""
FIX-009: Test that required fields in test-results.csv are non-empty.
"""
import csv
import os
import pytest

CSV_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.csv'
)

REQUIRED_FIELDS = ['ID', 'Test Name', 'Test Type', 'WP Reference', 'Status',
                   'Run Date', 'Environment', 'Result']


def test_required_fields_not_empty():
    """No required field may be blank in any row of test-results.csv."""
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    violations = []
    for i, row in enumerate(rows, start=2):  # start=2: header is line 1
        for field in REQUIRED_FIELDS:
            if not row.get(field, '').strip():
                violations.append(f"Row {i} (ID={row.get('ID', '?')}): field '{field}' is empty")

    assert violations == [], "Empty required fields found:\n" + "\n".join(violations[:20])
