# Dev Log — FIX-008

**Developer:** Developer Agent
**Date started:** 2026-03-13
**Iteration:** 1

## Objective

Add defense-in-depth to `tests/conftest.py`: (1) mock `shutil.which` for 'code'
to return None, (2) add `subprocess.Popen` sentinel that raises RuntimeError if
'code' is in args, (3) update `testing-protocol.md` with multi-layer safety
requirements and agent emergency procedures.

Goal: No test can spawn real VS Code instances even if `open_in_vscode` patches
are bypassed via module reimport.

## Implementation Summary

### Problem
`tests/conftest.py` previously only patched `open_in_vscode` at two import
bindings. A test that reimports `launcher.core.vscode` gets a fresh binding
pointing to the real `open_in_vscode` function, which calls `shutil.which("code")`
and then `subprocess.Popen` — potentially spawning 100+ VS Code windows.

FIX-006 promised `shutil.which` mock and `subprocess.Popen` guard but never
delivered them.

### Solution — Three Defense Layers

**Layer 1 (existing):** `open_in_vscode` patched at both
`launcher.core.vscode` and `launcher.gui.app` — returns False.

**Layer 2 (new — `_prevent_vscode_detection`):** `shutil.which` is wrapped
so that calls with `name="code"` return None. All other `shutil.which` calls
are forwarded to the real function unmodified.

**Layer 3 (new — `_subprocess_popen_sentinel`):** `subprocess.Popen` is
wrapped with a sentinel that raises `RuntimeError` if the first argument looks
like a VS Code executable (`"code"`, paths ending in `\code`, or strings
containing `"visual studio code"`). Non-VS-Code Popen calls pass through to
the real `subprocess.Popen`.

### FIX-006 test update

`test_subprocess_popen_is_real` in `tests/FIX-006/test_fix006_conftest_safety.py`
previously asserted that `subprocess.Popen is real_subprocess.Popen`. With the
FIX-008 sentinel wrapper in place this assertion would fail because `Popen` is
now wrapped. The test was updated to:
- Accept that `subprocess.Popen` may be a sentinel wrapper (not the raw Popen)
- Verify the sentinel allows non-VS-Code Popen calls to pass through

### testing-protocol.md update

Section 2 (autouse fixtures) updated to list all three defense layers. A new
emergency procedure rule was added describing what to do if a VS Code instance
accidentally appears during testing.

## Files Changed

- `tests/conftest.py` — Added `import shutil`, `import subprocess` (already had
  `import os`); added `_prevent_vscode_detection` and `_subprocess_popen_sentinel`
  autouse fixtures
- `tests/FIX-006/test_fix006_conftest_safety.py` — Updated
  `test_subprocess_popen_is_real` to accept FIX-008 sentinel wrapper
- `docs/work-rules/testing-protocol.md` — Updated rule 2 bullet list to include
  all three layers; added emergency procedure rule between rules 2 and 3
- `docs/workpackages/workpackages.csv` — Added FIX-008 row
- `tests/FIX-008/__init__.py` — Created empty init for test package
- `tests/FIX-008/test_fix008_multilayer_guard.py` — Six tests verifying all
  three defense layers

## Tests Written

- `test_shutil_which_code_returns_none` — Verifies `shutil.which("code")` returns None
- `test_shutil_which_other_commands_work` — Verifies `shutil.which("python")` still works (or at minimum does not return None for a non-code command)
- `test_popen_sentinel_blocks_vscode` — Verifies `subprocess.Popen(["code", "/tmp"])` raises RuntimeError
- `test_popen_sentinel_allows_other_commands` — Verifies non-VS-Code Popen calls are not blocked
- `test_find_vscode_returns_none` — Verifies `find_vscode()` returns None during tests
- `test_all_three_layers_present` — Verifies all three autouse fixtures are registered in conftest

## Known Limitations

- The `subprocess.Popen` sentinel checks the first element of `args` for string
  `"code"` (case-insensitive). A VS Code binary named differently (e.g. `code-insiders`)
  or launched via a full path not ending in `\code` could theoretically slip through.
  The Layer 1 and Layer 2 guards make this extremely unlikely in practice.
- The string form of `args` check uses a split on whitespace; edge cases with
  unusual quoting are not handled (Layer 1 and 2 would catch them first anyway).

---

## Iteration 2

**Date:** 2026-03-13
**Triggered by:** Tester feedback — BUG-033 (code-insiders not blocked)

### Problem (from test-report.md)

The Layer 3 sentinel and Layer 2 shutil.which guard only checked for `"code"`.
`subprocess.Popen(["code-insiders", ...])` and `subprocess.Popen("code-insiders ...")`
passed through the sentinel without raising RuntimeError. On a machine with VS Code
Insiders installed, this would spawn the IDE.

### Fix

1. Added module-level `_VSCODE_CMDS = frozenset({"code", "code-insiders"})` to
   `tests/conftest.py` so both variants are defined in one place.

2. `_prevent_vscode_detection` (`_guarded_which`): changed `name == "code"` to
   `name in _VSCODE_CMDS` — now `shutil.which("code-insiders")` also returns None.

3. `_subprocess_popen_sentinel` (`_guarded_popen`):
   - List-args branch: replaced `cmd == "code"` with `cmd in _VSCODE_CMDS`; also
     added `cmd.endswith(os.sep + "code-insiders")` to catch absolute paths.
   - String-args branch: replaced `first == "code"` with `first in _VSCODE_CMDS`.

### Tests

All 11 FIX-008 tests pass (including the 2 previously-failing Tester edge-case tests):
- `test_popen_sentinel_blocks_code_insiders` — PASS (was FAIL)
- `test_popen_sentinel_blocks_code_insiders_string_form` — PASS (was FAIL)

Full regression: 1567 passed / 2 skipped / 0 failed.

### Test Results Logged

- TST-619: test_popen_sentinel_blocks_code_insiders — Pass
- TST-620: test_popen_sentinel_blocks_code_insiders_string_form — Pass
- TST-621: FIX-008 full suite + regression — Pass (1567 passed / 2 skipped)

### Files Changed

- `tests/conftest.py` — Added `_VSCODE_CMDS` frozenset; updated `_guarded_which`
  and `_guarded_popen` to block `"code-insiders"` alongside `"code"`
