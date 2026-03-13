# Test Report — FIX-008: Conftest Multi-Layer VS Code Guard

**Tester:** Tester Agent  
**Date:** 2026-03-13  
**Iteration:** 1  
**Verdict:** ❌ FAIL — Return to Developer

---

## Overview

FIX-008 adds defense-in-depth to `tests/conftest.py` via two new autouse
fixtures (Layers 2 and 3) to prevent VS Code from spawning during tests even
if the existing Layer 1 `open_in_vscode` patches are bypassed through module
reimport.  The implementation was reviewed against the WP description, dev-log,
and the three-layer safety model documented in `docs/work-rules/testing-protocol.md`.

---

## Code Review Findings

### Positive Findings

| Item | Finding |
|------|---------|
| Layer 1 | Correctly preserved. `open_in_vscode` patched at both `launcher.core.vscode` and `launcher.gui.app`. |
| Layer 2 (`_prevent_vscode_detection`) | Wraps `shutil.which` at the `shutil` module level. Guard correctly targets only `name == "code"` and forwards all other names to the real function. |
| Layer 3 (`_subprocess_popen_sentinel`) | Captures `_real_popen = subprocess.Popen` before patching, then wraps. Non-VS-Code list and string args pass through to real Popen unmodified. |
| FIX-006 test update | `test_subprocess_popen_is_real` correctly updated to assert RuntimeError for code launch instead of asserting raw identity. |
| testing-protocol.md | All three layers documented clearly. Emergency VS Code procedure (Rule 2.5) is accurate and actionable. |
| `find_vscode()` scope | `vscode.py:find_vscode()` only calls `shutil.which("code")` — Layer 2 correctly targets the exact lookup the production code makes. |

### Identified Gap — BUG-033

**Severity:** Medium  
**Component:** `tests/conftest.py` — `_subprocess_popen_sentinel`

The Layer 3 sentinel intercepts these patterns:

```python
cmd == "code"
cmd.endswith(os.sep + "code")
"visual studio code" in cmd
```

It does **not** intercept:
- `["code-insiders", ...]` — VS Code Insiders binary (list form)
- `"code-insiders /path"` — VS Code Insiders binary (string form)
- Paths ending in `\code-insiders` (Windows) or `/code-insiders` (Unix)

**Reproduction:** `subprocess.Popen(["code-insiders", "/tmp"])` passes through
the sentinel with no RuntimeError and reaches the real `subprocess.Popen`.  On
this machine `code-insiders` is not installed so a `FileNotFoundError` results.
On a machine where VS Code Insiders is installed, the IDE window would spawn.

See **BUG-033** in `docs/bugs/bugs.csv`.

---

## Test Run Results

| TST-ID | Test | Result |
|--------|------|--------|
| TST-612 | Full regression baseline (1563 tests, Tester pre-review) | ✅ Pass |
| TST-613 | FIX-008 developer test suite — 7 tests | ✅ Pass |
| TST-614 | `test_popen_sentinel_blocks_code_insiders` (Tester edge-case) | ❌ Fail |
| TST-615 | `test_popen_sentinel_blocks_code_insiders_string_form` (Tester edge-case) | ❌ Fail |
| TST-616 | `test_layer3_works_independently_of_layers_1_and_2` (Tester edge-case) | ✅ Pass |
| TST-617 | `test_popen_allows_python_subprocess` (Tester edge-case) | ✅ Pass |
| TST-618 | FIX-008 tester edge-case suite combined (5 new tests, 2 fail) | ❌ Fail |

All developer-submitted tests (TST-604 through TST-611) continue to pass.  
Total failing tests after Tester additions: **2** (both related to BUG-033).

---

## Edge-Case Analysis

### Attack Vectors Considered

| Vector | Status |
|--------|--------|
| `open_in_vscode` reimport bypass → `subprocess.Popen(["code", …])` | ✅ Blocked by Layer 3 |
| `shutil.which("code")` returns real path (Layer 2 bypassed) | ✅ Layer 3 catches Popen |
| `subprocess.Popen(["code", …])` direct call | ✅ RuntimeError raised |
| `subprocess.Popen("code /path")` string form | ✅ RuntimeError raised |
| Path ending in `\code` on Windows | ✅ Blocked by `endswith` check |
| `subprocess.Popen(["code-insiders", …])` | ❌ **Not blocked — BUG-033** |
| `subprocess.Popen("code-insiders /path")` string form | ❌ **Not blocked — BUG-033** |
| Non-VS-Code commands (`["echo", …]`, `["python", …]`) | ✅ Pass through correctly |
| `shutil.which("python")` selectivity | ✅ Not intercepted |
| Multiple fixtures active simultaneously | ✅ All three autouse fixtures confirmed present |
| Module reload causes fresh `find_vscode()` binding | ✅ Level 2 patch is at shutil module level; survives reload |

### Boundary Conditions

- **Empty Popen args list:** `isinstance([], (list, tuple)) and []` evaluates to `False` — passes through silently. Low risk since empty Popen args would fail at OS level anyway.
- **Popen with `None` args:** Falls through to real Popen and fails at OS level. No guard needed.
- **`shutil.which("")`:** The sentinel checks `name == "code"` so an empty string passes through to real `shutil.which`. Acceptable.

---

## Verdict: ❌ FAIL

**Reason:** Tester edge-case test `test_popen_sentinel_blocks_code_insiders` and
`test_popen_sentinel_blocks_code_insiders_string_form` both fail.  The Layer 3
sentinel does not intercept VS Code Insiders (`code-insiders`) in either list or
string invocation form.

---

## Developer TODOs for Iteration 2

### TODO-1 — Extend Layer 3 sentinel to block `code-insiders` (BLOCKING)

**File:** `tests/conftest.py`  
**Fixture:** `_subprocess_popen_sentinel` → `_guarded_popen`

Update the list-args check from:
```python
if cmd == "code" or cmd.endswith(os.sep + "code") or "visual studio code" in cmd:
```
to also cover `code-insiders` and any future VS Code variant.  Recommended approach:

```python
_VSCODE_CMDS = frozenset({"code", "code-insiders"})
if (
    cmd in _VSCODE_CMDS
    or any(cmd.endswith(os.sep + exe) for exe in _VSCODE_CMDS)
    or "visual studio code" in cmd
):
```

Update the string-args check from:
```python
if first == "code":
```
to:
```python
if first in _VSCODE_CMDS:
```

The `_VSCODE_CMDS` frozenset should be defined at function scope (inside
`_guarded_popen`) or at fixture scope.

### TODO-2 — Verify the two Tester edge-case tests pass after the fix (BLOCKING)

After applying TODO-1:
1. Run `tests/FIX-008/test_fix008_multilayer_guard.py::test_popen_sentinel_blocks_code_insiders`
2. Run `tests/FIX-008/test_fix008_multilayer_guard.py::test_popen_sentinel_blocks_code_insiders_string_form`
3. Both must raise `RuntimeError` with `SAFETY VIOLATION`.

### TODO-3 — Run full regression suite after fix (BLOCKING)

Confirm `1563 passed, 2 skipped, 0 failed` (or better) before re-handing off.

---

## Re-handoff Checklist

When re-submitting for Tester review:
- [ ] `tests/conftest.py` updated per TODO-1
- [ ] `tests/FIX-008/test_fix008_multilayer_guard.py` — Tester edge-case tests pass (all 11)
- [ ] Full regression suite green
- [ ] `dev-log.md` updated with Iteration 2 changes
- [ ] `docs/workpackages/workpackages.csv` status set to `Review`
