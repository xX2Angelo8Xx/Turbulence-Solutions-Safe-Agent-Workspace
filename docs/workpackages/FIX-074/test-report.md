# Test Report — FIX-074

**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Verdict:** PASS

---

## WP Summary

FIX-074 removes the "Coding" project type from the launcher dropdown and replaces it with a non-selectable "Certification Pipeline — Coming Soon..." entry. Only "Agent Workbench" remains selectable. The fix is implemented in `src/launcher/gui/app.py` via:

1. Module-level constant `_COMING_SOON_LABEL`
2. `_get_template_options()` excludes `certification-pipeline` from selectable names
3. `_on_template_selected()` reverts to the previous valid template on coming-soon selection
4. `_on_create_project()` shows an info dialog and returns early when coming-soon is selected

---

## Code Review

**Files changed:** `src/launcher/gui/app.py`, `tests/FIX-074/`, `docs/bugs/bugs.csv`, `docs/test-results/test-results.csv`, `docs/workpackages/FIX-074/dev-log.md`, `docs/workpackages/workpackages.csv`

### Implementation correctness
- `_COMING_SOON_LABEL = "Certification Pipeline — Coming Soon..."` — clear, unambiguous constant.
- `_get_template_options()` filter `name != "certification-pipeline"` correctly separates selectable display names from the disabled label. The label is appended separately in `_build_ui()` via `configure(values=options + [_COMING_SOON_LABEL])`, keeping `_get_template_options()` clean for FIX-072 compatibility. ✓
- `_on_template_selected()` guard uses a strict equality check against the constant; no regex or string matching footguns. ✓
- `_on_create_project()` guard is the first check, before name/destination validation — correct ordering prevents creating a project with the label as the template name under any combination of inputs. ✓
- No new widget (CTkComboBox) was introduced — consistent with existing UI style. Decision is well-justified in dev-log. ✓

### Known limitation acknowledged
The `_get_template_options` filter only excludes `certification-pipeline` by directory name. If a `coding/` directory were added and marked ready, it would appear as selectable. This is documented in `dev-log.md` and covered by a dedicated edge-case test (`test_coding_template_would_appear_if_directory_existed_and_was_ready`).

### Security review
- `_COMING_SOON_LABEL` contains no path separators, HTML tags, or shell metacharacters (verified by test). ✓
- The string comparison `display_template == _COMING_SOON_LABEL` uses identity with a module constant — no injection surface. ✓
- Guard in `_on_create_project()` fires before any filesystem or create operation. ✓

---

## Test Execution

### Developer's test suite (19 tests)
| File | Tests | Result |
|------|-------|--------|
| `tests/FIX-074/test_fix074_project_type_dropdown.py` | 19 | ✅ All pass |

### Tester edge-case additions (11 tests)
| File | Tests | Result |
|------|-------|--------|
| `tests/FIX-074/test_fix074_edge_cases.py` | 11 | ✅ All pass |

**Total FIX-074 tests: 30 — all pass**

### FIX-072 regression (17 tests)
All 17 FIX-072 tests pass. The `_get_template_options()` contract change is backward-compatible: the method still returns only selectable display names with no coming-soon suffix. ✓

### Full regression suite
- **6788 passed, 73 failed** (full suite including 30 new FIX-074 tests)
- The 73 failures are **pre-existing** and unrelated to FIX-074. Verified by running the same failing tests on `main` — identical failure set. FIX-074 changed only `src/launcher/gui/app.py` and test/tracking files; no test that was passing on `main` now fails.
- Logged as TST-2214 (full suite Regression) and TST-2215 (FIX-074 Unit).

---

## Edge Cases Tested (Tester additions)

| Test | Purpose |
|------|---------|
| `test_coming_soon_is_last_with_three_templates` | Coming-soon always last even with multiple templates |
| `test_coming_soon_appears_exactly_once` | No duplicate coming-soon entries |
| `test_coding_template_would_appear_if_directory_existed_and_was_ready` | Documents known limitation re: coding filter |
| `test_coming_soon_guard_fires_even_with_empty_project_name` | Guard ordering: comes before name validation |
| `test_coming_soon_guard_fires_even_with_empty_destination` | Guard ordering: comes before destination validation |
| `test_revert_to_empty_string_when_current_template_not_set` | Revert logic is safe with falsy _current_template |
| `test_revert_uses_current_template_at_time_of_call` | Revert uses correct template snapshot |
| `test_label_has_no_path_traversal` | Security: no path separators or `../` patterns |
| `test_label_has_no_html_or_script_tags` | Security: no HTML injection characters |
| `test_label_has_no_shell_metacharacters` | Security: no shell injection characters |
| `test_coming_soon_guard_idempotent_across_multiple_calls` | Guard fires reliably on repeated calls |

---

## Acceptance Criteria Verification

| AC | Criteria | Status |
|----|----------|--------|
| AC1 | Dropdown shows Agent Workbench (selectable) | ✅ Pass |
| AC2 | Certification Pipeline — Coming Soon... appears in dropdown | ✅ Pass |
| AC3 | Coming-soon entry is non-selectable (reverts on click) | ✅ Pass |
| AC4 | No Coding option in dropdown | ✅ Pass — BUG-116 regression test confirms |
| AC5 | Create Project rejects coming-soon selection | ✅ Pass |

---

## Bugs Found

None. No new bugs introduced by this WP.

---

## Verdict

**PASS** — All acceptance criteria met. 30 tests pass (19 Developer + 11 Tester). FIX-072 regression clean. BUG-116 → Closed.
