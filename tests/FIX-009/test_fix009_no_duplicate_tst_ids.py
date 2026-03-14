"""
FIX-009: Test that every TST-ID in test-results.csv is unique.
"""
import csv
import os
import pytest

CSV_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.csv'
)


def test_no_duplicate_tst_ids():
    """Every TST-ID in test-results.csv must be unique."""
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    ids = [r['ID'] for r in rows]
    assert len(set(ids)) == len(ids), (
        f"Duplicate TST-IDs found: "
        + str({k: ids.count(k) for k in set(ids) if ids.count(k) > 1})
    )
