# FIX-072 Dev Log — GUI: Remove coming-soon templates from dropdown

## WP Details
- **ID:** FIX-072
- **Branch:** FIX-072/dropdown-coming-soon
- **Bug:** BUG-107 — GUI dropdown shows coming-soon templates
- **Status:** In Progress → Review

---

## Problem

`_get_template_options()` in `src/launcher/gui/app.py` appended "...coming soon"
suffixes to unready templates and included them in the dropdown. Users could see
(and attempt to select) templates they could not actually use.

## Implementation

### Files Changed

- `src/launcher/gui/app.py`

### Changes Made

1. **`_get_template_options()`** — Rewritten to filter out unready templates:
   - Only appends a display name for templates where `is_template_ready()` returns `True`.
   - Removed the `coming_soon` set accumulation and `self._coming_soon_options` side-effect.
   - Returns only ready template display names.

2. **`App.__init__()`** — Removed the `self._coming_soon_options: set[str] = set()` field
   initialiser since the field is no longer needed.

3. **`_build_ui()`** — Cleaned up references that existed to filter coming-soon entries
   away from what `_get_template_options()` already returned:
   - Removed `ready_options` local variable (no longer needed; `options` is already filtered).
   - Updated `self._current_template` assignment and dropdown `values=` argument to use
     `options` directly.

4. **`_on_template_selected()`** — Removed the coming-soon guard that reverted selection to
   the previous template (the guard is impossible to trigger now that no coming-soon entries
   exist in the dropdown).

## Tests Written

- `tests/FIX-072/test_fix072_dropdown_filter.py`
  - `test_ready_templates_included` — verifies ready templates appear in options
  - `test_unready_templates_excluded` — verifies unready templates are not in options
  - `test_no_coming_soon_suffix_in_options` — verifies "...coming soon" text is absent
  - `test_coming_soon_options_attr_removed` — verifies `_coming_soon_options` no longer exists on App
  - `test_on_template_selected_updates_current_template` — verifies normal selection works
  - `test_on_template_selected_no_revert_for_valid` — verifies all selectable items are valid
  - `test_get_template_options_returns_only_ready` — integration: mock mix of ready/unready templates

## Known Limitations / Decisions

- `_coming_soon_options` attribute removed from `App` entirely; any code referencing it
  externally would break (no such code exists in this codebase).
- If in the future there are zero ready templates, the dropdown will show `[""]` as a
  safe fallback — same behaviour as before.

---

## Iteration 2 — Fix test regressions from coming-soon removal

**Tester verdict:** FAIL — 16 existing tests in `tests/GUI-002/` and `tests/GUI-014/`
still asserted the old coming-soon behavior that was deliberately removed.

### Files Changed

- `tests/GUI-014/test_gui014_coming_soon.py`
- `tests/GUI-002/test_gui002_project_type_selection.py`

### Changes Made

**`tests/GUI-014/test_gui014_coming_soon.py`** (10 tests fixed):
- `test_coming_soon_label_appended_to_unready` → renamed to `test_unready_template_excluded_from_options`; now asserts unready templates are absent
- `test_returns_both_ready_and_coming_soon` → renamed to `test_returns_only_ready_templates`; asserts only 1 ready item returned
- `test_coming_soon_set_contains_only_unready_display_names` → removed (tried to unpack tuple from `_get_template_options()`)
- `test_default_does_not_select_coming_soon` → renamed to `test_default_does_not_select_unready_template`; removed `_coming_soon_options` reference
- `test_coming_soon_options_set_populated` → removed (`_coming_soon_options` attribute no longer exists)
- `test_revert_on_coming_soon_selection` → removed (revert guard no longer exists)
- `test_coming_soon_selection_does_not_update_current_template` → removed (all selectable options are valid)
- `test_current_template_fallback_when_all_coming_soon` → renamed to `test_current_template_is_empty_when_no_ready_templates`; asserts `_current_template == ""`
- `test_coming_soon_set_has_all_when_none_ready` → removed (`_coming_soon_options` attribute gone)
- `test_real_templates_display_names` → updated to assert only "Agent Workbench" present, "Certification Pipeline" absent

**`tests/GUI-002/test_gui002_project_type_selection.py`** (6 tests fixed):
- `test_with_two_subdirs` → updated assertion: `certification-pipeline` must NOT appear
- `test_results_preserve_order_from_list_templates` → mock `is_template_ready=True` so fake names pass through; assert order preserved
- `test_dropdown_created_with_values_from_get_template_options` → flipped assertion: "Certification Pipeline" must NOT be in dropdown values
- `test_adding_new_template_dir_changes_options` → mock `is_template_ready=True` for new "data-science" entry
- `test_dropdown_values_not_hardcoded` → mock `is_template_ready=True`; assert `["My Custom Type"]` exactly
- `test_real_templates_dir_options_contain_creative_marketing` → renamed to `test_real_templates_dir_options_do_not_contain_certification_pipeline`; flipped assertion

### Test Results

- Targeted suite (FIX-072 + GUI-002 + GUI-014): 70 passed, 0 failed
- Full regression suite: 72 pre-existing failures (unchanged), 0 new failures
