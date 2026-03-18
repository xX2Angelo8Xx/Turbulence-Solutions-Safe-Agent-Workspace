# SAF-028 Test Report — Tester Agent

**WP ID:** SAF-028  
**Branch:** saf-028  
**Commit reviewed:** e480fec  
**Tester:** Tester Agent  
**Date:** 2026-03-18  
**Verdict:** ❌ FAIL

---

## Summary

SAF-028 correctly implements Step 8 for the basic bare-verb cases (`dir`, `ls`, `gci`,
`Get-ChildItem`, `tree`, `find` with zero arguments from workspace root). All 21
Developer tests pass. However, the Tester edge-case sweep discovered **5 distinct
bypass vectors** that allow an agent to enumerate the workspace root despite the
bare-listing protection.

The bypass vectors all stem from a shared root cause: Step 8's token-classification
loop does not correctly filter out (a) whitespace-only quoted strings, and (b) flag
argument values (string/numeric tokens that immediately follow a flag parameter).

---

## Review Findings

### Implementation

| Item | Status |
|------|--------|
| `_BARE_LISTING_VERBS` constant defined | ✅ |
| Step 8 added after Step 7 in `_validate_args` | ✅ |
| `os.getcwd()` used (mockable) | ✅ |
| Empty quoted strings filtered | ✅ (`if not stripped:`) |
| Windows flags (`/b`, `/a`) filtered | ✅ (WIN_FLAG_RE_S8) |
| POSIX flags (`-Force`, `-Recurse`) filtered | ✅ (`if stripped.startswith("-")`) |
| Whitespace-only quoted strings filtered | ❌ (see BUG-066) |
| Flag argument values (strings) filtered | ❌ (see BUG-067) |
| Flag argument values (numeric) filtered | ❌ (see BUG-068) |
| Explicit `.` path treated as bare | ❌ (see BUG-069) |
| Template copy matches Default-Project | ✅ (SHA256 identical) |
| Hash constant `_KNOWN_GOOD_GATE_HASH` updated | ✅ |
| `dev-log.md` present and non-empty | ✅ |

---

## Test Results

### Developer Tests (21)

```
tests/SAF-028/test_saf028_bare_enumeration.py — 21/21 PASS
```

All 21 Developer tests pass. Regression against SAF-006 (95 tests) is clean.

### Tester Edge-Case Tests (10 — new, added in this review)

```
tests/SAF-028/test_saf028_tester_edge_cases.py
```

| Test | Expected | Actual | Result |
|------|----------|--------|--------|
| `test_gci_empty_path_param_denied` | deny | deny | ✅ PASS |
| `test_ls_combined_unix_flags_denied` | deny | deny | ✅ PASS |
| `test_gci_empty_literalpath_param_denied` | deny | deny | ✅ PASS |
| `test_dir_posix_github_path_denied` | deny | deny | ✅ PASS |
| `test_dir_whitespace_only_path_denied` | deny | allow | ❌ XFAIL (BUG-066) |
| `test_gci_include_filter_no_path_denied` | deny | allow | ❌ XFAIL (BUG-067) |
| `test_gci_filter_no_path_denied` | deny | allow | ❌ XFAIL (BUG-067) |
| `test_dir_recurse_depth_no_path_denied` | deny | allow | ❌ XFAIL (BUG-068) |
| `test_gci_depth_no_path_denied` | deny | allow | ❌ XFAIL (BUG-068) |
| `test_ls_dot_ws_root_denied` | deny | allow | ❌ XFAIL (BUG-069) |

### Full Suite Regression

```
3451 passed, 3 pre-existing failures, 29 skipped, 7 xfailed
```

Pre-existing failures (unrelated to SAF-028): FIX-009 TST-ID gaps/duplicates,
INS-005 Inno Setup `filesandirs` type. No new regressions introduced by SAF-028.

---

## Bugs Found

### BUG-066 — Whitespace-only quoted argument bypasses Step 8

**Command:** `dir "   "` (three spaces in quotes)  
**Bypass:** `shlex` (posix mode + whitespace_split) preserves the three-space
string as a token. `tok.strip("\"'")` strips only quotes → `'   '` (three
spaces, truthy). The `if not stripped:` guard does not fire. The three-space
token is appended to `path_args_s8`; `not path_args_s8` is False; CWD check
never fires.  
**Impact:** `dir "   "` from workspace root lists workspace root contents,
enumerating deny-zone subdirectory names.

### BUG-067 — String flag values treated as path arguments in Step 8

**Commands:** `gci -Include *.py`, `gci -Filter *.py`  
**Bypass:** Tokens following a flag parameter (in this case the values of
`-Include` and `-Filter`) are not flag tokens themselves (they don't start with
`-`). The Step 8 loop adds them to `path_args_s8` as if they were path
arguments. CWD check never fires.  
**Root cause:** Step 8 lacks `_prev_was_flag` tracking (present in Step 5 but
absent from Step 8).  
**Impact:** `gci -Include *.py` enumerates all .py files in workspace root.

### BUG-068 — Numeric flag values treated as path arguments in Step 8

**Commands:** `dir -Recurse -Depth 1`, `Get-ChildItem -Depth 1`  
**Bypass:** Identical root cause to BUG-067. The numeric string `"1"` (value of
`-Depth`) does not start with `-`, does not match WIN_FLAG_RE_S8, and is not an
ENV_ASSIGN. It is added to `path_args_s8`; CWD check never fires.  
**Impact:** `-Depth 1` listing commands from workspace root proceed unchecked.

