# Test Report — FIX-092: Hide terminal flash when opening VS Code

**Tester:** Tester Agent  
**Date:** 2026-03-31  
**Verdict:** PASS  

---

## Summary

FIX-092 adds `creationflags=subprocess.CREATE_NO_WINDOW` on `win32` to three
subprocess call sites:

| File | Function | Call type |
|------|----------|-----------|
| `src/launcher/core/vscode.py` | `open_in_vscode()` | `subprocess.Popen` |
| `src/launcher/core/github_auth.py` | `get_github_token()` | `subprocess.run` |
| `src/launcher/core/updater.py` | `_get_local_git_version()` | `subprocess.run` |
| `src/launcher/core/updater.py` | `check_for_update_source()` | `subprocess.run` (git fetch) |

---

## Tests Executed

### Developer tests — `tests/FIX-092/test_fix092_terminal_flash.py`

| Test | Result |
|------|--------|
| `TestOpenInVscode::test_win32_uses_create_no_window` | PASS |
| `TestOpenInVscode::test_non_win32_no_creationflags` | PASS |
| `TestOpenInVscode::test_correct_popen_args` | PASS |
| `TestOpenInVscode::test_returns_true_on_success` | PASS |
| `TestOpenInVscode::test_returns_false_when_not_found` | PASS |
| `TestGithubAuthCreationFlag::test_win32_uses_create_no_window` | PASS |
| `TestGithubAuthCreationFlag::test_non_win32_no_creationflags` | PASS |
| `TestUpdaterCreationFlag::test_git_describe_win32_creationflag` | PASS |
| `TestUpdaterCreationFlag::test_git_fetch_win32_creationflag` | PASS |

**9 / 9 passed**

### Tester edge-case tests — `tests/FIX-092/test_fix092_edge_cases.py`

| Test | Result |
|------|--------|
| `TestCreateNoWindowValue::test_exact_hex_value` | PASS |
| `TestOpenInVscodeEdgeCases::test_darwin_no_creationflags` | PASS |
| `TestOpenInVscodeEdgeCases::test_win32_path_string_conversion` | PASS |
| `TestOpenInVscodeEdgeCases::test_popen_not_called_when_vscode_missing` | PASS |
| `TestGithubAuthEdgeCases::test_capture_output_always_present` | PASS |
| `TestGithubAuthEdgeCases::test_darwin_no_creationflags` | PASS |
| `TestGithubAuthEdgeCases::test_correct_gh_command` | PASS |
| `TestUpdaterEdgeCases::test_git_describe_non_win32_no_creationflags` | PASS |
| `TestUpdaterEdgeCases::test_git_describe_capture_output_present` | PASS |
| `TestUpdaterEdgeCases::test_git_describe_correct_args` | PASS |
| `TestUpdaterEdgeCases::test_git_fetch_non_win32_no_creationflags` | PASS |
| `TestUpdaterEdgeCases::test_git_fetch_capture_output_always_present` | PASS |
| `TestUpdaterEdgeCases::test_git_fetch_correct_args` | PASS |
| `TestUpdaterEdgeCases::test_darwin_git_fetch_no_creationflags` | PASS |

**14 / 14 passed**

### Module regression — `tests/FIX-092/ + tests/SAF-035/ + tests/SAF-036/`

**109 / 109 passed** — no regressions in the changed modules or dependent test suites.

---

## Test Results Logged

| ID | Name | Status |
|----|------|--------|
| TST-2374 | FIX-092: Developer tests (9 passed) | Pass |
| TST-2375 | FIX-092: Tester edge-case tests (14 passed) | Pass |
| TST-2376 | FIX-092: Full module regression (109 passed) | Pass |

---

## Code Review

### vscode.py
- `if sys.platform == "win32"` guard is correct — `creationflags` is not set on
  Linux/macOS.
- `shell=False` is preserved (security requirement met).
- Kwargs dict pattern is clean and idiomatic; no style issues.

### github_auth.py
- `capture_output=True` is still present — stdio redirection preserved.
- Flag is in a `kwargs` dict, applied cleanly via `**kwargs` to `subprocess.run`.
- `timeout=3` is still present.
- Environment variable sources are checked first; subprocess is only called as
  fallback — no change to logic.

### updater.py
- Both `_get_local_git_version` and `check_for_update_source` follow identical
  kwargs pattern.
- `capture_output=True` confirmed still present in both calls.
- `shell=False` (implicit default) preserved throughout.

---

## Edge Cases Analysed

| Area | Finding |
|------|---------|
| `CREATE_NO_WINDOW` exact value | Confirmed `0x08000000` — matches Win32 API |
| macOS (darwin) | No `creationflags` set — correct |
| Linux | No `creationflags` set — correct |
| Path → str conversion | `str(workspace_path)` called before Popen — correct |
| `Popen` not called when VS Code missing | Short-circuit on `find_vscode() is None` — correct |
| `capture_output` retention | Present on all three `subprocess.run` sites on all platforms |
| `git fetch` args | `["git", "fetch", "--tags", "--quiet"]` — unchanged |
| `git describe` args | `["git", "describe", "--tags", "--abbrev=0"]` — unchanged |
| Race conditions | Not applicable — flag only affects window visibility, not process lifetime |
| Security (injection) | `shell=False` everywhere; list args used throughout — no injection risk |

---

## Known Pre-existing Failures

The full test suite (`tests/`) has ~469 pre-existing failures across DOC-*, FIX-*,
and template tests. These are entirely unrelated to FIX-092, were present before
this branch, and were not introduced by this change. No new failures were added.

---

## Verdict

**PASS** — Implementation is correct, cross-platform safe, minimal in scope, and
all 23 tests (9 developer + 14 tester) pass clean.
