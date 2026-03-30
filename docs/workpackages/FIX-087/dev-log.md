# FIX-087 Dev Log — Install pytest in macOS source install CI workflow

## Overview

**WP ID:** FIX-087  
**Branch:** `FIX-087/install-pytest-macos-ci`  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-30  
**Fixes:** BUG-159

## Problem

The `.github/workflows/macos-source-test.yml` workflow fails at the "Run test suite" step because `pytest` is not installed in the venv created by `scripts/install-macos.sh`. The install script only runs `pip install .` (production dependencies), and `pytest` is a dev dependency not included in the production install.

## Fix

Added a new step **before** the "Run test suite with venv Python" step in `.github/workflows/macos-source-test.yml`:

```yaml
      - name: Install test dependencies
        run: ~/.local/share/TurbulenceSolutions/venv/bin/pip install pytest
```

**Scope:** One-line YAML addition. The `scripts/install-macos.sh` script was intentionally NOT modified — production installs should not include test dependencies.

## Files Changed

- `.github/workflows/macos-source-test.yml` — added "Install test dependencies" step
- `docs/bugs/bugs.csv` — BUG-159 status set to Closed, Fixed In WP = FIX-087
- `docs/workpackages/workpackages.csv` — FIX-087 status updated
- `tests/FIX-087/test_fix087_workflow_pytest_step.py` — new test file

## Tests Written

| Test | Description |
|------|-------------|
| `test_workflow_file_exists` | Verifies the workflow YAML file exists |
| `test_install_pytest_step_present` | Verifies a step installing pytest via venv pip is present |
| `test_install_step_before_test_step` | Verifies the pytest install step appears before the test suite step |
| `test_install_step_uses_venv_pip` | Verifies the pip command uses the venv path |
| `test_test_step_unchanged` | Verifies the original test suite step is still present |
| `test_install_macos_sh_unchanged` | Verifies install-macos.sh does NOT install pytest (prod deps only) |

All 6 tests pass.

## Implementation Notes

- No changes to `scripts/install-macos.sh` — production install must remain test-dependency-free.
- The venv path `~/.local/share/TurbulenceSolutions/venv/bin/pip` matches the path used by the existing "Run test suite" step.
- BUG-159 marked Closed with Fixed In WP = FIX-087.

---

## Iteration 2 — 2026-03-30

**Reason for return:** Tester found regression in INS-028 tests (BUG-160). The new `pip install pytest` step contains the word `pytest` in its `run` field, causing 2 INS-028 edge-case tests to match it and fail their `-x`/`--tb=short` assertions.

**Fix applied:** In `tests/INS-028/test_ins028_tester_edge_cases.py`, narrowed the condition in `test_pytest_uses_fail_fast_flag` and `test_pytest_uses_short_traceback` from `if "pytest" in run:` to `if "python -m pytest" in run:`. This makes both tests specifically target the pytest *runner* step rather than any step that mentions the word "pytest".

**Files changed:**
- `tests/INS-028/test_ins028_tester_edge_cases.py` — narrowed condition in 2 tests
- `docs/bugs/bugs.csv` — BUG-160 set to Closed, Fixed In WP = FIX-087

**Test results:** 42 tests pass (13 FIX-087 + 29 INS-028), 0 failed (TST-2315).
