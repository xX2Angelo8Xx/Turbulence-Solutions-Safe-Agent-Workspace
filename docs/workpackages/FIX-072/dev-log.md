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
