# Test Report — GUI-001

**Tester:** Tester Agent
**Date:** 2026-03-11
**Iteration:** 1

## Summary

GUI-001 passes. The main `customtkinter` window renders correctly with all required widgets, correct layout, correct defaults, and headless test safety guard in place. 41 tests total (33 Developer + 8 Tester edge-case). Final regression suite TST-183 confirms 207/207 tests pass.

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_app_class_is_importable | Unit | Pass | TST-212 |
| test_app_has_run_method | Unit | Pass | TST-213 |
| test_app_has_browse_method | Unit | Pass | TST-214 |
| test_app_has_on_create_method | Unit | Pass | TST-215 |
| test_ctk_window_created | Unit | Pass | TST-216 |
| test_window_title_set | Unit | Pass | TST-217 |
| test_window_geometry_called | Unit | Pass | TST-218 |
| test_appearance_mode_set_to_dark | Unit | Pass | TST-219 |
| test_color_theme_set_to_blue | Unit | Pass | TST-220 |
| test_project_name_entry_created | Unit | Pass | TST-221 |
| test_destination_entry_created | Unit | Pass | TST-222 |
| test_project_type_dropdown_created | Unit | Pass | TST-223 |
| test_browse_button_created | Unit | Pass | TST-224 |
| test_create_project_button_created | Unit | Pass | TST-225 |
| test_open_in_vscode_checkbox_created | Unit | Pass | TST-226 |
| test_open_in_vscode_checkbox_text | Unit | Pass | TST-227 |
| test_project_name_entry_is_accessible_as_attribute | Unit | Pass | TST-228 |
| test_destination_entry_is_accessible_as_attribute | Unit | Pass | TST-229 |
| test_project_type_dropdown_is_accessible_as_attribute | Unit | Pass | TST-230 |
| test_browse_button_not_directly_stored | Unit | Pass | TST-231 |
| test_open_in_vscode_checkbox_is_accessible_as_attribute | Unit | Pass | TST-232 |
| test_create_button_is_accessible_as_attribute | Unit | Pass | TST-233 |
| test_browse_sets_destination_entry | Unit | Pass | TST-234 |
| test_browse_noop_on_cancel | Unit | Pass | TST-235 |
| test_browse_noop_on_none | Unit | Pass | TST-236 |
| test_browse_dialog_title | Unit | Pass | TST-237 |
| test_run_calls_mainloop | Unit | Pass | TST-238 |
| test_make_label_entry_row_returns_entry | Unit | Pass | TST-239 |
| test_make_label_entry_row_creates_label | Unit | Pass | TST-240 |
| test_make_browse_row_returns_entry | Unit | Pass | TST-241 |
| test_make_browse_row_creates_button | Unit | Pass | TST-242 |
| test_make_browse_row_wires_command | Unit | Pass | TST-243 |
| test_main_creates_app_and_calls_run | Integration | Pass | TST-244 |
| test_window_non_resizable | Unit | Pass | TST-175 — Tester edge-case |
| test_window_geometry_exact_dimensions | Unit | Pass | TST-176 — Tester edge-case; geometry must be exactly '580x340' |
| test_dropdown_default_value_is_coding | Unit | Pass | TST-177 — Tester edge-case |
| test_appearance_mode_set_before_window_creation | Unit | Pass | TST-178 — Tester edge-case; platform safety |
| test_open_in_vscode_var_default_true | Unit | Pass | TST-179 — Tester edge-case |
| test_make_label_entry_row_calls_grid_on_entry | Unit | Pass | TST-180 — Tester edge-case |
| test_make_browse_row_button_text_is_browse | Unit | Pass | TST-181 — Tester edge-case |
| test_headless_guard_skips_app_when_pytest_running | Unit | Pass | TST-182 — Tester edge-case; headless guard verified |
| Full regression suite — 207 tests (TST-183) | Regression | Pass | 207/207 pass — 158 prior + 41 GUI-001; zero regressions |

## Bugs Found
None.

## TODOs for Developer
None.

## Verdict
PASS — WP marked Done.
