# FIX-074 Dev Log — Replace Coding project type with disabled Certification Pipeline Coming Soon

## Status
Review

## Assigned To
Developer Agent

## Summary
Fix the Project Type dropdown in the launcher GUI:
- Remove the "Coding" project type option
- Add "Certification Pipeline — Coming Soon..." as a disabled/greyed-out entry
- Ensure only "Agent Workbench" is selectable

Related bugs: BUG-116

## Approach

`CTkOptionMenu` does not natively support disabled items. The chosen approach:

1. Add a module-level constant `_COMING_SOON_LABEL` in `app.py` for the disabled label string.
2. Change `_get_template_options()` to always exclude `certification-pipeline` from selectable options and always append `_COMING_SOON_LABEL` at the end.
3. Guard `_on_template_selected()` to revert to the previous valid template when the coming-soon label is selected.
4. Guard `_on_create_project()` to reject (with an info dialog) any attempt to create a project using the coming-soon label.

This approach avoids introducing a new widget (CTkComboBox) and remains consistent with the existing UI style. The revert-on-select pattern gives a visual indication that the item is not selectable.

## Files Changed
- `src/launcher/gui/app.py` — added `_COMING_SOON_LABEL`, updated `_get_template_options`, `_on_template_selected`, `_on_create_project`
- `tests/FIX-074/__init__.py` — test package marker
- `tests/FIX-074/test_fix074_project_type_dropdown.py` — unit + regression tests

## Tests Written
- `test_coming_soon_not_selectable_via_callback` — verifies `_on_template_selected` reverts on coming-soon selection
- `test_coming_soon_in_options` — verifies `_get_template_options` always includes the coming-soon label
- `test_coding_not_in_options` — verifies "Coding" never appears in options
- `test_agent_workbench_in_options` — verifies "Agent Workbench" is always in options
- `test_create_project_rejects_coming_soon` — verifies `_on_create_project` rejects the coming-soon label
- `test_agent_workbench_is_default` — verifies initial selection is "Agent Workbench"
- `test_current_template_unchanged_on_coming_soon_select` — verifies `_current_template` state is preserved
- `test_valid_template_selection_accepted` — verifies "Agent Workbench" selection is accepted normally
- `test_coming_soon_label_constant` — verifies the constant value contains expected text
- `test_certification_pipeline_not_selectable` — verifies certification-pipeline dir is excluded from selectable list

## Known Limitations
- If a real `coding/` template directory is added to `templates/`, it would appear. The filtering explicitly excludes only `certification-pipeline`; a `coding/` directory would need explicit exclusion too. However, per the codebase state at implementation time, no `coding/` directory exists.
- The revert-on-select pattern may cause a brief visual flash in the dropdown before reverting to Agent Workbench.
