# Dev Log — FIX-127: Fix upgrade parity: copilot-instructions and counter_config

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** FIX-127/upgrade-parity  
**Date Started:** 2026-04-07

---

## Relevant ADRs

- **ADR-003** (Template Manifest and Workspace Upgrade System) — Active. This WP extends the upgrade system by: (1) adding post-copy placeholder resolution for copilot-instructions.md, and (2) removing counter_config.json from the security-critical set. ADR-003 remains valid; no supersession required.

---

## Problem Statement

Two upgrade parity issues:

1. **copilot-instructions.md placeholder regression**: `workspace_upgrader.py` correctly upgrades `copilot-instructions.md` (security_critical=true). However, the template copy contains unresolved `{{PROJECT_NAME}}` and `{{WORKSPACE_NAME}}` tokens. After the upgrade, the workspace has a functional but un-personalized instructions file. Fix: after upgrade loop, detect project name from workspace folder name and call `replace_template_placeholders()`.

2. **counter_config.json is user configuration, not security-critical**: `counter_config.json` stores user-specific counter settings (enabled/threshold). Marking it `security_critical=true` means the upgrader overwrites the user's threshold back to template defaults on every upgrade. Fix: exclude it from security_critical in `generate_manifest.py`, add it to `_NEVER_TOUCH_PATTERNS` in `workspace_upgrader.py`, regenerate both MANIFESTs.

---

## Implementation Plan

### `scripts/generate_manifest.py`
- Add `counter_config.json` exclusion to `_is_security_critical()`: files matching `.github/hooks/scripts/counter_config.json` return `False` even though the prefix `.github/hooks/` is in `_SECURITY_CRITICAL_PREFIXES`.

### `src/launcher/core/workspace_upgrader.py`
- Add `".github/hooks/scripts/counter_config.json"` to `_NEVER_TOUCH_PATTERNS`.
- After the upgrade loop (and only when `not dry_run`), detect the project name from `workspace_path.name` (strip `SAE-` prefix), then call `replace_template_placeholders(workspace_path, project_name)`.

### MANIFEST.json regeneration
- Run `generate_manifest.py` for both templates after code changes.

### Tests (`tests/FIX-127/`)
- `test_fix127_upgrade_parity.py` — 4 test scenarios:
  1. After upgrade, copilot-instructions.md has resolved project name
  2. counter_config.json is not touched during upgrade
  3. counter_config.json is marked `security_critical=false` in manifest
  4. Project name detection from workspace path

---

## Files Changed

- `scripts/generate_manifest.py`
- `src/launcher/core/workspace_upgrader.py`
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json`
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json`
- `tests/FIX-127/test_fix127_upgrade_parity.py`
- `docs/workpackages/FIX-127/dev-log.md` (this file)
- `docs/workpackages/workpackages.jsonl`

---

## Implementation Summary

### `scripts/generate_manifest.py`
- Added `_NEVER_SECURITY_CRITICAL` set containing `.github/hooks/scripts/counter_config.json`.
- Updated `_is_security_critical()` to check this exclusion set BEFORE checking `_SECURITY_CRITICAL_FILES` and `_SECURITY_CRITICAL_PREFIXES`.
- Result: `counter_config.json` returns `False` from `_is_security_critical()` even though `.github/hooks/` matches a critical prefix.

### `src/launcher/core/workspace_upgrader.py`
- Added `from launcher.core.project_creator import replace_template_placeholders` import.
- Added `.github/hooks/scripts/counter_config.json` to `_NEVER_TOUCH_PATTERNS` (defense-in-depth even if manifest marks it critical).
- Added `_detect_project_name(workspace_path)` helper — strips `SAE-` prefix from the workspace folder name to derive the project name.
- Updated `upgrade_workspace()` to call `replace_template_placeholders(workspace_path, project_name)` AFTER the verification pass. This ensures: (a) the verification compares raw template hashes (before placeholder resolution changes the content), and (b) the final workspace has resolved placeholder content just like a freshly created workspace.

### MANIFEST.json regeneration
- Ran `generate_manifest.py` for both `agent-workbench` and `clean-workspace` templates.
- Both MANIFESTs now show `counter_config.json` with `"security_critical": false`.
- `copilot-instructions.md` remains `"security_critical": true` in both.

---

## Tests Written

`tests/FIX-127/test_fix127_upgrade_parity.py` — 13 unit tests in 4 classes:

| Class | Tests |
|-------|-------|
| `TestDetectProjectName` | SAE- prefix stripped; complex name; no SAE- prefix; empty suffix |
| `TestCopilotInstructionsPlaceholderResolution` | `{{PROJECT_NAME}}` resolved after upgrade; `{{WORKSPACE_NAME}}` resolved after upgrade |
| `TestCounterConfigNotTouched` | User counter_config preserved during upgrade; counter_config in _NEVER_TOUCH_PATTERNS; _is_user_content() returns True |
| `TestCounterConfigManifestClassification` | security_critical=false in agent-workbench MANIFEST; security_critical=false in clean-workspace MANIFEST; copilot-instructions.md remains True; generate_manifest._is_security_critical() returns False |

All 13 tests pass. Logged as TST-2760.

---

## Iteration 2 — Tester Feedback Resolution

**Date:** 2026-04-07  
**Tester Finding:** Blocking regression in `tests/GUI-035/test_gui035_edge_cases.py::TestManifestHashIntegrity::test_all_security_critical_files_marked`. The GUI-035 test explicitly asserted `counter_config.json` must be `security_critical=true`. FIX-127 intentionally changed it to `false` but did not update the pre-existing GUI-035 assertion.

### Fix Applied

**File:** `tests/GUI-035/test_gui035_edge_cases.py` — class `TestManifestHashIntegrity`

1. Removed `".github/hooks/scripts/counter_config.json"` from the `security_files` list in `test_all_security_critical_files_marked`.
2. Added new test method `test_counter_config_is_not_security_critical` that loads the manifest and asserts `counter_config.json` has `security_critical: False`.

### Test Results (Iteration 2)

- `tests/FIX-127/` — 16 passed (TST-2763)
- `tests/GUI-035/test_gui035_edge_cases.py::TestManifestHashIntegrity` — 4 passed (all 4 methods including new `test_counter_config_is_not_security_critical`)
- `validate_workspace.py --wp FIX-127` — clean (exit code 0)

