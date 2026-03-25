# Test Report — SAF-050

**WP:** SAF-050  
**Title:** Prevent grep_search information leak on workspace root files  
**Branch:** SAF-050/grep-search-leak  
**Tester:** Tester Agent  
**Date:** 2026-03-25  
**Verdict:** ❌ FAIL — Returned to In Progress

---

## Summary

The Developer's implementation correctly fixes the original inconsistency reported
in BUG-115 (workspace root files allowed by `read_file` but denied by
`grep_search` with an `includePattern`). All 41 Developer tests pass.

However, **two regressions were introduced** by the SAF-050 changes:

1. **Logic regression (BUG-127):** The new `_include_pattern_targets_deny_zone`
   helper uses `any()` over all path components, which incorrectly denies
   `includePattern` values like `project/.github/**` and `project/.vscode/**`.
   These patterns target deny-zone directories nested *inside* the agent's project
   folder, not at the workspace root, and must be allowed.
   **2 SAF-045 tester edge-case tests now fail as a direct result.**

2. **Missing hash update (BUG-128):** `security_gate.py` was modified but
   `update_hashes.py` was not run. The `_KNOWN_GOOD_GATE_HASH` constant is stale
   (stored `c453763...` ≠ computed `707823a...`). **7 integrity tests fail.**

---

## Test Runs

| ID | Name | Type | Status | Notes |
|----|------|------|--------|-------|
| TST-2204 | SAF-050 Developer suite (41 tests) | Unit | ✅ Pass | All 41 Developer tests pass |
| TST-2205 | SAF-050 Tester edge-case suite (8 tests) | Security | ❌ Fail | 4 regression failures, 4 bypass tests pass |
| TST-2206 | SAF-050 Regression check vs SAF-045 + hash tests | Regression | ❌ Fail | 9 new failures vs pre-SAF-050 baseline |

---

## Failures Summary

### New failures introduced by SAF-050 (9 total)

| Test | File | Type | Root Cause |
|------|------|------|------------|
| `test_grep_search_project_vscode_nested_allow` | `tests/SAF-045/test_saf045_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_grep_search_project_github_nested_allow` | `tests/SAF-045/test_saf045_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_edge_project_github_nested_allow` | `tests/SAF-050/test_saf050_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_edge_project_vscode_nested_allow` | `tests/SAF-050/test_saf050_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_edge_project_noagentzone_nested_allow` | `tests/SAF-050/test_saf050_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_edge_deep_concrete_prefix_vscode_allow` | `tests/SAF-050/test_saf050_tester_edge_cases.py` | Regression | BUG-127: any() check too broad |
| `test_verify_file_integrity_passes_with_good_hashes` | `tests/SAF-008/test_saf008_integrity.py` | Regression | BUG-128: stale hash |
| `test_embedded_gate_hash_matches_canonical_hash` + 3 more | `tests/SAF-025/test_saf025_hash_sync.py` | Regression | BUG-128: stale hash |
| `test_security_gate_hashes_valid` | `tests/FIX-042/test_fix042_noagentzone_visible.py` | Regression | BUG-128: stale hash |
| `test_gate_hash_valid_after_fix` | `tests/FIX-069/test_fix069_zone_classifier_import.py` | Regression | BUG-128: stale hash |

### Pre-existing failures (not caused by SAF-050)

| Test | Pre-existed? | Evidence |
|------|-------------|---------|
| `test_no_pycache_in_templates_coding` | ✅ Yes | Present on ebeace7 (SAF-046 commit) |
| `test_noagentzone_not_in_files_exclude_default` | ✅ Yes | Present on ebeace7 |
| `test_noagentzone_not_in_files_exclude_template` | ✅ Yes | Present on ebeace7 |
| FIX-028/031/038/039/037 codesign tests | ✅ Yes | Unrelated to security gate |
| INS-014/015/017 build job step count | ✅ Yes | Unrelated to security gate |

---

## Bug Details

### BUG-127 — Logic regression: `_include_pattern_targets_deny_zone` too broad

**Location:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
in `_include_pattern_targets_deny_zone()`, the relative-pattern branch.

**Current (broken) code:**
```python
components = [c.lower() for c in norm_pattern.split("/")]
if any(c in _WILDCARD_DENY_ZONES for c in components):
    return True
return False
```

**Problem:** This checks if ANY component equals a deny zone name. The pattern
`project/.github/**` has components `["project", ".github", "**"]`. The
`any()` finds `.github` and returns `True` (deny), even though `.github` is
nested inside `project/` — the agent's own project folder.

