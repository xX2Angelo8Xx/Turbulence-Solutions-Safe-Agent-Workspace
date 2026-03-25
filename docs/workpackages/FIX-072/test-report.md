# Test Report — FIX-072

**Tester:** Tester Agent (GitHub Copilot)
**Date:** 2026-03-25
**Iteration:** 1

## Summary

The core implementation is correct: `_get_template_options()` now filters out unready templates,
`_coming_soon_options` is removed, and `_on_template_selected()` no longer has a coming-soon
revert guard. All 17 FIX-072-specific tests pass.

**However**, the Developer did not update 16 existing tests in `tests/GUI-002/` and `tests/GUI-014/`
that were written for the old coming-soon behavior. These tests now fail, violating the
"all existing tests must pass" requirement. **This WP cannot be marked Done until those tests
are fixed.**

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-072 targeted suite (17 tests) | Unit | PASS | All developer + tester edge-case tests pass |
| Full regression suite (tests/) | Regression | FAIL | 88 failures total; 16 caused by FIX-072 (GUI-002 + GUI-014); remainder are pre-existing |
| GUI-002 + GUI-014 suite | Regression | FAIL | 16 tests broken by FIX-072 implementation; see TODOs |

## Tester Edge-Case Tests Added

File: `tests/FIX-072/test_fix072_edge_cases.py` (8 tests, all PASS)

| Test | Purpose |
|------|---------|
| `test_duplicate_template_names_preserved_in_order` | Duplicate names from `list_templates` pass through unchanged |
| `test_on_template_selected_with_empty_string` | Empty string sets `_current_template` to `""` without crash |
| `test_get_template_options_propagates_is_ready_exception` | `RuntimeError` in `is_template_ready` propagates |
| `test_get_template_options_propagates_list_templates_exception` | `OSError` from `list_templates` propagates |
| `test_get_template_options_preserves_ready_order` | Template order from `list_templates` is preserved |
| `test_single_ready_template_returned_as_single_element_list` | Single ready template returns singleton list |
| `test_large_template_list_only_ready_returned` | Large mixed list filtered to only ready subset |
| `test_no_coming_soon_options_class_attribute` | `App` class has no `_coming_soon_options` class attribute |

## Bugs Found

None (implementation logic is correct; issues are test hygiene only).

## TODOs for Developer

- [ ] **Update `tests/GUI-014/test_gui014_coming_soon.py`** — The following tests in
  `TestGetTemplateOptions` assert the old coming-soon behavior that FIX-072 deliberately
  removed. They must be updated or removed to reflect the new filter-only behavior:
  - `test_coming_soon_label_appended_to_unready` — remove or replace with assertion that
    unready templates are **absent** from the list
  - `test_returns_both_ready_and_coming_soon` — update: only ready templates should appear
  - `test_coming_soon_set_contains_only_unready_display_names` — remove: `_coming_soon_options`
    no longer exists and `_get_template_options()` no longer returns a tuple
  - `test_default_does_not_select_coming_soon` — update to assert first ready template is default
  - `test_coming_soon_options_set_populated` — remove: `_coming_soon_options` attribute gone
  - `test_revert_on_coming_soon_selection` — remove: revert guard no longer exists
  - `test_coming_soon_selection_does_not_update_current_template` — remove: all selectable
    templates are valid; any selection updates `_current_template`
  - `test_current_template_fallback_when_all_coming_soon` — update: when all templates are
    unready, `options` is empty and `_current_template` is `""` (not the first template)
  - `test_coming_soon_set_has_all_when_none_ready` — remove: `_coming_soon_options` gone
  - `test_real_templates_display_names` — update: real templates dir should only show ready
    templates (i.e., only `Agent Workbench`); `Certification Pipeline ...coming soon` must
    **not** appear

- [ ] **Update `tests/GUI-002/test_gui002_project_type_selection.py`** — The following tests
  assume unready templates are shown with a suffix, which is no longer true. Update them to
  reflect that unready templates are filtered out entirely:
  - `TestGetTemplateOptions::test_with_two_subdirs` — `certification-pipeline` is unready
    so it must NOT appear at all; update assertion to `assert "Certification Pipeline" not in result`
  - `TestGetTemplateOptions::test_results_preserve_order_from_list_templates` — comment
    says fake names get coming-soon suffix; now they are simply absent; update assertion to
    check the order of **absent** names (i.e., result is `[]` since none are ready), or
    mock `is_template_ready` to return `True` for those names
  - `TestDropdownDynamicLoading::test_dropdown_created_with_values_from_get_template_options`
    — assertion `assert any("Certification Pipeline" in v for v in values_arg)` should become
    `assert not any("Certification Pipeline" in v for v in values_arg)` since it's unready
  - `TestDropdownDynamicLoading::test_adding_new_template_dir_changes_options` — `data-science`
    name is not a real directory so `is_template_ready` returns False; mock `is_template_ready`
    to return True for the new name, or use an existing real name
  - `TestDropdownDynamicLoading::test_dropdown_values_not_hardcoded` — `my-custom-type` is
    not real so it is now filtered out entirely; mock `is_template_ready` to return True and
    assert `["My Custom Type"]` is returned
  - `TestTemplateDirPresence::test_real_templates_dir_options_contain_creative_marketing`
    — `certification-pipeline` is not ready (only README.md); update assertion to verify it
    is **absent** from the options list

## Verdict

**FAIL — Return to Developer.**

The implementation is correct and BUG-107 is fixed. However, 16 pre-existing tests in
`tests/GUI-002/` and `tests/GUI-014/` now fail because the Developer did not update them to
reflect the removal of the coming-soon behavior. Per the testing protocol, **all existing
tests must pass** before a WP can be marked Done. Please address all TODOs above and resubmit
for review.
