# SAF-015 Test Report — Expand Terminal Allowlist: Write Commands

## Verdict: PASS

| Field | Value |
|-------|-------|
| WP ID | SAF-015 |
| Tester | Tester Agent |
| Test Date | 2026-03-16 |
| Branch | `SAF-015/terminal-write-commands` |

---

## 1. Implementation Review

### Code Changes Verified

**`Default-Project/.github/hooks/scripts/security_gate.py`**
- Category M block (lines 607–678) was added before the closing `}` of `_COMMAND_ALLOWLIST`.
- All 10 new entries confirmed present: `set-content`, `sc`, `add-content`, `ac`, `out-file`, `rename-item`, `ren`, `tee-object`, `tee`, `ni`.
- All entries use `path_args_restricted=True` and `allow_arbitrary_paths=False` — correct.

**`templates/coding/.github/hooks/scripts/security_gate.py`**
- Identical Category M block confirmed present — template kept in sync.

**Category J commands (pre-existing)**
- `mkdir`, `new-item`, `cp`, `copy`, `copy-item`, `mv`, `move`, `move-item` — all confirmed present in Category J with `path_args_restricted=True`.
- Developer correctly noted these were already there; adding them again would have been a duplicate, not a gap.

### WP Description Check

The WP description lists: `rename-item`/`ren`/`mv`/`move-item`, `copy-item`/`cp`/`copy`, `new-item`/`ni`/`mkdir`, `tee-object`, `tee`, `set-content`/`sc`, `add-content`/`ac`, `out-file`.

Every listed alias is present in the allowlist (some pre-existing in Category J, new ones in Category M). **No missing entries.**

---

## 2. Test Results Summary

| Run | Scope | Pass | Fail | Skip | Notes |
|-----|-------|------|------|------|-------|
| Developer tests (Tester re-run) | `tests/SAF-015/test_saf015_write_commands.py` | 72 | 0 | 0 | All pass |
| Tester edge-case tests | `tests/SAF-015/test_saf015_edge_cases.py` | 57 | 0 | 0 | All pass |
| Full regression (post edge-case additions) | `tests/` | 2409 | 8 | 29 | 8 failures all pre-existing |

**Pre-existing failures (not caused by SAF-015):**
- `tests/FIX-009/` × 6 — UnicodeDecodeError reading test-results.csv (BUG-045, pre-existing)
- `tests/INS-005/test_ins005_edge_cases.py::test_uninstall_delete_type_is_filesandirs` — pre-existing
- `tests/SAF-008/test_saf008_integrity.py::test_verify_file_integrity_passes_with_good_hashes` — integrity hash not regenerated (pending SAF-025)

---

## 3. Edge-Case Tests Added by Tester

**File:** `tests/SAF-015/test_saf015_edge_cases.py` (57 tests)

| Area | Tests | Findings |
|------|-------|----------|
| Category J — `move-item` direct | 4 | PASS — both-in-project allowed; any outside denied |
| Category J — `cp` direct | 3 | PASS — source-or-dest outside denied |
| Category J — `copy` direct | 2 | PASS |
| Category J — `mkdir` direct | 3 | PASS |
| Category J — `new-item` direct | 2 | PASS |
| Piped write commands | 6 | PASS — `_split_segments` does NOT split on `\|`; all path tokens in the pipeline segment are zone-checked by the leading verb's `_validate_args` call. Deny-zone path in pipe tail is correctly denied. |
| PowerShell named params (`-Path`, `-FilePath`, `-Destination`) | 8 | PASS — Named param values are zone-checked because they are non-flag tokens following the `-Flag` token |
| Flags (`-Force`, `-Append`, `-Encoding`, `-a`) with project paths | 6 | PASS — Flags (starting with `-`) are skipped; path tokens are still zone-checked |
| Quoted paths with spaces | 4 | PASS — `shlex` correctly strips quotes; zone check fires on the unquoted path |
| Redirect operators (`>`, `>>`) | 3 | PASS — redirect targets zone-checked by existing BUG-013/BUG-016 guard |
| Mixed-case / all-uppercase verbs | 6 | PASS — case-insensitive via `.lower()` normalization |
| `copy-item` asymmetric src/dest | 3 | PASS — both `src-in-project+dest-outside` and `src-outside+dest-in-project` denied |
| `ni -ItemType Directory` | 2 | PASS — `-ItemType` is a flag (skipped), path token is zone-checked |
| `tee-object -Variable` (no file path) | 2 | PASS — `-Variable myvar` has no path-like token; correctly allowed. With deny-zone `-FilePath` → denied. |
| Path traversal on Category J commands | 3 | PASS — `..` traversal resolved by `posixpath.normpath` before zone classification |

---

## 4. Security Analysis

### Attack Vectors Evaluated

1. **Pipe injection** (`get-content safe.txt | set-content .github/evil.txt`): Denied — the zone check on all path-like tokens in the segment catches the destination path even though it follows a `|` that is not a segment delimiter.

2. **Named parameter bypass** (`set-content -Path .github/evil.txt -Value data`): Denied — the `-Path` token is skipped as a flag, but `.github/evil.txt` is the next positional token and is zone-checked.

3. **Flag bypass** (`set-content -Force .github/evil.txt data`): Denied — `-Force` is skipped; `.github/evil.txt` is zone-checked.

4. **Quoted paths** (`set-content '.github/hooks/evil.txt' bad`): Denied — `shlex` strips the surrounding quotes; zone check fires on the unquoted path.

5. **Embedded redirect** (`set-content project/f.txt>.github/evil.txt`): Denied — the embedded redirect BUG-013/BUG-016 guard extracts the right-side of `>` and zone-checks it.

6. **Path traversal** (`set-content project/../.github/evil.txt data`): Denied — `posixpath.normpath` resolves `..` before classification.

7. **Variable injection** (`set-content $HOME/.bashrc evil`): Denied — `$` in any token is an immediate deny.

8. **All-caps verb bypass** (`SET-CONTENT .github/evil.txt bad`): Denied — verb is lowercased before allowlist lookup; zone check still fires.

### No Security Gaps Found

All attempted bypass patterns are correctly blocked by existing `_validate_args` infrastructure. No new logic was required — the existing path restriction mechanism works correctly for all new Category M entries.

---

## 5. Pre-Done Checklist

- [x] `docs/workpackages/SAF-015/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-015/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-015/` (2 files: 72 Developer tests + 57 Tester edge-case tests)
- [x] All test runs logged in `docs/test-results/test-results.csv` (TST-1356 through TST-1370)
- [x] No new regressions introduced

---

## 6. Final Verdict

**PASS** — SAF-015 is complete and correct. All write commands were added to the allowlist with appropriate `path_args_restricted=True` enforcement. All aliases mentioned in the WP description are present. The existing `_validate_args` infrastructure correctly handles multi-path commands, flags, named parameters, piped commands, quoted paths, and traversal attempts without any additional logic changes.

WP status set to `Done`.
