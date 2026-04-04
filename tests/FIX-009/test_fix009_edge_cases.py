"""
FIX-009 Tester Edge-Case Tests

Additional tests beyond the Developer's suite:
  - TST-786+ range is strictly sequential with no gaps
  - WP Reference column has no empty values
  - All Run Date values are valid ISO 8601 calendar dates
"""
import json
import datetime
import os
import re

import pytest

JSONL_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'docs', 'test-results', 'test-results.jsonl'
)


def _load_rows():
    rows = []
    with open(JSONL_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_tst_ids_sequential_no_gaps_in_renumbered_range():
    """
    The deduplication script assigned TST-786 through TST-943 to previously
    duplicate rows plus new FIX-006/FIX-007/FIX-009 entries.  All numeric IDs
    from 786 up to the current maximum must form a contiguous sequence with no
    gaps or unexpected jumps.
    """
    rows = _load_rows()

    def _to_int(row_id):
        try:
            return int(row_id.split('-')[1])
        except (ValueError, IndexError):
            return None

    nums = sorted(
        n for r in rows
        if r['ID'].startswith('TST-')
        for n in [_to_int(r['ID'])]
        if n is not None and n >= 786
    )
    if not nums:
        pytest.skip('No renumbered IDs found (range 786+)')

    min_n = nums[0]
    max_n = nums[-1]
    expected = list(range(min_n, max_n + 1))
    missing = sorted(set(expected) - set(nums))
    extras = sorted(set(nums) - set(expected))
    assert missing == [], (
        f'Missing TST-IDs in renumbered range {min_n}-{max_n}: '
        + ','.join(f'TST-{n}' for n in missing)
    )
    assert extras == [], (
        f'Unexpected TST-IDs outside contiguous sequence: '
        + ','.join(f'TST-{n}' for n in extras)
    )


def test_wp_reference_not_empty_for_all_rows():
    """
    Every row in test-results.jsonl must have a non-blank WP Reference.
    The deduplication run should not have introduced rows without a WP linkage.
    """
    rows = _load_rows()
    empty_refs = [
        f"row CSV line ~{i + 2} (ID={r.get('ID', '?')})"
        for i, r in enumerate(rows)
        if not r.get('WP Reference', '').strip()
    ]
    assert empty_refs == [], (
        f'{len(empty_refs)} rows have an empty WP Reference:\n'
        + '\n'.join(empty_refs[:20])
    )


def test_all_run_dates_are_valid_iso8601():
    """
    Every Run Date must be a valid ISO 8601 calendar date (YYYY-MM-DD) and must
    represent a real calendar day (e.g. 2026-02-30 must be rejected).
    """
    rows = _load_rows()
    iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    bad = []
    for r in rows:
        d = r.get('Run Date', '').strip()
        if not iso_pattern.match(d):
            bad.append(f"ID={r['ID']}: '{d}' does not match YYYY-MM-DD")
            continue
        try:
            datetime.date.fromisoformat(d)
        except ValueError:
            bad.append(f"ID={r['ID']}: '{d}' is not a real calendar date")

    assert bad == [], (
        f'{len(bad)} invalid Run Date values:\n' + '\n'.join(bad[:20])
    )
