# Test Report — GUI-008

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 2

## Summary

GUI-008 is **complete**. All Iteration 1 failures have been resolved. The Developer
correctly added `get_display_version` to the `app.py` import and created `self.version_label`
as a `CTkLabel` placed via `place()` at the bottom-right corner. All 14 GUI-008 tests pass.
One test (`test_version_label_is_ctk_label_not_entry`) contained a mock design flaw introduced
in Iteration 1 — `isinstance()` cannot accept a `MagicMock` as its type argument — and was
fixed by the Tester to use mock identity comparison (`is not`). The implementation is correct.
No regressions. Pre-existing 11 failures (SAF-010, INS-004, INS-012) are unrelated and
unchanged.

## Acceptance Criteria Status

| AC | Requirement | Status |
|----|-------------|--------|
| AC1 | Version displayed in visible non-editable location | **PASS** — `version_label` is a `CTkLabel` placed at bottom-right via `place()` |
| AC2 | Version matches bundled application version | **PASS** — text is `f"v{get_display_version()}"` |
| AC3 | Shown on startup without user action | **PASS** — placed inside `_build_ui()` called from `__init__` |
| AC4 | Clear fallback if metadata unavailable | **PASS** — `get_display_version()` falls back to `VERSION` constant |

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_function_exists (TST-481) | Unit | PASS | Re-confirmed |
| test_returns_string (TST-482) | Unit | PASS | Re-confirmed |
| test_returns_non_empty_string (TST-483) | Unit | PASS | Re-confirmed |
| test_fallback_returns_version_constant (TST-484) | Unit | PASS | Re-confirmed |
| test_fallback_value_is_semver_like (TST-485) | Unit | PASS | Re-confirmed |
| test_version_constant_exists (TST-486) | Unit | PASS | Re-confirmed |
| test_version_constant_is_string (TST-487) | Unit | PASS | Re-confirmed |
| test_display_version_matches_version_constant_or_installed (TST-488) | Unit | PASS | Re-confirmed |
| test_exception_does_not_propagate (TST-489) | Unit | PASS | Re-confirmed |
| test_version_label_attribute_exists (TST-515) | Integration | PASS | Fixed in Iteration 2 |
| test_version_label_is_ctk_label_not_entry (TST-516) | Integration | PASS | Test mock-design fix applied by Tester; impl correct |
| test_version_label_grid_called (TST-517) | Integration | PASS | Fixed in Iteration 2 |
| test_version_label_text_contains_version (TST-518) | Integration | PASS | Fixed in Iteration 2 |
| test_version_label_get_display_version_imported (TST-519) | Integration | PASS | Fixed in Iteration 2 |
| Full regression suite — 14/14 GUI-008 + 936 total (TST-520) | Regression | PASS | 11 pre-existing failures unchanged; 0 new regressions |

**GUI-008 tests:** 14/14 pass  
**Full suite:** 924 pass, 11 fail (all pre-existing), 1 skipped

## Bugs Found

None in Iteration 2.

## Tester Test Fix

`test_version_label_is_ctk_label_not_entry` (TST-491/TST-516) originally used
`isinstance(app.version_label, _CTK_MOCK.CTkEntry)` which raises `TypeError` because
`MagicMock` is not a valid type for `isinstance()`. Fixed to use
`app.version_label is not _CTK_MOCK.CTkEntry.return_value` — a valid mock identity check
that correctly asserts the same property.

## TODOs for Developer

None.

## Verdict

**PASS — mark GUI-008 as Done.**

---

## Iteration 1 Record (archived)

**Date:** 2026-03-12 | **Verdict:** FAIL

GUI-008 was incomplete. The developer committed only half the implementation:
`get_display_version()` was added to `config.py` (correct), but the `version_label` widget
was never added to `app.py`. All four acceptance criteria failed at the GUI layer.

**Iteration 1 failures:**
- TST-490 `test_version_label_attribute_exists` — FAIL — App.version_label missing from app.py
- TST-491 `test_version_label_is_ctk_label_not_entry` — FAIL — blocked by missing attribute
- TST-492 `test_version_label_grid_called` — FAIL — blocked by missing attribute
- TST-493 `test_version_label_text_contains_version` — FAIL — blocked by missing attribute
- TST-494 `test_version_label_get_display_version_imported` — FAIL — not imported in app.py

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
