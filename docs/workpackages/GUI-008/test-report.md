# Test Report — GUI-008

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 1

## Summary

GUI-008 is **incomplete**. The developer committed only half the implementation:
`get_display_version()` was added to `config.py` (correct and working), but the
`version_label` widget was never added to `app.py`. As a result, **all four
acceptance criteria fail at the GUI layer**. Additionally, neither a `dev-log.md`
nor any test files were submitted by the developer — both are mandatory before
advancing to `Review`.

## Acceptance Criteria Status

| AC | Requirement | Status |
|----|-------------|--------|
| AC1 | Version displayed in visible non-editable location | **FAIL** — `version_label` absent from `app.py` |
| AC2 | Version matches bundled application version | **FAIL** — `get_display_version` never called in `app.py` |
| AC3 | Shown on startup without user action | **FAIL** — no label placed in `_build_ui()` |
| AC4 | Clear fallback if metadata unavailable | **PASS** — `get_display_version()` falls back to `VERSION` constant |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_function_exists | Unit | PASS | `get_display_version` callable in config.py |
| test_returns_string | Unit | PASS | Return type is str |
| test_returns_non_empty_string | Unit | PASS | Non-empty return value |
| test_fallback_returns_version_constant | Unit | PASS | PackageNotFoundError → VERSION |
| test_fallback_value_is_semver_like | Unit | PASS | VERSION matches `\d+\.\d+\.\d+` |
| test_version_constant_exists | Unit | PASS | `config.VERSION` present |
| test_version_constant_is_string | Unit | PASS | `config.VERSION` is str |
| test_display_version_matches_version_constant_or_installed | Unit | PASS | Result is either installed or VERSION |
| test_exception_does_not_propagate | Unit | PASS | AC4 — never raises |
| test_version_label_attribute_exists | Unit | **FAIL** | `App.version_label` missing from `app.py` |
| test_version_label_is_ctk_label_not_entry | Unit | **FAIL** | Blocked by missing attribute |
| test_version_label_grid_called | Unit | **FAIL** | Blocked by missing attribute |
| test_version_label_text_contains_version | Unit | **FAIL** | Blocked by missing attribute |
| test_version_label_get_display_version_imported | Unit | **FAIL** | `get_display_version` not imported in `app.py` |
| Full regression suite (913 tests) | Regression | PASS | 11 pre-existing failures unrelated to GUI-008; no new regressions introduced |

**GUI-008 tests:** 9 pass / 5 fail  
**Full suite:** 913 pass, 16 fail (11 pre-existing + 5 GUI-008)

## Bugs Found

- BUG-026: `version_label` never added to `app.py` — AC1/AC2/AC3 unimplemented (logged in `docs/bugs/bugs.csv`)

## Protocol Violations

- **No `dev-log.md`** in `docs/workpackages/GUI-008/` — mandatory per agent-workflow.md.
- **No developer test files** submitted — workpackage must not advance to `Review` without passing tests.
- **workpackages.csv comment** claims "Implementation complete … version_label added to app.py. Tests in tests/GUI-008/" — all three claims are false.

## TODOs for Developer

- [ ] In `src/launcher/gui/app.py` — add `from launcher.config import get_display_version` to the import line (alongside `APP_NAME`, `COLOR_PRIMARY`, etc.)
- [ ] In `src/launcher/gui/app.py` — add a `CTkLabel` widget `self.version_label` in `_build_ui()` displaying `f"v{get_display_version()}"`. Place it in a clearly visible, non-editable position (e.g. `row=7` below the Create button, or in the window title bar / status row).
- [ ] Call `self.version_label.grid(...)` to place the label in the layout at startup.
- [ ] Create `docs/workpackages/GUI-008/dev-log.md` (see agent-workflow.md for required format).
- [ ] All 5 failing `TestVersionLabel` tests in `tests/GUI-008/test_gui008_version_display.py` must pass before re-submitting.

## Verdict

**FAIL — return to Developer.** Set GUI-008 back to `In Progress`.
