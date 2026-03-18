# Dev Log — SAF-031: Fix VIRTUAL_ENV bypass via python -m pip and startswith collision

**WP ID:** SAF-031  
**Assigned To:** Developer Agent  
**Status:** In Progress → Review  
**Branch:** SAF-031/fix-virtualenv-bypass  
**Date:** 2026-03-18

---

## Summary

Fixes two related VIRTUAL_ENV validation vulnerabilities in `_validate_args` in `security_gate.py`.

### BUG-049 (Critical) — `python -m pip install` bypasses VIRTUAL_ENV check

**Root cause:** The VIRTUAL_ENV guard in `_validate_args` was gated on `verb in ("pip", "pip3")`. When invoked as `python -m pip install`, the verb is `python` and the guard never fired.

**Fix:** In the `-m` module handler under the `python`/`python3`/`py` branch, added a VIRTUAL_ENV check when the resolved module is `pip` or `pip3` and the subcommand is `install`. The check mirrors the existing guard for the direct `pip`/`pip3` verb path exactly.

### BUG-050 (High) — `startswith` path-component collision

**Root cause:** The previous VIRTUAL_ENV boundary check used `norm_venv.startswith(ws_root)`. A path like `c:/workspace2/.venv` would satisfy `startswith("c:/workspace")` even though `workspace2` is a different directory.

**Fix:** Changed the predicate to:
```python
norm_venv.startswith(ws_norm + "/") and norm_venv != ws_norm
```
where `ws_norm = ws_root.rstrip("/")`. This ensures the substring match terminates at a path-component boundary.

---

## Pre-existing State

Inspection of `Default-Project/.github/hooks/scripts/security_gate.py` at HEAD (commit `d900786`, SAF-030) revealed that **both fixes were already embedded in the committed code**. The `# BUG-049` and `# BUG-050` comment markers are present at lines 1240 and 1268 respectively, with the correct logic in place. Both the `Default-Project` and `templates/coding` copies are in sync.

This WP therefore focuses on:
1. Formally acknowledging the fixes via tests and documentation
2. Writing the regression test suite for `tests/SAF-031/`
3. Running the full regression suite to confirm no regressions

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | Both fixes already present (committed in prior work) |
| `templates/coding/.github/hooks/scripts/security_gate.py` | In sync with Default-Project |
| `tests/SAF-031/__init__.py` | Created |
| `tests/SAF-031/conftest.py` | Created — workspace fixture |
| `tests/SAF-031/test_saf031_virtualenv_bypass.py` | Created — 9 test cases covering both bugs |
| `docs/workpackages/SAF-031/dev-log.md` | This file |
| `docs/workpackages/workpackages.csv` | Status → Review, Assigned To → Developer Agent |
| `docs/test-results/test-results.csv` | Test run logged |

---

## Tests Written

All tests in `tests/SAF-031/test_saf031_virtualenv_bypass.py`:

| Test | Coverage |
|------|----------|
| `test_python_m_pip_install_no_venv_denied` | BUG-049: deny without VIRTUAL_ENV |
| `test_python_m_pip_install_valid_venv_allowed` | BUG-049: allow with VIRTUAL_ENV inside project |
| `test_python_m_pip_install_outside_venv_denied` | BUG-049 + BUG-050: deny with VIRTUAL_ENV outside workspace |
| `test_python_m_pip_list_allowed` | Read-only pip list: always allow regardless of VIRTUAL_ENV |
| `test_python_m_pip_show_allowed` | Read-only pip show: always allow regardless of VIRTUAL_ENV |
| `test_pip_install_no_venv_denied` | Regression: direct pip without VIRTUAL_ENV still denied |
| `test_pip_install_startswith_collision_denied` | BUG-050: c:/workspace2/.venv denied when ws_root=c:/workspace |
| `test_pip_install_valid_venv_allowed` | Direct pip with valid VIRTUAL_ENV inside project: allow |
| `test_python_m_pip_install_editable_valid_venv` | `python -m pip install -e .` with valid VIRTUAL_ENV: allow |

---

## Regression Suite Result

All tests in the regression suite passed. See `docs/test-results/test-results.csv`.
