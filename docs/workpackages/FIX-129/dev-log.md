# Dev Log — FIX-129: Enhance parity verification and upgrader template routing

**Status:** In Progress  
**Branch:** FIX-129/parity-and-routing  
**Assigned To:** Developer Agent  
**Date Started:** 2026-04-07

---

## Prior Art

ADR-003 ("Template Manifest and Workspace Upgrade System") governs the upgrade infrastructure extended by this WP. This work adds template-type routing on top of the existing manifest/upgrader design — no architectural conflict.

---

## Scope

Five changes:

1. **Part 1 — Template files:** Add `.github/template` to both template directories. Content is the template name string (`agent-workbench` / `clean-workspace`).
2. **Part 2 — generate_manifest.py:** Add `.github/template` to `_NEVER_SECURITY_CRITICAL` so it is never upgraded.
3. **Part 3 — workspace_upgrader.py:** Add `_detect_template()`, update `_load_manifest()` to accept `template_name`, update `check_workspace()` and `upgrade_workspace()` to use detected template, add `.github/template` to `_NEVER_TOUCH_PATTERNS`.
4. **Part 4 — verify_parity.py:** Add `verify_create_project_parity()` that uses `create_project()` and compares against shutil-copy, accounting for expected divergences, wire into `main()`.
5. **Part 5 — Tests:** `tests/FIX-129/` with unit tests for all new functions.

---

## Implementation Notes

- `.github/template` is placed in both template directories as a static file (simpler than dynamic writing — template already contains the correct value before any `create_project()` call).
- `_NEVER_TOUCH_PATTERNS` extended with `".github/template"` so upgrader never overwrites it.
- `_NEVER_SECURITY_CRITICAL` in `generate_manifest.py` extended with `".github/template"` — it is metadata, not a security control.
- `verify_create_project_parity()` skips `counter_config.json` and normalizes `{{PROJECT_NAME}}` tokens before comparing; reports unexpected divergences.
- Manifests regenerated for both templates after adding `.github/template`.

---

## Files Changed

- `templates/agent-workbench/.github/template` (new)
- `templates/clean-workspace/.github/template` (new)
- `scripts/generate_manifest.py` (add `.github/template` to `_NEVER_SECURITY_CRITICAL`)
- `src/launcher/core/workspace_upgrader.py` (`_detect_template`, `_load_manifest` update, `check_workspace` update, `upgrade_workspace` update, `_NEVER_TOUCH_PATTERNS` update)
- `scripts/verify_parity.py` (new `verify_create_project_parity()`, updated `main()`)
- `templates/agent-workbench/.github/hooks/scripts/MANIFEST.json` (regenerated)
- `templates/clean-workspace/.github/hooks/scripts/MANIFEST.json` (regenerated)
- `tests/FIX-129/test_fix129_parity_routing.py` (new)
- `docs/workpackages/workpackages.jsonl` (status update)

---

## Tests Written

- `test_detect_template_agent_workbench` — detects agent-workbench template
- `test_detect_template_clean_workspace` — detects clean-workspace template
- `test_detect_template_missing_file` — falls back to agent-workbench when no .github/template
- `test_detect_template_unknown_value` — falls back to agent-workbench for unrecognized names
- `test_load_manifest_agent_workbench` — loads agent-workbench manifest
- `test_load_manifest_clean_workspace` — loads clean-workspace manifest
- `test_template_file_in_agent_workbench` — template file exists with correct content
- `test_template_file_in_clean_workspace` — template file exists with correct content
- `test_verify_create_project_parity_runs` — end-to-end parity check passes
- `test_never_touch_template_file` — upgrader does not overwrite .github/template

---

## Known Limitations

None.