### BUG-069 — `ls .` explicit dot bypasses Step 8

**Command:** `ls .`  
**Bypass:** `ls .` provides an explicit path argument `.`. Step 8's
`not path_args_s8` is False (path_args_s8 = ['.']), so the CWD check does not
fire. Step 5 zone-checks `.` but the zone classifier returns `"allow"` for the
workspace root (only its children `.github`, `.vscode`, `NoAgentZone` are deny
zones). Neither Step 7 (non-recursive) nor Step 8 catches it.  
**Impact:** `ls .` from workspace root is semantically identical to bare `ls` —
both list workspace root contents including deny-zone subdirectory names.

---

## Bypass Vector Summary

| BUG | Bypass command | Root cause | CWD check fires? |
|-----|----------------|------------|-----------------|
| BUG-066 | `dir "   "` | Whitespace-only token is truthy | No |
| BUG-067 | `gci -Include *.py` | String flag value added to path_args_s8 | No |
| BUG-067 | `gci -Filter *.py` | String flag value added to path_args_s8 | No |
| BUG-068 | `dir -Recurse -Depth 1` | Numeric flag value added to path_args_s8 | No |
| BUG-068 | `Get-ChildItem -Depth 1` | Numeric flag value added to path_args_s8 | No |
| BUG-069 | `ls .` | Explicit `.` zone-classifies as allow | Zone checks `.` → allow |

---

## Developer TODOs (required before re-review)

### TODO-1: Fix whitespace-only string detection (BUG-066)

In Step 8's token loop, change the empty-string guard from:

```python
if not stripped:  # empty quoted string — not a real path
    continue
```

to:

```python
if not stripped.strip():  # empty or whitespace-only — not a real path
    continue
```

This ensures `'   '` (spaces only) is also excluded, matching the design intent
stated in the dev-log.

---

### TODO-2: Add `_prev_was_flag` tracking in Step 8 (BUG-067, BUG-068)

Step 5 already uses `_prev_was_flag` to skip tokens that are argument values of
flag parameters. Add the same pattern to Step 8:

```python
_prev_was_flag_s8 = False
for tok in args:
    stripped = tok.strip("\"'")
    if not stripped.strip():  # empty or whitespace-only
        _prev_was_flag_s8 = False
        continue
    if stripped.startswith("-"):
        _prev_was_flag_s8 = True
        continue
    if _WIN_FLAG_RE_S8.match(stripped):
        _prev_was_flag_s8 = True  # treat as flag (consumes no value)
        continue
    if _ENV_ASSIGN_RE.match(stripped):
        _prev_was_flag_s8 = False
        continue
    if _prev_was_flag_s8:
        # This token is the value of the preceding flag, not a path
        _prev_was_flag_s8 = False
        continue
    _prev_was_flag_s8 = False
    path_args_s8.append(stripped)
```

After this change, `*.py` (value of `-Include`/`-Filter`) and `1` (value of
`-Depth`) will no longer be treated as path arguments.

---

### TODO-3: Handle explicit `.` path as implicit CWD target (BUG-069)

After the `path_args_s8` loop, when the only collected "paths" are `.` or `./`
(i.e., explicit references to CWD), treat them as equivalent to no path argument
and apply the CWD ancestor check. Add logic before the `if not path_args_s8:`
block:

```python
# If all collected paths resolve to "." (explicit CWD), treat as bare
_CWD_DOTS = frozenset({".", "./"})
path_args_s8 = [p for p in path_args_s8 if p not in _CWD_DOTS]
```

This ensures `ls .` is treated the same as bare `ls`.

---

### TODO-4: Update `_KNOWN_GOOD_GATE_HASH` after all fixes

After implementing TODOs 1–3, run `update_hashes.py` to recompute and embed the
new `_KNOWN_GOOD_GATE_HASH`. Sync both copies:
- `Default-Project/.github/hooks/scripts/security_gate.py`
- `templates/coding/.github/hooks/scripts/security_gate.py`

---

### TODO-5: Remove `xfail` markers from Tester edge-case tests

Once all fixes are in place, remove the `@pytest.mark.xfail` decorator from all
6 bypass tests in `tests/SAF-028/test_saf028_tester_edge_cases.py`. They should
now all pass as regular assertions.

---

### TODO-6: Add regression tests for the fixed bypass patterns to Developer test file

After fixes, also add the corrected-behavior tests to the Developer's main test
file (`test_saf028_bare_enumeration.py`) so they become permanent regression
anchors in the Developer test set.

---

## Pre-Done Checklist

- [x] `dev-log.md` exists and is non-empty
- [x] `test-report.md` written by Tester Agent (this file)
- [x] `tests/SAF-028/test_saf028_tester_edge_cases.py` created with 10 edge-case tests
- [x] Test runs logged in `test-results.csv` (TST-1795, TST-1796)
- [x] Bugs logged in `bugs.csv` (BUG-066 through BUG-069)
- [ ] WP **SAF-028** set back to **In Progress**
- [ ] Commit: `SAF-028: Tester FAIL — 5 bypass vectors found in Step 8`
- [ ] Push: `git push origin saf-028`
