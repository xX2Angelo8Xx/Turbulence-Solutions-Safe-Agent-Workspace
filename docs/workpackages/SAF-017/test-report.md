# Test Report — SAF-017: Expand Terminal Allowlist — Python and pip Commands

## Verdict: **PASS** ✓ *(Iteration 2)*

**Tester:** Tester Agent  
**Date:** 2026-03-16  
**Branch:** `SAF-017/python-pip-commands`

---

## Iteration 2 Summary (Re-test — 2026-03-16)

Both BUG-049 and BUG-050 have been fixed correctly. All 74 SAF-017 tests pass, including the 4 previously failing edge cases. No regressions were introduced. WP is approved for Done.

---

## Iteration 1 Summary

The Developer correctly implemented requirements 1–3 and partially implemented requirements 4–5. Two security vulnerabilities were found that allow global `pip install` to proceed without an active virtual environment, directly contradicting requirements 4 and 5.

---

## Requirements Verification

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | `python -c` allowed (P-01 removed, `-c` out of `denied_flags`) | ✅ PASS | All 11 developer tests pass |
| 2 | `python -m venv <path>` path-checked; outside project → deny | ✅ PASS | All 10 developer tests pass |
| 3 | `pip list/show/freeze/check` allowed without path restrictions | ✅ PASS | All 12 developer tests pass |
| 4 | `pip install` allowed when `VIRTUAL_ENV` inside workspace | ✅ PASS | All 6 developer tests pass |
| 5 | `pip install` denied when no venv active or venv outside project | ✅ PASS | **Fixed in Iteration 2** — BUG-049 + BUG-050 resolved |

---

## Test Run Results

### Iteration 2 (Re-test after BUG-049 + BUG-050 fixes)

| Run | Scope | Outcome |
|-----|-------|---------|
| SAF-017 full suite `tests/SAF-017/` (74 tests) | 74 tests | **74 PASS** (TST-1383) |
| Full regression `tests/` | 2594 pass, 29 skip, 1 fail | Fail is pre-existing INS-005 (TST-1384) |

All 4 previously failing edge-case tests now pass:
- `test_python_m_pip_install_no_venv_should_be_denied` ✅
- `test_python3_m_pip_install_no_venv_should_be_denied` ✅
- `test_python_m_pip_install_venv_outside_should_be_denied` ✅
- `test_pip_install_venv_path_with_prefix_collision_denied` ✅

### Iteration 1 (Initial review)

| Run | Scope | Outcome |
|-----|-------|---------|
| Developer suite `tests/SAF-017/test_saf017_python_pip_commands.py` | 52 tests | All 52 PASS |
| Full regression `tests/` | 2572 pass, 29 skip, 1 fail | Fail is pre-existing INS-005 (documented in dev-log) |
| Tester edge-case suite `tests/SAF-017/test_saf017_edge_cases.py` | 22 tests | **4 FAIL**, 18 pass |

---

## Failures Found

> **Iteration 2 status: Both bugs fixed and verified. See below for the original Iteration 1 findings.**

### BUG-049 — ✅ FIXED: `python -m pip install` skips VIRTUAL_ENV check

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`  
**Function:** `_validate_args`  
**Severity:** Critical  

**Root cause:**  
The VIRTUAL_ENV guard in `_validate_args` gates on `verb in ("pip", "pip3")`. When pip is invoked as `python -m pip install`, the verb is `python`, so the guard is never reached. The `pip` module passes the `_PYTHON_ALLOWED_MODULES` check, and the path arguments (`install`, `requests`, etc.) are not path-like so zone-checking is a no-op. The command returns `("allow", None)` even with no `VIRTUAL_ENV` set.

**Reproducer:**
```python
# Remove VIRTUAL_ENV from environment, then:
sanitize_terminal_command("python -m pip install requests", "/workspace")
# Returns: ("allow", None)  ← should be ("deny", ...)
```

**Failing tests:**
- `test_python_m_pip_install_no_venv_should_be_denied`
- `test_python3_m_pip_install_no_venv_should_be_denied`
- `test_python_m_pip_install_venv_outside_should_be_denied`

**Fix required:**  
In `_validate_args`, inside the Python `-m` module handler, add a VIRTUAL_ENV check when the module is `pip` or `pip3`. Specifically, after identifying that `module in ("pip", "pip3")`, apply the same `VIRTUAL_ENV` check that exists for direct `pip`/`pip3` verbs — check that the subcommand (next non-flag arg after the module) is `install`, and if so, validate `VIRTUAL_ENV` is set and points inside the workspace.

```python
# Inside the "if module in _PYTHON_ALLOWED_MODULES" block, after the venv check:
if module in ("pip", "pip3"):
    # Apply the same install guard as direct pip/pip3 verb
    remaining_args = args[i + 2:]  # args after the module name
    pip_subcmd = next(
        (a.lower() for a in remaining_args if not a.startswith("-")),
        None,
    )
    if pip_subcmd == "install":
        virtual_env = os.environ.get("VIRTUAL_ENV", "")
        if not virtual_env:
            return False
        norm_venv = normalize_path(virtual_env)
        if not norm_venv.startswith(ws_root + "/") and norm_venv != ws_root:
            return False
