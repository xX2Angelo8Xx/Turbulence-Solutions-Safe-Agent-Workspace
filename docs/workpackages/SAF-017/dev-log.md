# Dev Log — SAF-017: Expand Terminal Allowlist — Python and pip Commands

## Status
Review

## Assigned To
Developer Agent

## Date
2026-03-16

---

## Summary

Updated `security_gate.py` in both `Default-Project/.github/hooks/scripts/` and `templates/coding/.github/hooks/scripts/` to expand the terminal allowlist for Python and pip commands per the five acceptance criteria in the workpackage.

---

## Requirements Implemented

| # | Requirement | Implementation |
|---|-------------|----------------|
| 1 | `python -c "..."` allowed when cwd is inside project folder | Removed `-c` from `denied_flags` for `python`, `python3`, and `py` rules; removed P-01 obfuscation pattern (`python -c`) from `_EXPLICIT_DENY_PATTERNS`; inline code argument skipped from zone-check |
| 2 | `python -m venv <path>` allowed when target path is inside the project folder; denied outside | Added `"venv"` to `_APPROVED_MODULES`; added zone-check logic in the `-m` handler branch to validate the venv target path |
| 3 | `pip list`, `pip show`, `pip freeze`, `pip check` allowed without path restrictions | These subcommands were added to (or already present in) the `allowed_subcommands` frozenset for `pip` and `pip3` rules |
| 4 | `pip install` allowed when `VIRTUAL_ENV` is active and points inside the workspace | Added VIRTUAL_ENV check in the pip subcommand handler: reads `os.environ.get("VIRTUAL_ENV", "")` and calls `_check_path_arg` to verify it is inside the workspace |
| 5 | `pip install` denied when no venv is active or venv points outside the project | Returns `("deny", ...)` when `VIRTUAL_ENV` is empty or its path fails the zone check |

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | All 5 requirement changes (see above) |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Synced copy of same changes |
| `docs/workpackages/workpackages.csv` | SAF-017 status → `In Progress` → `Review` |
| `docs/test-results/test-results.csv` | Test run logged |

---

## Tests Written

- **Location:** `tests/SAF-017/test_saf017_python_pip_commands.py`
- **Count:** 52 tests
- **Coverage:**
  - `python -c`, `python3 -c`, `py -c` allowed inside workspace
  - `python -c` denied at obfuscation-pattern level (ipython -c still blocked)
  - `python -m venv` path allowed inside / denied outside workspace
  - `pip list`, `pip show`, `pip freeze`, `pip check` allowed unconditionally
  - `pip install` with active VIRTUAL_ENV inside workspace → allow
  - `pip install` with VIRTUAL_ENV outside workspace → deny
  - `pip install` with no VIRTUAL_ENV set → deny
  - `pip uninstall`, `pip download`, `pip config` behaviour unchanged

---

## Test Conflicts Resolved

SAF-017 intentionally changed behavior tested by two earlier WPs. Five affected tests were updated to reflect the new expected behavior (assertions updated, comments revised with SAF-017 attribution):

| Test File | Test Function | Old Assertion | New Assertion |
|-----------|--------------|---------------|---------------|
| `tests/SAF-005/test_saf005_terminal_sanitization.py` | `test_allowlist_pip_install` | `is_ask(...)` ("allow") | `is_deny(...)` |
| `tests/SAF-005/test_saf005_terminal_sanitization.py` | `test_bypass_python_c_extra_spaces` | `is_deny(...)` | `is_ask(...)` ("allow") |
| `tests/SAF-005/test_saf005_terminal_sanitization.py` | `test_bypass_case_variation` | `is_deny(...)` | `is_ask(...)` ("allow") |
| `tests/SAF-005/test_saf005_edge_cases.py` | `test_bypass_tab_injection_python_c_blocked` | `is_deny(...)` | `is_ask(...)` ("allow") |
| `tests/SAF-013/test_saf013_edge_cases.py` | `test_terminal_obfuscation_python_c_returns_deny` | `assert result == "deny"` | `assert result == "allow"` |

**Pre-existing Failure (not caused by SAF-017):** `tests/INS-005/test_ins005_edge_cases.py::test_uninstall_delete_type_is_filesandirs` — this test was already failing on `main` before this branch was created. It searches for `Type: filesandirs` but the template uses `Type: filesandordirs`. Out of scope for this WP.

---

---

## Iteration 2 — Bug Fixes (2026-03-16)

### Summary
Fixed two security vulnerabilities reported by the Tester (BUG-049, BUG-050).

### BUG-049 — Fix: `python -m pip install` bypasses VIRTUAL_ENV check
**Root cause:** The VIRTUAL_ENV guard in `_validate_args` only fired when `verb in ("pip", "pip3")`. Invoking pip as `python -m pip install` set `verb = "python"`, skipping the guard entirely.

**Fix:** Inside the `-m` module handler (section 4 of `_validate_args`), added a check: when `module in ("pip", "pip3")`, extract the pip subcommand from `args[i + 2:]` and apply the same `install` → VIRTUAL_ENV validation as the direct `pip`/`pip3` verb path.

### BUG-050 — Fix: VIRTUAL_ENV `startswith(ws_root)` path-boundary collision
**Root cause:** `"c:/workspace2/.venv".startswith("c:/workspace")` returns `True` in Python — a directory that merely shares a string prefix passes the check even though it is not inside the workspace.

**Fix:** Replaced `norm_venv.startswith(ws_root)` with `norm_venv.startswith(ws_norm + "/") and norm_venv != ws_norm` (where `ws_norm = ws_root.rstrip("/")`) in both the direct `pip`/`pip3` verb path and the new `python -m pip` path.

### Files Changed
| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | BUG-049 + BUG-050 fixes; re-ran update_hashes.py |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Synced same fixes; re-ran update_hashes.py |

### Test Results
| Suite | Result |
|-------|--------|
| `tests/SAF-017/test_saf017_edge_cases.py` (22 tests) | 22 PASS |
| `tests/SAF-017/` (74 tests total) | 74 PASS |
| Full suite | 2594 pass, 29 skip, 1 fail (INS-005 pre-existing) |

---

## Known Limitations

- The `python -c` inline code argument is intentionally not zone-checked (it is a code string, not a path). Malicious code within the string is the responsibility of the outer AI safety layer.
- `pip install` check relies solely on the `VIRTUAL_ENV` environment variable. Scenarios where the variable is set but the venv is corrupted are out of scope for this WP.
