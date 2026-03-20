# FIX-052 Dev Log — Fix FIX-047 version tests to use dynamic version

## Summary

**Assigned To:** Developer Agent  
**Date:** 2026-03-20  
**Status:** In Progress → Review

## Investigation Findings

Upon inspection of `tests/FIX-047/test_fix047_version.py`, the file already uses
`CURRENT_VERSION` from `tests/shared/version_utils.py`. Commit `adf50a7`
("FIX-049: Fix version test regression pattern — use dynamic version source of
truth") had already addressed this for the FIX-047 test file.

**Evidence:** The test file contains:
```python
# Use the shared version utility instead of hardcoding.
import sys
sys.path.insert(0, str(REPO_ROOT / "tests" / "shared"))
from version_utils import CURRENT_VERSION as TARGET_VERSION
```

No hardcoded "3.0.0" string exists anywhere in `tests/FIX-047/`.

All 11 existing FIX-047 tests pass with the current version (3.0.3).

## Work Performed

Since the fix described in FIX-052 was already applied by FIX-049, this WP's
deliverable is:

1. **Verified** that `tests/FIX-047/test_fix047_version.py` uses dynamic
   versioning (no hardcoded "3.0.0").
2. **Created** `tests/FIX-052/test_fix052_no_hardcoded_version.py` — a regression
   guard that statically checks the FIX-047 test file source for hardcoded version
   strings, ensuring future edits cannot re-introduce them.
3. **Confirmed** all 11 FIX-047 tests pass.

## Files Changed

- `docs/workpackages/workpackages.csv` — Updated FIX-052 status to "In Progress" / "Review"
- `docs/workpackages/FIX-052/dev-log.md` — This file (created)
- `tests/FIX-052/test_fix052_no_hardcoded_version.py` — New regression guard test

## Tests Written

| Test | Description |
|------|-------------|
| `test_no_hardcoded_300_in_fix047_test` | Asserts "3.0.0" does not appear in the FIX-047 test source |
| `test_fix047_imports_version_utils` | Asserts the FIX-047 test file imports from version_utils |
| `test_fix047_tests_all_pass` | Confirms all 11 FIX-047 tests pass via subprocess |

## Test Results

- FIX-047 suite: **11/11 passed**
- FIX-052 suite: **3/3 passed**

## Known Limitations

None. The WP goal ("FIX-047 tests pass without modification after any future
version bump") was already achieved by FIX-049. This WP adds an explicit static
regression guard to prevent regression.
