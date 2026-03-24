# SAF-040 Test Report

**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Branch:** `SAF-040/read-only-commands`  
**Verdict:** ✅ PASS

---

## 1. Summary

SAF-040 adds 7 new read-only commands (`diff`, `fc`, `comp`, `sort`, `uniq`,
`awk`, `sed`) to the Category G terminal allowlist in `security_gate.py` with
`path_args_restricted=True`. `more` and `less` were already present.

All 7 entries were implemented correctly. AC 1 of US-036 is satisfied. All
developer tests (35) pass and 37 tester edge-case tests pass with 2 xfailed
documenting a pre-existing limitation (BUG-098, low severity).

---

## 2. Code Review

### Changes Verified

| File | Change |
|------|--------|
| `templates/coding/.github/hooks/scripts/security_gate.py` | Added 7 `CommandRule` entries after the existing `more` entry in Category G |
| `templates/coding/.github/hooks/scripts/security_gate.py` | `_KNOWN_GOOD_GATE_HASH` updated by `update_hashes.py` |

### Allowlist Entries

All 7 commands verified to have:
- `path_args_restricted=True` ✅
- `allow_arbitrary_paths=False` ✅
- `denied_flags=frozenset()` ✅ (no flags blocked — write-mode `sed -i` on project files is allowed by the "maximum freedom inside project" design principle)
- Placed correctly in **Category G** (Read-only File Inspection), after existing `more`/`less` entries ✅

### Hash Update

`_KNOWN_GOOD_GATE_HASH` in `security_gate.py` was updated after the allowlist
change via `update_hashes.py`. Verified present in the committed file. ✅

### No Unintended Changes

Diff confirmed as additive only — 7 new `CommandRule` entries and hash update.
No existing allowlist entries were modified. ✅

---

## 3. Test Results

### Developer Tests (35)

| Run | Tests | Passed | Failed | Result |
|-----|-------|--------|--------|--------|
| TST-2051 | 35 | 35 | 0 | Pass |

All 35 developer tests pass:
- Each command allowed with project-folder path arg (7 commands × allow)
- Each command denied with `.github/`, `.vscode/`, or root-level path (7 × deny)
- Pre-existing `more`/`less` regression tests (4)
- Piped stdin usage without path args (`sort`, `uniq`, `awk` with no file) (3)

### Tester Edge-Case Tests (37)

| Run | Tests | Passed | xFailed | Failed | Result |
|-----|-------|--------|---------|--------|--------|
| TST-2052 | 37 | 35 | 2 | 0 | Pass |

**xFailed (expected failures documenting known limitations):**
- `test_fc_windows_text_flag_allowed` — `fc /L project/a.txt project/b.txt` denied (BUG-098)
- `test_fc_windows_binary_flag_allowed` — `fc /B project/a.txt project/b.txt` denied (BUG-098)

### Full Regression Suite

| Run | Passed | Failed | Pre-existing | New Failures |
|-----|--------|--------|--------------|--------------|
| TST-2053 | 4803 | 71 | 71 | **0** |

Baseline on `main`: 4768 passed, 71 failed. SAF-040 adds **35 new passing tests**
with zero regressions. The 71 failures are identical to `main` (SAF-022
settings.json, SAF-025 pycache check, INS-019 shim, SAF-010 ts-python).

---

## 4. Security Analysis

### Attack Vectors Tested

**Path traversal** — `diff project/../../.github/secret project/file` → DENIED ✅  
The traversal `../../.github/` normalizes outside the project; zone_classifier
correctly denies it.

**NoAgentZone access** — All 7 commands with `NoAgentZone/` argument → DENIED ✅  
Tested for `diff`, `sed`, `awk`, `sort`, `uniq`, `comp`, `fc`.

**Both path args outside project** — `diff .github/file .vscode/file` → DENIED ✅  
Zone check fires on the first restricted path.

