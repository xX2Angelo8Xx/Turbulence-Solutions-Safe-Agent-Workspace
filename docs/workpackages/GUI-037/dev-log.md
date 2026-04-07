# Dev Log — GUI-037: Move workspace upgrade to Settings dialog

**Status:** Review  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-07

---

## ADR Acknowledgement

**ADR-003** (Template Manifest and Workspace Upgrade System) is directly relevant.  
ADR-003 § 4 states: "The launcher GUI offers a 'Check Workspace Health' function."  
This WP moves that function from the main window into the Settings dialog — the decision to *offer* the function is unchanged; only the surface it lives on changes. No supersession required.

---

## Summary

- Removed `workspace_health_button` and `_on_check_workspace_health` from the main `App` class.
- Added a **Repair / Upgrade Workspace** section to `SettingsDialog` (rows 7–9).
- Re-ordered SettingsDialog rows: Danger Zone → rows 10–12, Close button → row 13.
- Increased dialog height from 620 → 720 to fit the new section.
- The `workspace_entry` folder browser (row 5) is now shared between Reset Agent Blocks and Repair / Upgrade sections.
- Added `_update_version_label(workspace_path)` helper that reads `.github/version` and shows version + outdated count.
- Updated `_auto_health_check()` to update the version label instead of showing a messagebox referencing the removed button.
- Added `_on_check_and_upgrade()` method that performs the full check→upgrade flow.

---

## Files Changed

- `src/launcher/gui/app.py` — main implementation

---

## Tests Written

- `tests/GUI-037/test_gui037_settings_upgrade_section.py`
  - Verifies workspace_health_button is no longer present on App
  - Verifies SettingsDialog has `_on_check_and_upgrade` method
  - Verifies SettingsDialog has `_update_version_label` method
  - Verifies `_auto_health_check` no longer references "Check Workspace Health"
  - Verifies the version label is initialized with placeholder text
  - Tests the upgrade flow logic with mocked check_workspace / upgrade_workspace

---

## Iteration 1

Initial implementation. All tests pass.
