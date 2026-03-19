# Dev Log — FIX-044

**WP ID:** FIX-044  
**Title:** Fix PermissionError on read-only template .md with placeholders  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-18  
**Branch:** FIX-044/fix-readonly-placeholder  

---

## Problem

`replace_template_placeholders()` in `src/launcher/core/project_creator.py` had
an asymmetry between its read guard and write guard:

- **Read** was wrapped in `try/except (UnicodeDecodeError, OSError)` — binary and
  unreadable files are silently skipped.
- **Write** (`file_path.write_text(...)`) was NOT wrapped — if a `.md` file was
  read-only and contained placeholder tokens, `write_text()` raised
  `PermissionError` (a subclass of `OSError`), crashing project creation.

Bug reference: **BUG-052** (Minor).

---

## Fix

**File:** `src/launcher/core/project_creator.py`  
**Function:** `replace_template_placeholders()`

Wrapped the `write_text()` call in `try: ... except OSError: continue` to
silently skip read-only (or otherwise unwritable) files, matching the existing
read-guard behavior:

```python
if updated != original:
    try:
        file_path.write_text(updated, encoding="utf-8")
    except OSError:
        # Skip read-only or otherwise unwritable files (mirrors the
        # read-guard above — silently continue rather than raising).
        continue
```

No other code changes were made.

---

## Tests Written

**File:** `tests/FIX-044/test_fix044_readonly_placeholder.py`  
**6 tests in `TestReadOnlyPlaceholder`:**

| Test | Category | Description |
|------|----------|-------------|
| `test_readonly_md_with_placeholder_does_not_raise` | Regression | BUG-052 direct regression: read-only .md with placeholder must not raise |
| `test_readonly_md_with_placeholder_is_skipped` | Unit | Read-only file retains original content after skipped write |
| `test_writable_md_with_placeholder_is_replaced` | Unit | Writable .md files are still correctly processed |
| `test_readonly_md_without_placeholder_is_unaffected` | Unit | Read-only .md without placeholders: no exception, content unchanged |
| `test_mixed_tree_readonly_and_writable` | Integration | Mixed tree: writable updated, read-only silently skipped |
| `test_oserror_is_caught_not_only_permission_error` | Unit | Any OSError subclass is caught (not just PermissionError) |

---

## Test Results

### FIX-044 suite
```
6 passed in 0.31s
```

### DOC regression (DOC-001 through DOC-004)
```
101 passed in 0.99s
```

---

## Files Changed

| File | Change |
|------|--------|
| `src/launcher/core/project_creator.py` | Wrap `write_text()` in `try/except OSError: continue` |
| `tests/FIX-044/test_fix044_readonly_placeholder.py` | New — 6 regression/unit tests |
| `docs/workpackages/FIX-044/dev-log.md` | New — this file |
| `docs/workpackages/workpackages.csv` | Status → Review, Assigned To → Developer Agent |
| `docs/test-results/test-results.csv` | 2 new TST entries (TST-1837, TST-1838) |