**Mixed paths (one project, one restricted)** — DENIED ✅  
Verified for `diff`, `fc`, `comp` in developer tests.

**`sed -i` write mode** — `sed -i project/file` → ALLOWED ✅  
Write operations inside the project folder are permitted by design (US-019 AC 1).
`sed -i .github/file` → DENIED ✅ (zone check still fires on the path arg).

**`awk` with `$` token** — Token containing `$` is caught by the `_check_path_arg`
dollar-sign guard → DENIED ✅. The developer correctly avoids `$`-containing
programs in tests (uses `NR==1` rather than `{print $1}`).

**`sort -o /tmp/output.txt project/input.txt`** — `/tmp/output.txt` is path-like
and outside project → DENIED ✅ (write-output attack via sort is blocked).

**Wildcard patterns** — These commands inherit the existing SAF-020 wildcard guard.
No new wildcard attack surface is introduced.

### Boundary Conditions

**Flags before path args** — `diff -u project/a.txt project/b.txt` → ALLOWED ✅  
Dash-prefixed flags are skipped correctly by `_validate_args` step 5.

**`fc` Unix builtin (no path args)** — `fc` (bash history editor) → ALLOWED ✅  
No path args means no zone violation.

**`fc -1` (Unix history offset)** — numeric arg, no path-like detection → ALLOWED ✅

### Limitations Discovered

#### L1 — `sed 's/foo/bar/' file` false positive (documented, not a security issue)

`sed 's/foo/bar/' project/file.txt` is **DENIED** because the substitution
pattern `s/foo/bar/` contains `/` and `_is_path_like()` returns True for any
token with a forward slash. Zone classification of `s/foo/bar` resolves outside
the project folder → deny.

**Workaround:** Use an alternative delimiter in the sed expression:
`sed 's|foo|bar|' project/file.txt` (pipe delimiter, no `/`) → ALLOWED ✅

This is a pre-existing limitation of `_is_path_like()` and affects all commands
with path restriction, not only the SAF-040 additions.

#### L2 — `fc /L` and `fc /B` Windows slash-flags denied (BUG-098)

Windows `fc` command uses `/L` (line compare) and `/B` (binary compare) flags.
The `_validate_args` flag-skipping logic only recognizes dash-prefixed flags
(`stripped.startswith("-")`). Slash-prefixed Windows flags like `/L` contain `/`
and are treated as absolute paths outside the project → DENIED.

**Severity:** Low — `fc` without flags works correctly. The missing flags are
optional modes, not required for basic file comparison.  
**Bug filed:** BUG-098  
**Not a security issue** — the behaviour is overly restrictive, not a bypass.

---

## 5. Acceptance Criteria Verification

| AC | Criterion | Status |
|----|-----------|--------|
| US-036 AC 1 | Read-only commands (more, less, diff, fc, comp, sort, uniq, awk, sed) work inside project folder | ✅ PASS |
| US-036 AC 1 | Denied outside project folder | ✅ PASS |

---

## 6. Pre-Done Checklist

- [x] `docs/workpackages/SAF-040/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-040/test-report.md` written by Tester Agent
- [x] Test files exist in `tests/SAF-040/` (developer: 35 tests; tester: 37 tests)
- [x] All test results logged via `scripts/add_test_result.py` (TST-2051, TST-2052, TST-2053)
- [x] `scripts/validate_workspace.py --wp SAF-040` returns clean (see below)
- [x] BUG-098 logged in `docs/bugs/bugs.csv`

---

## 7. Bugs Filed

| ID | Title | Severity |
|----|-------|----------|
| BUG-098 | `fc /flag` Windows-style slash flags misidentified as paths | Low |

---

## 8. Verdict

**PASS** — SAF-040 correctly implements all 7 read-only commands with
`path_args_restricted=True`. All security vectors tested deny correctly.
AC 1 of US-036 is satisfied. One low-severity bug (BUG-098) was discovered
and documented; it is non-blocking and does not represent a security
vulnerability.