**Dev-log describes the intended behavior (Section: Implementation):**
> For relative patterns: denies only if the first path component is a deny zone
> name (.github, .vscode, noagentzone). … allowing patterns that start inside an
> allowed folder (project/.github/**, src/.vscode/**).

**The code contradicts the spec.**

**Required fix:** Only deny if the deny zone component appears before any
*concrete* (non-wildcard, non-deny-zone) path anchor. Examples:

| Pattern | First concrete component | Deny? | Reason |
|---------|--------------------------|-------|--------|
| `.github/**` | `.github` (deny zone) | ✅ DENY | Workspace root deny zone at position 0 |
| `**/.github/**` | `**` (wildcard) | ✅ DENY | Wildcard expands to zero segments → can reach workspace root |
| `*/.github/**` | `*` (wildcard) | ✅ DENY | Conservative: `*` could match any directory |
| `project/.github/**` | `project` (concrete) | ✅ ALLOW | `.github` nested inside project folder |
| `project/.vscode/**` | `project` (concrete) | ✅ ALLOW | `.vscode` nested inside project folder |
| `project/src/.vscode/**` | `project` (concrete) | ✅ ALLOW | Deeper concrete prefix |
| `*.py` | `*.py` (not a deny zone) | ✅ ALLOW | No deny zone component at all |

**Suggested algorithm (pseudocode):**
```python
seen_concrete_anchor = False
for c in components:
    is_wildcard = c in ("*", "**") or "*" in c or "?" in c
    in_deny_zone = c in _WILDCARD_DENY_ZONES
    if in_deny_zone and not seen_concrete_anchor:
        return True   # deny zone reachable from workspace root
    if not is_wildcard and not in_deny_zone:
        seen_concrete_anchor = True
return False
```

> **Important:** The `**/.github/**` bypass must remain DENIED. Changing from
> `any()` to first-component-only is NOT sufficient — a wildcard prefix before
> the deny zone name must also trigger a deny. The algorithm above handles this.
> See tester edge-case tests for all required behaviors.

---

### BUG-128 — `_KNOWN_GOOD_GATE_HASH` not updated after security_gate.py modification

**Location:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`,
constant `_KNOWN_GOOD_GATE_HASH` on line ~96.

**Stored value:** `c453763711aff3617a03df7ab6391b10c9109337536427470b071c10c4462c09`  
**Computed value:** `707823abbd6cbe8e72c42101254d2b6ea4492d5b1cfbd9177eb733a1af6d7983`

**Required fix:**
1. Fix BUG-127 (code change).
2. Run `update_hashes.py` to recompute and store the new hash:
   ```powershell
   .venv\Scripts\python.exe templates\coding\.github\hooks\scripts\update_hashes.py
   ```
3. Verify `_KNOWN_GOOD_GATE_HASH` in the file matches the computed hash.
4. Run `tests/SAF-025/`, `tests/SAF-008/`, `tests/FIX-042/`, `tests/FIX-069/`
   to confirm all hash tests pass.

---

## Security Assessment

The SAF-050 bypass guard tests **all pass** in the current implementation:
- `**/.github/**` → ✅ correctly DENIED  
- `**/.vscode/**` → ✅ correctly DENIED
- `**/NoAgentZone/**` → ✅ correctly DENIED
- `*/.github/**` → ✅ correctly DENIED
- Path traversal `project/../../.github/**` → ✅ correctly DENIED
- Brace expansion `{.github,project}/**` → ✅ correctly DENIED

No security bypass was found. The regression is a false-negative direction
(over-restriction, not under-restriction) — legitimate paths are incorrectly
denied, but no protected zones are exposed.

The hash failure (BUG-128) means the integrity guard is currently reporting a
mismatch for every hook invocation, which would lock all tools in a real
deployment. This is a medium-high severity operational issue.

---

## Required Developer Actions (TODOs)

### TODO 1 — Fix `_include_pattern_targets_deny_zone` logic (BUG-127)

In `templates/agent-workbench/.github/hooks/scripts/security_gate.py`,
function `_include_pattern_targets_deny_zone`, the relative-pattern branch
**must** be changed from:

```python
components = [c.lower() for c in norm_pattern.split("/")]
if any(c in _WILDCARD_DENY_ZONES for c in components):
    return True
return False
```

To an algorithm that:
1. Iterates components left to right.
2. DENIES if a deny-zone component is found AND no concrete (non-wildcard,
   non-deny-zone) component has been seen yet.
3. Sets `seen_concrete_anchor = True` when a concrete directory name is found.
4. Returns `False` (allow) if a concrete anchor precedes all deny-zone
   components.

After the fix, ALL of the following must be verified:
- `project/.github/**` → allow  
- `project/.vscode/**` → allow
- `project/NoAgentZone/**` → allow
- `project/src/.vscode/**` → allow
- `.github/**` → deny (unchanged)
- `**/.github/**` → deny (wildcard bypass must still be caught)
- `*/.github/**` → deny (conservative)

Tests to pass: `tests/SAF-050/test_saf050_tester_edge_cases.py` (all 8),
`tests/SAF-045/test_saf045_tester_edge_cases.py::test_grep_search_project_vscode_nested_allow`,
`tests/SAF-045/test_saf045_tester_edge_cases.py::test_grep_search_project_github_nested_allow`.

### TODO 2 — Run `update_hashes.py` (BUG-128)

After fixing BUG-127, run:
```powershell
.venv\Scripts\python.exe templates\coding\.github\hooks\scripts\update_hashes.py
```
Verify `_KNOWN_GOOD_GATE_HASH` in `security_gate.py` is updated to the new value.

Tests to pass: `tests/SAF-025/`, `tests/SAF-008/test_saf008_integrity.py::test_verify_file_integrity_passes_with_good_hashes`,
`tests/FIX-042/test_fix042_noagentzone_visible.py::test_security_gate_hashes_valid`,
`tests/FIX-069/test_fix069_zone_classifier_import.py::test_gate_hash_valid_after_fix`.

### TODO 3 — Full test suite must be green (minus pre-existing failures)

Run the full suite before re-submitting:
```powershell
.venv\Scripts\python.exe -m pytest tests/ --tb=short -q 2>&1 | Select-Object -Last 30
```

Acceptable pre-existing failures (verified to pre-date SAF-050 on ebeace7):
- `test_no_pycache_in_templates_coding`
- `test_noagentzone_not_in_files_exclude_default`
- `test_noagentzone_not_in_files_exclude_template`
- FIX-028/029/031/037/038/039 codesign tests
- INS-014/015/017 step count tests
- Others present on the baseline commit

Any failure beyond those pre-existing failures is a blocker.

---

## Verdict

**FAIL** — WP returned to `In Progress`.

Two blocking issues:
1. **BUG-127** — Logic regression breaks SAF-045 tests (6 total failures).
2. **BUG-128** — Stale `_KNOWN_GOOD_GATE_HASH` causes 7 integrity test failures.
