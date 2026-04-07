# Test Report — FIX-127: Fix upgrade parity: copilot-instructions and counter_config

**Tester:** Tester Agent  
**Date:** 2026-04-07  
**Verdict (Iteration 1):** FAIL — TST-2761  
**Verdict (Iteration 2):** PASS — TST-2764, TST-2765  
**Final Verdict:** PASS

---

## Iteration 2 Summary (2026-04-07)

The blocking issue from Iteration 1 has been fully resolved. The Developer:
1. Removed `counter_config.json` from the `security_files` list in `test_all_security_critical_files_marked`
2. Added `test_counter_config_is_not_security_critical` which asserts `security_critical=false`

**Full test suite (FIX-127 branch vs main):**
- main: 250 failed, 9220 passed, 353 skipped, 91 errors
- FIX-127: 250 failed, 9220 passed, 353 skipped, 91 errors
- **Identical counts — no new regressions introduced by FIX-127**

**Targeted suite (tests/FIX-127/ + tests/GUI-035/):**
- 79 passed, 2 failed (pycache pollution — pre-existing on main)
- `test_all_security_critical_files_marked` → **PASS** (was FAIL in Iteration 1)
- `test_counter_config_is_not_security_critical` → **PASS** (new test)
- All 16 FIX-127 tests → **PASS**
- `validate_workspace.py --wp FIX-127` → **clean (exit code 0)**

---

## Iteration 1 Summary

FIX-127's core implementation is correct and well-tested. All 16 FIX-127-specific tests pass. However, the Developer introduced a **regression in `tests/GUI-035/test_gui035_edge_cases.py`** by changing `counter_config.json` from `security_critical=true` to `security_critical=false` in the MANIFEST without updating the pre-existing GUI-035 assertion that explicitly expects it to remain `security_critical=true`.

**Blocking issue (now resolved):** `tests/GUI-035/test_gui035_edge_cases.py::TestManifestHashIntegrity::test_all_security_critical_files_marked` — was FAIL, now PASS

---

## Verification Results

### Requirements Checked

| Requirement | Status | Evidence |
|-------------|--------|---------|
| copilot-instructions.md resolved after upgrade (no `{{PROJECT_NAME}}`) | PASS | `TestCopilotInstructionsPlaceholderResolution` (2 tests) |
| copilot-instructions.md remains `security_critical: true` | PASS | agent-workbench MANIFEST confirmed; `test_copilot_instructions_still_security_critical_agent_workbench` passes |
| counter_config.json NOT touched during upgrade | PASS | `test_counter_config_preserved_during_upgrade`; user threshold survives |
| counter_config.json in `_NEVER_TOUCH_PATTERNS` | PASS | `test_counter_config_in_never_touch_patterns` passes |
| counter_config.json `security_critical: false` in agent-workbench MANIFEST | PASS | Verified directly in MANIFEST.json |
| counter_config.json `security_critical: false` in clean-workspace MANIFEST | PASS | Verified directly in MANIFEST.json |
| `_detect_project_name` strips SAE- prefix | PASS | 4 tests cover SAE-prefix, complex names, no-prefix, empty-suffix |
| generate_manifest._is_security_critical() returns False for counter_config | PASS | `test_generate_manifest_excludes_counter_config_from_critical` passes |

### Tests Run

| Test Suite | Tests | Outcome |
|------------|-------|---------|
| `tests/FIX-127/` (Developer) | 13 | ALL PASS |
| `tests/FIX-127/` (Tester additions) | 3 | ALL PASS |
| `tests/GUI-035/test_gui035_edge_cases.py` | 1 (relevant) | **FAIL** |

### The Regression

**File:** `tests/GUI-035/test_gui035_edge_cases.py`  
**Test:** `TestManifestHashIntegrity::test_all_security_critical_files_marked`  
**Error:**
```
AssertionError: .github/hooks/scripts/counter_config.json must be marked security_critical=true in MANIFEST.json
assert False is True
```

**Root cause:** The GUI-035 test was written to assert that `counter_config.json` is `security_critical=true`. FIX-127 intentionally changes this to `false`, but the Developer did not update the GUI-035 test accordingly.

**Was this test passing on main before FIX-127?** Yes. `git diff main~2 main -- src/` is empty, confirming FIX-126 did not touch src/. The GUI-035 test was passing on main with `counter_config.json` as `security_critical=true`.

### Other Failures Investigated

| Test | Category | Verdict |
|------|----------|---------|
| `DOC-010::test_src_directory_not_modified_by_wp` | Pre-existing test design fragility (uses `git diff HEAD~2 HEAD`; always fails when any branch modifies src/) | NOT caused by FIX-127 logic, but triggered by it |
| `GUI-035::test_no_pycache_directories` | Runtime test pollution (pycache from test runner importing security_gate.py) | Not from FIX-127; clears after `rm -rf __pycache__` |
| `GUI-035::test_no_pyc_files` | Same as above | Not from FIX-127 |
| SAF-073, SAF-074, INS-012, GUI-009, SAF-077 (appeared as new in full run) | Test isolation failures — all pass when run individually | Not regressions |

