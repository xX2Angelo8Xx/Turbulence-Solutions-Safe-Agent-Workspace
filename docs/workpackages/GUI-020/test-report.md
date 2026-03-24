# GUI-020 — Test Report

**WP:** Write counter config to workspace on creation  
**Branch:** `GUI-020/counter-config-write`  
**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Verdict:** ✅ PASS

---

## Summary

The implementation correctly writes `counter_config.json` into created workspaces. All acceptance criteria for AC 5 of US-038 are satisfied. 45 tests pass (28 developer + 17 tester edge cases). No regressions introduced.

---

## Code Review

### `src/launcher/core/project_creator.py`

**`write_counter_config(project_dir, counter_enabled, counter_threshold)`**
- Correct file path: `<workspace>/.github/hooks/scripts/counter_config.json`
- `mkdir(parents=True, exist_ok=True)` ensures the directory chain is created even when the template lacks `.github/hooks/scripts/` — verified by tester edge cases.
- Writes exactly two keys: `counter_enabled` (bool) and `lockout_threshold` (int). No extra keys.
- Uses `json.dumps(config_data, indent=4)` — produces valid, human-readable JSON.
- Overwrites the template's default `counter_config.json` rather than merging — correct behaviour; GUI values always win.

**`create_project()` parameter additions**
- `counter_enabled` and `counter_threshold` are keyword arguments with safe defaults (`True`, `20`). Existing callers are unaffected.
- `write_counter_config()` is called after `shutil.copytree()` — correct sequencing (template is copied first, then GUI values overwrite the template defaults).
- Path traversal protection already enforced earlier in `create_project()` via `is_relative_to`; the config write is within the already-validated workspace.

### `src/launcher/gui/app.py`

**`_on_create_project()`**
- Reads `counter_enabled_var.get()` (BooleanVar, always returns a bool).
- Calls `get_counter_threshold()` in a `try/except ValueError` block with fallback `20` — **fails closed** as required by security policy.
- Passes both values as keyword arguments to `create_project()`.

**`get_counter_threshold()`**
- Rejects non-integers with `ValueError`.
- Rejects `value <= 0` with `ValueError` — ensures threshold is always a positive integer at the GUI level.

**Security assessment:** Implementation adheres to the security-rules.md requirements. No input escapes validation. Config write is contained within the already path-validated workspace. No injection vectors identified.

---

## Test Execution

| Test ID | Test Name | Type | Result |
|---------|-----------|------|--------|
| TST-2089 | GUI-020 developer tests (28 passed) | Unit | **Pass** |
| TST-2090 | GUI-020 tester edge-case tests (17 passed) | Unit | **Pass** |

**Total: 45 tests, 0 failures.**

---

## Tester Edge Cases Added

File: `tests/GUI-020/test_gui020_tester_edge_cases.py`

| Class | Tests | Rationale |
|-------|-------|-----------|
| `TestBoundaryThresholds` | threshold=1, threshold=999999, disabled+threshold=1, default constant check | Off-by-one and boundary conditions |
| `TestJsonTypeCorrectness` | `counter_enabled` is bool not string, `lockout_threshold` is int not string, no UTF-8 BOM | Ensures types are semantically correct; SAF-036 uses `counter_config["counter_enabled"]` as a truthy value — a string "False" would incorrectly evaluate as truthy |
| `TestTemplateWithoutHooksDir` | write creates missing parent dirs, create_project writes config when no .github, disabled counter, hooks dir without existing config | Real-world robustness: templates may not always have the hooks directory pre-populated |
| `TestAppThresholdValidation` | raises for zero, raises for negative, returns int, fallback for zero, fallback for negative | Guards against edge cases where threshold slips past GUI validation |

---

## Regression Analysis

- **Full suite run:** 69 failed, 5281 passed (identical baseline failure count + 28 developer tests on this branch).
- **One extra failure vs main:** `tests/DOC-010/test_doc010_tester_edge_cases.py::TestSourceCodeUnmodified::test_src_directory_not_modified_by_wp` — this test uses `git diff HEAD~2 HEAD -- src/` to verify DOC-010 didn't touch `src/`. It fires whenever any recent commit modifies `src/`, making it inherently fragile when the test suite is run on any feature branch that touches source code. This is **not a regression introduced by GUI-020** — it is a pre-existing test design issue in DOC-010. All 68 other pre-existing failures are unchanged.
- **GUI-020 tests:** All 45 pass. No regressions.

---

## Bugs Found

None. No bugs logged.

---

## Acceptance Criteria Check (US-038, AC 5)

> AC 5: The selected counter settings are written into the workspace during project creation.

| Criterion | Status |
|-----------|--------|
| Counter threshold value from GUI is written to `counter_config.json` | ✅ Verified |
| Counter enabled flag from GUI is written to `counter_config.json` | ✅ Verified |
| Config is written after template copy (GUI values override template defaults) | ✅ Verified |
| Config format matches what SAF-036 reads (`counter_enabled`, `lockout_threshold`) | ✅ Verified |
| Existing callers of `create_project()` are unaffected (backward compatible) | ✅ Verified |

---

## Verdict

**PASS** — All tests pass, implementation is correct, secure, and complete. WP set to `Done`.
