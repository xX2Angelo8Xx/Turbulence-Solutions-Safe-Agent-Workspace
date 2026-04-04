"""
FIX-009: Test that every TST-ID matches the TST-NNN format.
"""
import json
import os
import re
import pytest

JSONL_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.jsonl'
)

TST_ID_PATTERN = re.compile(r'^TST-\d+$')


def test_tst_id_format():
    """Every ID in test-results.jsonl must match the TST-NNN format."""
    rows = []
    with open(JSONL_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    bad_ids = [r['ID'] for r in rows if not TST_ID_PATTERN.match(r['ID'])]
    assert bad_ids == [], f"IDs with invalid format: {bad_ids}"
