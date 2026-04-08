# DOC-067 — Test Report

**WP:** DOC-067  
**Name:** Agent-workbench template doc gaps for v3.4.0  
**Branch:** DOC-067/agent-workbench-doc-gaps  
**Tester:** Tester Agent  
**Date:** 2026-04-08  
**Verdict:** ❌ FAIL — Return to Developer

---

## Summary

DOC-067's own 6 tests all pass. However, the README.md change introduced **6 new regression failures** in existing test suites (`FIX-086` and `DOC-002`) that are **not in the regression baseline**. The WP cannot be marked Done until these regressions are resolved.

---

## Test Results

### DOC-067 Own Tests — 6/6 PASS ✅

| Test | Result |
|------|--------|
| `test_mcp_gitkraken_row_present` | PASS |
| `test_mcp_gitkraken_marked_blocked` | PASS |
| `test_readme_no_force_ask` | PASS |
| `test_readme_no_approval_dialog` | PASS |
| `test_readme_tier2_controlled_access` | PASS |
| `test_get_childitem_dot_workaround_present` | PASS |

### FIX-086 Regressions — 3/3 FAIL ❌ (New, not in baseline)

| Test | Failure |
|------|---------|
| `tests/FIX-086/test_fix086_tester_edge_cases.py::TestReadmeSecurityZoneDescriptions::test_readme_has_tier2_force_ask` | `AssertionError: README must describe Tier 2 Force Ask security zone` — DOC-067 intentionally removed "Force Ask" but this test was not updated |
| `tests/FIX-086/test_fix086_tester_edge_cases.py::TestPlaceholderUsage::test_placeholder_count_is_exactly_four` | `AssertionError: README must have exactly 5 {{PROJECT_NAME}} occurrences … found 4` — DOC-067 removed the only `{{PROJECT_NAME}}/` reference in Tier 2 description |
| `tests/FIX-086/test_fix086_tester_edge_cases.py::TestPlaceholderUsage::test_placeholder_appears_in_tier2_section` | `AssertionError: Tier 2 description must reference outside \`{{PROJECT_NAME}}/\`` — DOC-067 removed this reference from the Tier 2 wording |

### DOC-002 Regressions — 3/3 FAIL ❌ (New, not in baseline)

| Test | Failure |
|------|---------|
| `tests/DOC-002/test_doc002_tester_edge_cases.py::TestPlaceholderCount::test_default_readme_has_exactly_three_placeholder_occurrences` | `AssertionError: Expected 5 occurrences but found 4` |
| `tests/DOC-002/test_doc002_tester_edge_cases.py::TestPlaceholderCount::test_coding_template_readme_has_exactly_three_placeholder_occurrences` | `AssertionError: Expected 5 occurrences but found 4` |
| `tests/DOC-002/test_doc002_tester_edge_cases.py::TestAllOccurrencesInActualTemplate::test_all_three_actual_readme_occurrences_replaced` | `AssertionError: assert 4 == 5` — expected 5 substitutions in generated README, found 4 |

### Regression Baseline

All failures above are **not in `tests/regression-baseline.json`** — they are new failures introduced by this WP. All other full-suite failures were confirmed as pre-existing baseline entries. No other new regressions found beyond these 6.

---

## Root Cause

The change to `templates/agent-workbench/README.md` line 14:

```diff
-| **Tier 2 — Force Ask** | `.github/`, `.vscode/`, workspace root | Operations outside `{{PROJECT_NAME}}/` trigger an approval dialog |
+| **Tier 2 — Controlled Access** | `.github/`, `.vscode/`, workspace root | Reads of authorized paths (e.g. workspace-root config files, `.github/instructions/`) auto-allow silently; writes and access to restricted zones are denied |
```

