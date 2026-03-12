# Test Report — SAF-006

**Tester:** Tester Agent
**Date:** 2026-03-12
**Iteration:** 4

## Verdict: PASS

---

## Summary

SAF-006 Iteration 4 addresses **BUG-024** (Windows-style flags `/s`, `/b`, etc. were being collected as path arguments in Step 7, preventing the cwd fallback and allowing `dir /s` without an explicit path to return `ask` instead of `deny`).

The Developer added `_WIN_FLAG_RE = re.compile(r'^/[a-zA-Z0-9]{1,2}$')` inside the `if is_recursive:` block of `_validate_args()`. Tokens matching this pattern are now skipped before being added to `path_args`, so the cwd fallback fires correctly when no real path arguments are present.

**Review findings:**
- The regex `^/[a-zA-Z0-9]{1,2}$` correctly matches short Windows flags (`/s`, `/b`, `/S`, `/ad`) and does **not** match real paths (`/workspace`, `/home/user`) because those have more than two characters after `/` or contain embedded `/`.
- The guard is placed correctly inside the `if is_recursive:` block so it only runs on commands that have already triggered `_has_recursive_flag()` — non-recursive `dir /ad` is unaffected.
- The cwd fallback (`if not path_args: path_args = ["."]`) now fires as intended when all arguments are Windows flags.
- No regressions: `dir /s Project/` still returns `ask` because the real path argument survives the filter.

All 82 tests pass, including 17 new tester-authored edge-case tests.

---

## Tests Executed

### Developer tests — `test_saf006_recursive_protection.py` (46 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Full 46-test suite | Security / Unit | Pass | All 46 pass including `test_dir_slash_s_blocked` (BUG-024 regression) |

### Developer edge-case tests — `test_saf006_edge_cases.py` (19 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Full 19-test suite | Security / Regression | Pass | All 19 pass including `test_dir_slash_s_no_path_blocked`, `test_dir_slash_s_slash_b_no_path_blocked` |

### Tester iteration 4 edge-cases — `test_saf006_tester_iter4.py` (17 tests)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| `test_dir_slash_s_slash_b_with_safe_path_asks` | Security | Pass | Flags filtered, real path kept → ask |
| `test_dir_slash_s_slash_b_relative_safe_path_asks` | Security | Pass | Relative safe path retained → ask |
| `test_dir_slash_s_slash_b_deny_zone_denied` | Security | Pass | Flags filtered, deny-zone path retained → deny |
| `test_dir_attr_flag_not_recursive` | Unit | Pass | `/ad` alone — not recursive, Step 7 not triggered → ask |
| `test_dir_attr_flag_with_path_asks` | Unit | Pass | `/ad` + safe path — no ancestor → ask |
| `test_dir_slash_s_github_trailing_slash_denied` | Security | Pass | Trailing slash normalised → deny |
| `test_dir_slash_s_vscode_trailing_slash_denied` | Security | Pass | `.vscode/` trailing slash → deny |
| `test_dir_slash_S_uppercase_cwd_fallback_denied` | Security | Pass | `/S` filtered by WIN_FLAG_RE (case-insensitive) → cwd fallback → deny |
| `test_dir_slash_s_long_absolute_path_not_filtered` | Security | Pass | Long path NOT filtered by WIN_FLAG_RE → ask |
| `test_dir_slash_s_long_absolute_deny_zone_denied` | Security | Pass | Long path to deny zone → deny |
| `test_tree_slash_f_no_path_denied` | Security | Pass | `/f` filtered → cwd fallback → deny |
| `test_tree_slash_f_slash_a_no_path_denied` | Security | Pass | Both `/f` and `/a` filtered → deny |
| `test_tree_slash_f_safe_path_asks` | Security | Pass | `/f` filtered, safe path kept → ask |
| `test_tree_slash_f_deny_zone_denied` | Security | Pass | `/f` filtered, deny-zone path retained → deny |
| `test_dir_slash_s_slash_ad_no_path_denied` | Security | Pass | 2-char `/ad` also matched by WIN_FLAG_RE → cwd fallback → deny |
| `test_dir_slash_s_slash_ad_safe_path_asks` | Security | Pass | 2-char flag filtered, safe path kept → ask |
| `test_dir_slash_s_slash_ad_deny_zone_denied` | Security | Pass | 2-char flag filtered, deny zone kept → deny |

### Full combined suite (82 tests)

| Result | Count |
|--------|-------|
| Pass | 82 |
| Fail | 0 |
| **Total** | **82** |

---

## Attack Vector Analysis

| Vector | Result | Notes |
|--------|--------|-------|
| `dir /s` no path — cwd = workspace root | deny | BUG-024 regression; fixed |
| `dir /s /b` no path — two flags, no path | deny | BUG-024 variant; fixed |
| `dir /S` uppercase flag | deny | WIN_FLAG_RE matches upper/lower via `[a-zA-Z0-9]` |
| `dir /s /ad` — 2-char flag + no path | deny | 2-char flags correctly filtered |
| `dir /s Project/` — flags + safe path | ask | Real path arg retained after filtering |
| `dir /s .github/` — trailing slash deny zone | deny | `normalize_path` strips trailing slash |
| `tree /f` — Windows display flag, no path | deny | Inherently recursive; `/f` filtered → cwd fallback |
| `tree /f /a` — two Windows tree flags | deny | Both filtered; no path → cwd fallback |
| `tree /f Project/` — display flag + safe path | ask | Real path survives filter |
| Long `/workspace/project` starting with `/` | not filtered | Only 1–2 char alphanumeric after `/` matches WIN_FLAG_RE |

**Boundary analysis of WIN_FLAG_RE `^/[a-zA-Z0-9]{1,2}$`:**
- Matches: `/s`, `/S`, `/b`, `/ad`, `/3`, `/r2` — all short Windows flags ✓
- Does NOT match: `/workspace`, `/home`, `/mnt/c`, `/` (zero chars) — real paths safe ✓
- Does NOT match: `/sab` (3 chars) — 3-char+ Windows flags not filtered; `dir /s /sab` with no real path would see `/sab` added to path_args and `_is_ancestor_of_deny_zone('/sab', ...)` would return False (not a deny-zone ancestor), so the command returns `ask`. This is a narrow theoretical gap for non-standard flags, but such a command would fail on Windows and `/sab` is not a real deny-zone ancestor; no actionable exploit path exists.

**Minor observation (non-blocking):** `_WIN_FLAG_RE` is compiled inside the `if is_recursive:` block on every `_validate_args()` call rather than at module level. Python's internal regex cache mitigates this in practice. Recorded for developer awareness; no security impact.

---

## Bugs Found

None new. BUG-024 is confirmed fixed and closed.

---

## TODOs for Developer

None — all acceptance criteria satisfied.

---

## Verdict

**PASS — mark SAF-006 as Done.**

All 82 tests pass. BUG-024 is resolved. The `_WIN_FLAG_RE` fix correctly filters Windows-style short flags from `path_args` while leaving real path arguments intact, and the cwd fallback fires as intended. No new security defects found.
