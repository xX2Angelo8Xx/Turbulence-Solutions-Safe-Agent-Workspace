# Dev Log — FIX-094: Fix CI tkinter import failure

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** FIX-094/ci-tkinter-fix  
**Date Started:** 2026-04-03  

---

## Problem Statement

`tests/conftest.py` imports `tkinter.filedialog` and `tkinter.messagebox` at
module top-level (lines 14–15). On Ubuntu and macOS CI runners using
`actions/setup-python`, the installed Python build does **not** include
tkinter, causing an `ImportError` at pytest collection time (exit code 2).

A prior fix attempt added `apt-get install python3-tk` to `.github/workflows/`
but that installs tkinter for the **system Python**, not for the `actions/setup-python`
Python in the venv, so pytest still fails to collect.

## ADR Check

No ADRs are directly related to test-infrastructure or tkinter mocking. ADR-002
("Mandatory CI Test Gate Before Release Builds") is relevant in spirit — this
WP unblocks that gate. Acknowledged.

## Implementation Plan

1. Wrap the tkinter imports in `tests/conftest.py` in a `try/except ImportError`
   block, mimicking the `customtkinter` mock pattern already at line 22.
2. Remove the non-working `apt-get install python3-tk` and macOS tkinter
   diagnostic steps from all three CI workflow files.
3. Write regression tests in `tests/FIX-094/` that verify conftest.py loads
   even when tkinter is absent (by simulating the mock path).

## Changes Made

### `tests/conftest.py`
- Replaced bare `import tkinter.filedialog` / `import tkinter.messagebox`
  with a `try/except ImportError` block.
- When tkinter is unavailable, `MagicMock` objects are registered in
  `sys.modules` so all downstream `patch.object` calls on `tkinter.messagebox`
  and `tkinter.filedialog` continue to work (MagicMock allows arbitrary
  attribute access and assignment).

### `.github/workflows/release.yml`
- Removed "Install system dependencies (Linux)" step (apt-get python3-tk).
- Removed "Install system dependencies (macOS)" step (tkinter diagnostic).

### `.github/workflows/test.yml`
- Removed "Install system dependencies (Linux)" step (apt-get python3-tk).

### `.github/workflows/staging-test.yml`
- Removed "Install system dependencies (Linux)" step (apt-get python3-tk).

## Tests Written

- `tests/FIX-094/test_fix094_tkinter_fallback.py`
  - Verifies that importing conftest (or the mock pattern) does not raise even
    when tkinter is mocked away from sys.modules.
  - Verifies that `_HAS_TK` is set correctly depending on tkinter availability.
  - Verifies that `tkinter.messagebox` and `tkinter.filedialog` in sys.modules
    are accessible after the mock fallback.

## Test Results

All tests passed — see test-results.csv entry logged via `add_test_result.py`.

## Known Limitations

None. The fix is minimal and targeted.