```

---

### BUG-050 — ✅ FIXED: VIRTUAL_ENV startswith check has path-component prefix-collision

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`  
**Function:** `_validate_args`  
**Severity:** High  

**Root cause:**  
The VIRTUAL_ENV check uses a raw Python string `startswith`:
```python
norm_venv = normalize_path(virtual_env)
if not norm_venv.startswith(ws_root):
```
Python string `startswith` does not respect path-component boundaries. If `ws_root = "c:/workspace"`, then `VIRTUAL_ENV = "c:/workspace2/.venv"` satisfies `norm_venv.startswith("c:/workspace")` (returns True) even though `c:/workspace2` is a completely different directory — not inside `c:/workspace`.

**Reproducer:**
```python
WS = "c:/workspace"
# VIRTUAL_ENV = "c:/workspace2/.venv" — clearly outside WS
sanitize_terminal_command("pip install requests", WS)
# with VIRTUAL_ENV = "c:/workspace2/.venv"  ← shared string prefix with WS
# Returns: ("allow", None)  ← should be ("deny", ...)
```

**Failing test:** `test_pip_install_venv_path_with_prefix_collision_denied`

**Fix required:**  
Change the check to verify path-component boundary:
```python
ws_with_sep = ws_root.rstrip("/") + "/"
if not (norm_venv == ws_root.rstrip("/") or norm_venv.startswith(ws_with_sep)):
    return False
```
This also affects BUG-049's fix — use the same boundary-safe check there.

---

## Design Decisions Verified

The following intentional behaviors were confirmed by tester tests:

| Behavior | Verdict |
|----------|---------|
| `python -c "import os"` — inline code allowed, no audit of content | Intentional, documented in dev-log |
| `eval` / `exec` in inline code triggers obfuscation patterns P-20/P-21 → deny | Correct security-conservative behavior |
| `ipython -c` still blocked by P-08 | Correct (P-01 removed, P-08 retained) |
| `pip3.11 install` normalized to `pip3`, venv check applies | Correct |
| Mixed-case `PIP list` → normalized, allowed | Correct |
| `VIRTUAL_ENV = ws_root` (no `.venv` subdir) → allowed | Known design limitation — acceptable per WP scope |

---

## Pre-existing Failure (out of scope)

`tests/INS-005/test_ins005_edge_cases.py::TestShortcutsAndUninstaller::test_uninstall_delete_type_is_filesandirs` — pre-existing failure on `main`, documented in dev-log. Searching for `Type: filesandirs` but template uses `Type: filesandordirs`. Not introduced by SAF-017.

---

## Iteration 2 — Fix Verification

| Item | Status |
|------|--------|
| BUG-049: `python -m pip install` without venv denied | ✅ Verified — 3 tests confirm deny behaviour |
| BUG-050: Path-boundary safe check (`ws_norm + "/"`) | ✅ Verified — prefix-collision test passes |
| Fix applied to `Default-Project/.github/hooks/scripts/security_gate.py` | ✅ Confirmed in code review |
| Fix applied to `templates/coding/.github/hooks/scripts/security_gate.py` | ✅ Confirmed in code review |
| `_KNOWN_GOOD_GATE_HASH` updated via `update_hashes.py` | ✅ Noted in dev-log |
| All 74 SAF-017 tests pass (52 dev + 22 tester) | ✅ 74/74 PASS |
| No new regressions in full suite | ✅ 2594 pass, 1 pre-existing INS-005 failure |

---

## Iteration 1 — TODOs for Developer *(Completed)*

~~1. **[BLOCKER] Fix BUG-049**~~ ✅ Done  
~~2. **[BLOCKER] Fix BUG-050**~~ ✅ Done  
~~3. **Re-run full test suite**~~ ✅ Done  
~~4. **Update `_KNOWN_GOOD_GATE_HASH`**~~ ✅ Done  
~~5. **Keep tester edge-case tests**~~ ✅ All 22 pass

---

_Initial report (Iteration 1 FAIL): Tester Agent — 2026-03-16_  
_Iteration 2 re-test (PASS): Tester Agent — 2026-03-16_