This change:
1. Removed the string `"Force Ask"` — breaking `test_readme_has_tier2_force_ask` in FIX-086.
2. Removed the `{{PROJECT_NAME}}/` placeholder from the Tier 2 cell — reducing the total number of `{{PROJECT_NAME}}` occurrences from 5 to 4, breaking three placeholder-count tests in FIX-086 and DOC-002.
3. Removed the `outside \`{{PROJECT_NAME}}/\`` wording — breaking `test_placeholder_appears_in_tier2_section` in FIX-086.

The Developer's own DOC-067 tests check what was *added* but do not guard against what was *removed* from existing contracts.

---

## Checks Performed

| Check | Result |
|-------|--------|
| On correct branch (`DOC-067/agent-workbench-doc-gaps`) | ✅ |
| `templates/clean-workspace/` NOT touched | ✅ |
| `mcp_gitkraken_*` row in AGENT-RULES.md §3 marked Blocked | ✅ |
| `Get-ChildItem .` (explicit dot) workaround in AGENT-RULES.md §7 | ✅ |
| README.md contains "Controlled Access" | ✅ |
| README.md does NOT contain "Force Ask" | ✅ |
| README.md does NOT contain "trigger an approval dialog" | ✅ |
| MANIFEST.json regenerated | ✅ |
| `scripts/validate_workspace.py --wp DOC-067` exits 0 | ✅ |
| Full regression suite — no NEW failures | ❌ 6 new failures |
| ADR conflicts | None found (ADR-003 properly acknowledged) |
| Security scope | No security issues introduced |

---

## Required Fixes (TODOs for Developer)

### Option A — Fix the README.md (Recommended)

Restore a `{{PROJECT_NAME}}/` reference in the Tier 2 `Behaviour` cell so the placeholder count remains 5 and the `outside \`{{PROJECT_NAME}}/\`` contract is preserved. For example:

```markdown
| **Tier 2 — Controlled Access** | `.github/`, `.vscode/`, workspace root | Reads of authorized paths auto-allow silently; writes outside `{{PROJECT_NAME}}/` and restricted zone access are denied |
```

Then update `tests/FIX-086/test_fix086_tester_edge_cases.py`:
- `test_readme_has_tier2_force_ask`: Change assertion to check for `"Controlled Access"` instead of `"Force Ask"`. Rename the function to `test_readme_has_tier2_controlled_access`.

This leaves DOC-002 tests unchanged (they will pass with 5 occurrences again).

### Option B — Fix all 6 broken tests

Update the test files directly to match the new README content (only if the README wording not including `{{PROJECT_NAME}}/` is intentional):

**`tests/FIX-086/test_fix086_tester_edge_cases.py`:**
1. `test_readme_has_tier2_force_ask` → Rename to `test_readme_has_tier2_controlled_access` and change assertion to check `"Controlled Access"`.
2. `test_placeholder_count_is_exactly_four` → Change `assert count == 5` to `assert count == 4` and update the docstring.
3. `test_placeholder_appears_in_tier2_section` → Update or remove the assertion for `outside \`{{PROJECT_NAME}}/\``.

**`tests/DOC-002/test_doc002_tester_edge_cases.py`:**
4. `test_default_readme_has_exactly_three_placeholder_occurrences` → Change `assert count == 5` to `assert count == 4`.
5. `test_coding_template_readme_has_exactly_three_placeholder_occurrences` → Change `assert count == 5` to `assert count == 4`.
6. `test_all_three_actual_readme_occurrences_replaced` → Change `assert result.count("Nimbus/") == 5` to `== 4`.

> **Note:** The Tester cannot edit source files (`FIX-086`, `DOC-002` tests are outside `tests/DOC-067/`). These changes must be made by the Developer.

---

## Verdict

**FAIL** — Set WP status back to `In Progress`.

The 6 regressions are new (not baseline), caused directly by the README.md change. The WP implementation is otherwise correct and complete. Once the Developer resolves the placeholder count and tier-label contract issues (via Option A or B), the WP should pass cleanly.
