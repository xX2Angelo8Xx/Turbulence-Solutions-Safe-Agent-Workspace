# Test Report — SAF-006

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 2

---

## Summary

SAF-006 Iteration 2 introduced `_is_ancestor_of_deny_zone()`, `_has_recursive_flag()`,
`_INHERENTLY_RECURSIVE_COMMANDS`, and Step 7 in `_validate_args()`. All 46 developer
tests pass. The core protection logic (blocking tree/find at workspace root and
deny-zone paths) is correct and complete.

However, a **design inconsistency (BUG-023)** was found: standalone recursive flags
(`-r`, `-R`) in `ls.denied_flags` and `gci.denied_flags` block ALL recursive use
regardless of path, while combined flags (`-lR`, `-Rl`) correctly allow recursive
listing of safe zones via Step 7's ancestor check. This means:

- `ls -R Project/` → **deny** (Step 1, `denied_flags`)  ← wrong per US-011
- `ls -lR Project/` → **ask** (Step 7, ancestor check) ← correct per US-011
- `gci -r Project/` → **deny** (Step 1, `denied_flags`)  ← wrong per US-011

The user story AC states: *"Recursive file listing commands targeting protected zones
are blocked."* — safe zones (`Project/`) must NOT be blocked. The `denied_flags`
remnants contradict both the user story and the SAF-006 Step 7 design intent.

**Verdict: FAIL** — 2 new edge-case tests expose the inconsistency.

---

## Tests Executed

### Developer tests (baseline)
| Test | Type | Result | Notes |
|------|------|--------|-------|
| 46 developer tests (test_saf006_recursive_protection.py) | Unit / Security / Regression | Pass (46/46) | TST-312 |

### Tester edge-case tests
| Test | Type | Result | Notes |
|------|------|--------|-------|
| test_ec_tree_relative_project_allowed | Security | Pass | `tree Project/` → ask |
| test_ec_find_name_flag_ws_root_blocked | Security | Pass | `find . -name '*.py'` → deny |
| test_ec_find_project_name_flag_allowed | Security | Pass | `find Project/ -name '*.py'` → ask |
| test_ec_ls_capital_r_posix_root_blocked | Security | Pass | `ls -R /` → deny |
| test_ec_ls_capital_r_project_should_allow | Security | **FAIL** | BUG-023: `ls -R Project/` → deny (expected ask) |
| test_ec_ls_combined_lr_project_allowed | Regression | Pass | `ls -lR Project/` → ask (consistent with Step 7) |
| test_ec_ls_combined_rl_no_path_blocked | Regression | Pass | `ls -Rl` → deny (BUG-022 fix verified) |
| test_ec_ls_combined_rl_project_allowed | Regression | Pass | `ls -Rl Project/` → ask |
| test_ec_gci_r_project_should_allow | Security | **FAIL** | BUG-023: `gci -r Project/` → deny (expected ask) |
| test_ec_find_traversal_dotdot_github_blocked | Security | Pass | `find ../../.github` → deny |
| test_ec_dir_no_s_project_safe | Regression | Pass | `dir Project/` → ask (non-recursive still allowed) |
| test_ec_get_childitem_no_recurse_project_safe | Regression | Pass | `Get-ChildItem Project/` → ask |
| test_ec_ls_no_recurse_project_safe | Regression | Pass | `ls Project/` → ask |

### Full regression suite (TST-315)
| Category | Count | Notes |
|----------|-------|-------|
| SAF-006 total (59 tests) | 57 pass / 2 fail | 2 fail = BUG-023 |
| Full suite (600 tests) | 564 pass / 35 fail / 1 skip | 33 pre-existing (INS-004 In Progress, 1 INS-012); 2 new SAF-006 |

---

## Bugs Found

- **BUG-023**: SAF-006 design inconsistency — standalone recursive flags deny ALL
  paths while combined flags are path-aware (logged in `docs/bugs/bugs.csv`)

---

## TODOs for Developer

- [ ] **Remove `-r` and `--recursive` from `ls.denied_flags`** in `_COMMAND_ALLOWLIST`.
  These flags are already handled by `_RECURSIVE_FLAG_MAP["ls"]` and Step 7's
  `_has_recursive_flag()` / `_is_ancestor_of_deny_zone()` ancestor check. With
  them in `denied_flags`, `ls -R Project/` is denied by Step 1 before Step 7 can
  apply the path-aware check. Verified that removing them does NOT break
  `test_ls_r_no_args_blocked` — Step 7 still catches `ls -r` with no path
  because the implicit workspace-root target is an ancestor of deny zones.

- [ ] **Remove `-recurse` and `-r` from `gci.denied_flags`** (and identically from
  `get-childitem.denied_flags`) for the same reason. `_RECURSIVE_FLAG_MAP` already
  maps `gci` → `{"-recurse", "-r"}` so Step 7 will handle them.

- [ ] **Remove `/s` from `dir.denied_flags`** for consistency. `dir` is already in
  `_RECURSIVE_FLAG_MAP` with `/s`. Same design argument applies: `dir /s Project/`
  should be allowed per US-011 but is currently denied by Step 1.

- [ ] **Update `ls` and `gci` allowlist notes** from "non-recursive listing only"
  to "recursive listing allowed only in non-ancestor paths (Step 7 check)" to
  reflect the SAF-006 design intent correctly.

- [ ] **Add regression tests** for the fixed cases so they cannot regress:
  - `ls -R Project/` → ask
  - `ls -r Project/` → ask
  - `gci -r Project/` → ask
  - `gci -recurse Project/` → ask
  - `dir /s Project/` → ask
  - `ls -R .github` → deny (Step 7 ancestor check still works)
  - `gci -r .github` → deny (Step 7 ancestor check still works)

- [ ] **Verify `dir /s Project/` behavior** — same issue as ls and gci; expected
  to be allowed per US-011 once `/s` is removed from `dir.denied_flags`.

- [ ] **Note on BUG-021 and BUG-022 tracking**: workpackages.csv comments reference
  BUG-021 (code not committed) and BUG-022 (combined flags) as fixed in Iteration 2,
  but neither entry exists in `docs/bugs/bugs.csv`. Developer should add retrospective
  BUG-021 and BUG-022 entries (both Closed, fixed in SAF-006 Iteration 2).

---

## Verdict

**FAIL** — return to Developer.

Iteration 1 fixes are confirmed (BUG-021 resolved: code committed; BUG-022 resolved:
`_has_recursive_flag()` detects combined POSIX flags). However, BUG-023 (standalone
recursive flags in `denied_flags` block safe-zone paths that should be allowed per
US-011) was discovered during edge-case testing and must be fixed before approval.

The 2 failing tests (`test_ec_ls_capital_r_project_should_allow`,
`test_ec_gci_r_project_should_allow`) in `tests/SAF-006/test_saf006_recursive_edge_cases.py`
must pass in Iteration 3.
