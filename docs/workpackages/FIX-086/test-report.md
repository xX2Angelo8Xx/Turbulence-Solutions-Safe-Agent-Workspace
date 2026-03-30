# Test Report — FIX-086

**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Iteration:** 1  

---

## Summary

FIX-086 restores the workspace root `README.md` in the `templates/agent-workbench/` template, fixing
BUG-158 (regression from v3.2.3→v3.2.4). The implementation correctly:

1. Updates `templates/agent-workbench/README.md` with an agent-workbench-specific title and an
   early pointer to `AGENT-RULES.md`.
2. Preserves all security-zone content (Tier 1/2/3, exempt tools list) so DOC-002 regression tests
   continue to pass.
3. Maintains exactly 4 `{{PROJECT_NAME}}` placeholder occurrences required by DOC-002.
4. Provides 11 tests covering template file presence, content sections, and workspace creation
   behavior for both `include_readmes=True` and `include_readmes=False`.

The Tester added 18 additional edge-case tests covering security tier descriptions, placeholder
count correctness, UTF-8 encoding, title specificity, early AGENT-RULES.md orientation,
`templates/coding/` consistency, and workspace-creation boundary conditions.

**Verdict: PASS**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2307: FIX-086 full regression suite (run_tests.py) | Regression | Pass | 7506 passed, 84 pre-existing failures (same as main), 33 skipped. No new failures. |
| TST-2308: FIX-086 developer tests (11 passed) | Regression | Pass | BUG-158 regression guard, template presence, workspace creation, placeholder replacement |
| TST-2309: FIX-086 tester edge-case tests (18 passed) | Regression | Pass | Security zone tiers, placeholder count=4, UTF-8 encoding, title check, early AGENT-RULES.md, coding template consistency, workspace creation edge cases |
| TST-2310: FIX-086 full regression suite (Tester run) | Regression | Pass | Confirmed: 84 failures = same 84 on main. No regressions introduced by FIX-086. |

**Total: 29 FIX-086-specific tests passed, 0 failed.**

---

## Regression Analysis

The 84 failures visible in the full suite are **all pre-existing** on the `main` branch (confirmed
by running the identical suite on `main` and counting 84 failed, same test IDs). The relevant sets:

- `INS-004/test_coding_prompts_review_exists` — `review.prompt.md` missing from template (pre-existing)
- `FIX-077` version string test — version number expectation outdated (pre-existing)
- `INS-014/015/017` — CI workflow step count tests (pre-existing)
- `INS-019` shim tests — python-path.txt related (pre-existing)
- `MNT-002`, `SAF-010`, `SAF-025` — various pre-existing issues

None of these are related to FIX-086's changes (`templates/agent-workbench/README.md`).

DOC-002 (27 tests) — **all pass** — confirms backward compatibility with existing placeholder tests.
INS-004 (58 tests) — 57 pass, 1 pre-existing fail — no regression from FIX-086.

---

## Edge-Case Analysis

| Area | Finding |
|------|---------|
| Security zone correctness | All three tiers (Auto-Allow, Force Ask, Hard Block) accurately described in README ✓ |
| `{{PROJECT_NAME}}` count | Exactly 4 occurrences — satisfies DOC-002 strict count test ✓ |
| Placeholder in all three critical sections | Tier 1, Tier 2, Exempt Tools sections all use the placeholder ✓ |
| UTF-8 encoding | README decodes clean with no BOM issues ✓ |
| Title specificity | First non-empty line contains "Safe" and "Agent" — not generic ✓ |
| AGENT-RULES.md early orientation | Reference appears within the first 5 non-empty lines ✓ |
| `templates/coding/` consistency | No separate README in `templates/coding/` — no divergence risk ✓ |
| Placeholder replacement idempotency | All 4 occurrences replaced; `CleanProject/` appears ≥4 times post-creation ✓ |
| `include_readmes=False` boundary | README correctly absent at workspace root when disabled ✓ |

---

## Bugs Found

None. BUG-158 is resolved. No new bugs found during testing.

---

## TODOs for Developer

None. WP passes all requirements.

---

## Verdict

**PASS — mark WP as Done.**

All acceptance criteria are met:
- `templates/agent-workbench/README.md` exists with workspace structure documentation ✓
- Newly created workspaces have `README.md` at root (when `include_readmes=True`) ✓
- BUG-158 regression is guarded by dedicated tests ✓
- No existing tests broken ✓
