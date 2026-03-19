# Test Report — GUI-011

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 2

## Summary

All 29 tests pass (23 developer-written + 6 tester edge-case). Developer iteration 2 correctly persisted all color changes to disk. The three constants (`COLOR_PRIMARY=#0A1D4E`, `COLOR_SECONDARY=#5BC5F2`, `COLOR_TEXT=#FFFFFF`) are present in `config.py`. The window background is set to `COLOR_PRIMARY`. All interactive widgets (dropdown, checkbox, Create Project button, Browse button) use `fg_color=COLOR_SECONDARY` and `text_color=COLOR_TEXT`. All labels and entries in the reusable component builders use `text_color=COLOR_TEXT`. Error labels correctly retain `text_color="red"` (not a brand colour).

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-277 — GUI-011 developer test suite iteration 1 (23 tests) | Unit | Fail | Iteration 1: source not saved to disk — 0/23 pass |
| TST-278 — Full regression suite (excl. GUI-011, SAF-006) | Regression | Pass | No regressions caused by unchanged source |
| TST-283 — GUI-011 developer test suite iteration 2 (23 tests) | Unit | Pass | All 23/23 pass after developer fix |
| TST-284 — GUI-011 tester edge-case tests (6 tests) | Unit | Pass | All 6/6 pass |

### Edge-Case Tests Added (TestEdgeCasesGui011)

| Test | What It Validates |
|------|-------------------|
| `test_color_primary_hex_format` | `#0A1D4E` starts with `#`, is 7 chars, decodes as valid hex |
| `test_color_secondary_hex_format` | `#5BC5F2` starts with `#`, is 7 chars, decodes as valid hex |
| `test_color_text_hex_format` | `#FFFFFF` starts with `#`, is 7 chars, decodes as valid hex |
| `test_window_is_non_resizable` | `resizable(False, False)` is called on the window |
| `test_window_title_is_app_name` | Window title is set to `APP_NAME` constant |
| `test_error_labels_use_red_not_brand_color` | At least 2 error labels use `"red"`, not a brand colour |

## Bugs Found

None (Iteration 1 bug BUG-017 is resolved in Iteration 2).

## TODOs for Developer

None.

## Verdict

**PASS — mark WP as Done.**

