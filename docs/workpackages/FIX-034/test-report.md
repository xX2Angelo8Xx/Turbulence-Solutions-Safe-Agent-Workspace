# Test Report — FIX-034

**Tester:** Tester Agent
**Date:** 2026-03-18
**Iteration:** 1

## Summary

FIX-034 implements an early venv activation detection pass in `sanitize_terminal_command()` that runs before Stage 3 obfuscation pre-scan. The implementation correctly handles all standard venv activation forms (`source`, `&`, POSIX dot-source, direct execution) and denies activation paths outside the project folder.

All 40 Developer tests pass. 17 additional Tester edge-case tests were added and pass. Full regression across FIX-033, FIX-023, SAF-020, FIX-032 shows 0 regressions (294 total).

**Verdict: PASS**

---

## Code Review Findings

### `_VENV_ACTIVATION_SEG_RE` regex analysis

The regex is structurally correct with these observations:

1. **Path traversal (`../../.venv/bin/activate`)**: The optional dir prefix `(?:[^\s]*[/\\])?` will match `../../` before the `.venv` literal. However, after the regex match, `posixpath.normpath` normalises the traversal and `zone_classifier.classify` resolves it against the workspace root — the classifier correctly denies paths that escape `ws_root`. `_try_project_fallback` joins the path after the project folder and runs it through `classify` again; traversal above project resolves to an absolute path outside the workspace and is denied. **Secure. ✓**

2. **Unicode tricks**: Characters like U+202E (RLO) inside a path break the `[/\\]` separator match; the segment is not whitelisted and falls through to Stage 3 where P-22 fires. Non-ASCII venv directory names (e.g. Greek letters) cannot match the literal ASCII regex `venv`. **Secure. ✓**

3. **Null bytes**: `\x00` is a C0 control character. It is NOT stripped before the regex runs — the regex sees `.venv\x00/bin/activate`, where `\x00` fails the `[/\\]` separator match. The segment falls to Stage 3, P-22 fires. (`normalize_path` strips C0 chars but classify is called with the post-normpath path, not the raw regex input.) **Secure. ✓**

4. **Venv-like names (`venv2`, `.venv_project`)**: `\.?venv` matches only `. venv` or `venv` exactly, followed immediately by `[/\\]`. Any suffix (digit, underscore) between `venv` and the separator breaks the match. **Secure. ✓**

5. **`bin/activate.ps1` false acceptance**: The regex allows `.ps1` only under `Scripts/`, not `bin/`. `source .venv/bin/activate.ps1` falls through to Stage 3 → P-22 fires. **Secure. ✓**

6. **`_venv_seg_indices` blind-spot analysis**: Excluded segments skip Stage 3 obfuscation scan AND Stage 4 allowlist check. A segment that matches the venv regex but contains a trailing pipe (e.g. `& .venv/Scripts/Activate.ps1 | iex`) does NOT match because `\s*$` requires only whitespace until end-of-string. The trailing `| iex` prevents the match. **No blind spot. ✓**

7. **Single-pipe bypass**: `_split_segments` splits on `;`, `&&`, `||` only — NOT on `|`. Therefore `& .venv/Scripts/Activate.ps1 | Invoke-Expression` is ONE segment. The venv regex fails (trailing `| Invoke-Expression` breaks `\s*$`), Stage 3 catches `\binvoke-expression\b`. **Secure. ✓**

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| FIX-034 Developer suite (40 tests) | Unit/Security/Regression | PASS | All 40 pass |
| FIX-034 Tester edge-case suite (17 tests) | Security | PASS | All 17 pass |
| FIX-033 regression (17 tests) | Regression | PASS | 0 regressions |
| FIX-023 regression | Regression | PASS | 0 regressions |
| SAF-020 regression | Regression | PASS | 0 regressions |
| FIX-032 regression | Regression | PASS | 0 regressions |
| Full cross-WP suite (294 tests) | Regression | PASS | 294 passed / 0 failed |

---

## Edge-Case Test Details (TST-2095 to TST-2111)

| ID | Command | Expected | Rationale |
|----|---------|----------|-----------|
| TST-2095 | `source .venv/bin/activate ; rm -rf /` | DENY | Venv ok; `rm /` fails zone-check |
| TST-2096 | `& .venv/Scripts/Activate.ps1 ; Invoke-Expression "malicious"` | DENY | P-12 explicit long-form |
| TST-2097 | `source ../../.venv/bin/activate` | DENY | Traversal escapes workspace |
| TST-2097b | `& ../../.venv/Scripts/Activate.ps1` | DENY | PS form traversal |
| TST-2098 | `source .venv\u202e/bin/activate` | DENY | Unicode RLO breaks separator match |
| TST-2099a | `  source .venv/bin/activate  ` | ALLOW | `strip()` normalises padding |
| TST-2099b | `source   .venv/bin/activate` | ALLOW | `\s+` allows multiple spaces |
| TST-2100 | `& ./malicious.ps1` | DENY | Not venv; `&` not in allowlist |
| TST-2100b | `& project/scripts/setup.ps1` | DENY | Not a venv path |
| TST-2101 | `source .venv/bin/activate.ps1` | DENY | `.ps1` invalid under `bin/`; P-22 fires |
| TST-2102 | `source .venv/bin/activate ; source .venv/bin/activate` | ALLOW | Same-form double activation |
| TST-2103 | `& .venv/Scripts/Activate.ps1 \| Invoke-Expression` | DENY | `\|` not a segment split; P-12 fires |
| TST-2104 | `source .venv\x00/bin/activate` | DENY | Null byte breaks `[/\\]` match |
| TST-2105a | `source .venv2/bin/activate` | DENY | Numeric suffix after `venv` not matched |
| TST-2105b | `source .venv_project/bin/activate` | DENY | Underscore suffix not matched |
| TST-2106 | `& C:/evil/.venv/Scripts/Activate.ps1` | DENY | Absolute path outside workspace |
| TST-2107 | `source project/setup.sh` | DENY | P-22 fires on non-venv file |

---

## Bugs Found

None. All attack vectors tested are correctly denied by the implementation.

---

## TODOs for Developer

None.

---

## Verdict

**PASS** — Mark FIX-034 as Done.

All acceptance criteria met:
- `.\Project\venv\Scripts\activate` and all standard forms allowed when inside project
- `& .venv/Scripts/Activate.ps1` PowerShell form allowed
- Activation outside project folder denied
- No false positives from P-22 (`source`) or P-23 (POSIX dot-source)
- Path traversal attacks denied
- Malicious chained commands denied
- No regressions in FIX-033, FIX-023, SAF-020, FIX-032
