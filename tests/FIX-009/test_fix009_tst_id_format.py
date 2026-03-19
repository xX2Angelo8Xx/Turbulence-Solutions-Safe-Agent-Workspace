"""
FIX-009: Test that every TST-ID matches the TST-NNN format.
"""
import csv
import os
import re
import pytest

CSV_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.csv'
)

TST_ID_PATTERN = re.compile(r'^TST-\d+$')


def test_tst_id_format():
    """Every ID in test-results.csv must match the TST-NNN format."""
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    bad_ids = [r['ID'] for r in rows if not TST_ID_PATTERN.match(r['ID'])]
    assert bad_ids == [], f"IDs with invalid format: {bad_ids}"