---

## Edge Cases Tested (Tester Additions)

1. **`test_dry_run_skips_placeholder_resolution`** — Confirms `upgrade_workspace(dry_run=True)` does NOT resolve placeholders. `{{PROJECT_NAME}}` must remain in file after dry run. PASS.

2. **`test_placeholder_resolution_oserror_adds_to_errors`** — Confirms that if `replace_template_placeholders` raises `OSError` (e.g., disk full), the error is captured in `report.errors` rather than propagating as an uncaught exception. PASS.

3. **`test_non_sae_workspace_upgrade_resolves_full_folder_name`** — Confirms that for workspaces not named `SAE-xxx`, the full folder name is used as the project name (no SAE prefix stripping). `{{PROJECT_NAME}}` → folder name, `{{WORKSPACE_NAME}}` → `SAE-{folder_name}`. Note: the workspace_name will be `SAE-MyCustomWorkspace` even if the folder is just `MyCustomWorkspace`. This is acceptable per the dev-log design. PASS.

---

## Security Review

- **copilot-instructions.md security_critical=true**: CONFIRMED. This is the first layer of agent defense. Not weakened.
- **counter_config.json security_critical=false**: Design-correct change. counter_config.json is user configuration (lockout threshold, enabled flag), not security enforcement code. Overwriting user thresholds on every upgrade violated user expectations.
- **`_NEVER_TOUCH_PATTERNS`**: Defense-in-depth addition is correct. Even if a manifest is tampered, the upgrader will never overwrite counter_config.json.
- **`replace_template_placeholders` call sequence**: Runs after the verification pass so the hash check compares raw template content. This ordering is correct.
- **Import cycle risk**: `workspace_upgrader.py` imports `project_creator.replace_template_placeholders`. Verified: no circular import (`project_creator` does not import `workspace_upgrader`).

---

## ADR Conflict Check

Checked `docs/decisions/index.jsonl` via dev-log reference. Dev-log acknowledges ADR-003 (Template Manifest and Workspace Upgrade System) is Active and remains so. No supersession needed or triggered by this WP.

---

## TODOs for Developer (MANDATORY before re-handoff)

### TODO-1 (Blocking): Update `tests/GUI-035/test_gui035_edge_cases.py`

In `TestManifestHashIntegrity::test_all_security_critical_files_marked`, the list `security_files` includes `counter_config.json`. This must be removed:

```python
# REMOVE this line from the security_files list:
".github/hooks/scripts/counter_config.json",
```

After removing it, add a separate assertion that explicitly confirms `counter_config.json` is NOT security_critical (to document the intentional design decision):

```python
def test_counter_config_is_not_security_critical(self):
    """counter_config.json stores user settings — must NOT be security_critical (FIX-127)."""
    manifest = self._load_manifest()
    entry = manifest["files"].get(".github/hooks/scripts/counter_config.json")
    assert entry is not None
    assert entry.get("security_critical") is False, (
        "counter_config.json must be security_critical=false — it stores user settings "
        "that must survive workspace upgrades (see FIX-127)"
    )
```

### TODO-2 (Recommended): Add regression baseline entry for DOC-010 git-test

The DOC-010 test `test_src_directory_not_modified_by_wp` uses `git diff HEAD~2 HEAD -- src/` and will fail on any branch that modifies src/. This is a pre-existing test design fragility. While not caused by this WP, the Developer should add this to the baseline or file a separate FIX for the DOC-010 test design:

```json
"tests.DOC-010.test_doc010_tester_edge_cases.TestSourceCodeUnmodified.test_src_directory_not_modified_by_wp": {
  "reason": "Git-based test uses HEAD~2 HEAD; fails on any branch that modifies src/. Pre-existing test design fragility unrelated to WP logic."
}
```

### TODO-3 (After fixing): Re-run and confirm clean

1. Run `tests/GUI-035/` — ALL must pass (including the updated test)
2. Run `tests/FIX-127/` — ALL 16 must still pass
3. Run `scripts/validate_workspace.py --wp FIX-127` — must exit 0
4. Commit and push the updated test

---

## Verdict

**FAIL — WP returned to In Progress.**

The implementation is correct and the fix logic is sound. The single blocking issue is the missing GUI-035 test update. This is a small, well-scoped fix. Once the Developer updates `tests/GUI-035/test_gui035_edge_cases.py` per TODO-1 and confirms all tests pass, this WP should receive a PASS on re-review.
