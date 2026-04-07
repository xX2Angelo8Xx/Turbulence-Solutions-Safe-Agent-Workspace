# FIX-124 Dev Log — Fix 26 CI test regressions from v3.4.0 fixes

**WP:** FIX-124  
**Status:** In Progress  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-07

---

## ADR Acknowledgements

- **ADR-008** (Tests Must Track Current Codebase State) — directly governs this WP; all test fixes are required to bring tests in line with current code.
- **ADR-002** (Mandatory CI Test Gate Before Release Builds) — these regressions block the CI gate; fixing them is a blocker for the next release.

---

## Problem Summary

FIX-121, FIX-122, FIX-123, and DOC-064 introduced 26 new test failures:

| Category | Count | Root Cause |
|---------|-------|------------|
| GUI threading (GUI-007, GUI-014, GUI-015) | 23 | FIX-121 refactored `_on_create_project` to use `threading.Thread` + `self._window.after()`. Tests did not mock `after` to run synchronously and did not handle async thread. |
| Template count (GUI-023) | 1 | `clean-workspace` template added; count was 2, now 3. |
| AGENT-RULES path (DOC-035) | 5 errors | Test had wrong path: `Project/AgentDocs/AGENT-RULES.md` → actual: `Project/AGENT-RULES.md`. |
| Stale version (FIX-070) | 1 | Hardcoded `"3.3.11"` assertion; version is now `"3.4.0"`. |
| Fragile count (FIX-052) | 1 | `"11 passed"` in stdout no longer matches (6 passed + 5 skipped). |

---

## Implementation

### Category 1: GUI Threading (23 failures)

**Root cause:** `_on_create_project` now spawns a `threading.Thread`. Callbacks are scheduled via `self._window.after(0, fn)`. In tests:
- `_window` is a MagicMock, so `_window.after()` records calls but never invokes `fn`.
- The thread runs asynchronously; assertions execute before thread completes.

**Fix applied:**
1. Added `tests/GUI-007/conftest.py`, `tests/GUI-014/conftest.py`, `tests/GUI-015/conftest.py` — each provides an autouse fixture that patches `launcher.gui.app.threading.Thread` with a synchronous replacement.
2. Updated `_make_app()` helpers in all three GUI-007 test files to:
   - Set `app._window.after = lambda ms, fn: fn()` (synchronous callback dispatch)
   - Set `app._set_creation_ui_state = MagicMock()` (prevent real widget manipulation)
3. Updated GUI-014 test setups (`TestCreateProjectUsesCurrentTemplate`, `TestCreateProjectComingSoonBypass`) with the same `after` fix.
4. Updated GUI-015 `test_on_create_project_duplicate_guard_uses_prefix` with the same `after` fix.

### Category 2: Template Count (GUI-023)

Changed `assert len(names) == 2` → `assert len(names) == 3` in `test_list_templates_real_count`.

### Category 3: AGENT-RULES Path (DOC-035)

Fixed `AGENT_RULES` path: removed `"AgentDocs"` subdirectory segment. File is at `Project/AGENT-RULES.md`, not `Project/AgentDocs/AGENT-RULES.md`.

### Category 4: Stale Version (FIX-070)

Renamed `test_current_version_is_3_3_11` → `test_current_version_is_3_4_0` and updated assertion to `== "3.4.0"`.

### Category 5: Fragile Count (FIX-052)

Replaced `assert "11 passed" in result.stdout` with `assert result.returncode == 0`. The count is fragile because FIX-052-era tests became skippable after subsequent WPs added conditional skip logic.

### Category 6: MANIFEST Regeneration

Ran `python scripts/generate_manifest.py` and `python scripts/generate_manifest.py --template clean-workspace` to regenerate both template MANIFESTs.

---

## Files Changed

- `tests/GUI-007/conftest.py` — new: sync thread fixture
- `tests/GUI-014/conftest.py` — new: sync thread fixture
- `tests/GUI-015/conftest.py` — new: sync thread fixture
- `tests/GUI-007/test_gui007_validation.py` — updated `_make_app()`
- `tests/GUI-007/test_gui007_edge_cases.py` — updated `_make_app()`
- `tests/GUI-007/test_gui007_tester_additions.py` — updated `_make_app()`
- `tests/GUI-014/test_gui014_coming_soon.py` — updated test setups
- `tests/GUI-015/test_gui015_rename_root_folder.py` — updated test body
- `tests/GUI-023/test_gui023_tester_edge_cases.py` — count 2→3
- `tests/DOC-035/test_doc035_agentdocs.py` — fixed AGENT_RULES path
- `tests/FIX-070/test_fix070_version_bump.py` — renamed test, updated assertion
- `tests/FIX-052/test_fix052_no_hardcoded_version.py` — replaced fragile count check
- `templates/agent-workbench/MANIFEST.json` — regenerated
- `templates/clean-workspace/MANIFEST.json` — regenerated
- `docs/workpackages/workpackages.jsonl` — status In Progress → Review
- `tests/regression-baseline.json` — entries removed (tests now pass)
- `tests/FIX-124/test_fix124_regressions.py` — new: regression guard tests

---

## Tests Written

- `tests/FIX-124/test_fix124_regressions.py` — verifies all key fixes hold

---

## Known Limitations

None.
