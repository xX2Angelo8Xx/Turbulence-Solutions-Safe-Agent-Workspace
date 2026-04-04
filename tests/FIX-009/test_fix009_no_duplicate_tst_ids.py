"""
FIX-009: Test that every TST-ID in test-results.jsonl is unique.
"""
import json
import os
import pytest

JSONL_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.jsonl'
)


def test_no_duplicate_tst_ids():
    """Every TST-ID in test-results.jsonl must be unique."""
    rows = []
    with open(JSONL_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    ids = [r['ID'] for r in rows]
    assert len(set(ids)) == len(ids), (
        f"Duplicate TST-IDs found: "
        + str({k: ids.count(k) for k in set(ids) if ids.count(k) > 1})
    )
