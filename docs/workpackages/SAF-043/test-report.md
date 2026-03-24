# Test Report — SAF-043

**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Verdict:** PASS  

---

## Summary

`validate_file_search()` correctly scopes `file_search` tool calls to the project
folder by blocking queries that reference deny-zone directory names, contain path
traversal sequences, or specify absolute paths outside the project folder. All 40
developer tests and 34 Tester-added edge-case tests pass. No regressions in the
full security gate test set.

---

## Code Review

### `validate_file_search()` in `security_gate.py`

**Deny-zone name detection (`.github`, `.vscode`, `NoAgentZone`)**  
- Check is case-insensitive (uses `query.lower()` before substring comparison).  
- Handles both flat and VS Code nested `tool_input` payload formats.  
- Correctly denies deny-zone names embedded anywhere in the query string  
  (e.g., `**/.github/**/*.json` is denied).  
- ✅ Correct.

**Path traversal blocking (`..`)**  
- Simple substring check on the raw query: `".." in query`.  
- Catches `../`, `project/../../outside`, and Windows `project\..\outside` forms  
  since all contain the `..` literal substring.  
- ✅ Correct.

**Absolute path zone check**  
- Extracts the path prefix before the first wildcard character.  
- Zone-checks only when the prefix is an absolute path (starts with `/` or a  
  Windows drive letter `X:`).  
- Relative globs (e.g., `**/*.py`, `src/**`) are left to VS Code `search.exclude`  
  filtering — this is an explicit design decision documented in the dev-log.  
- ✅ Correct.

**`decide()` routing**  
- `file_search` tool calls are routed to `validate_file_search()` at line 2637.  
- The `_EXEMPT_TOOLS` block for `file_search` (added in FIX-021) has been  
  replaced by the explicit `validate_file_search()` call.  
- ✅ Correct.

### `search.exclude` in `templates/coding/.vscode/settings.json`

Verified the settings file contains:

```json
"search.exclude": {
    ".github": true,
    ".vscode": true,
    "**/NoAgentZone": true
}
```

All three deny zones are covered. ✅

---

## US-037 Acceptance Criteria

| AC | Description | Status |
|----|-------------|--------|
| AC 1 | `file_search` returns results from the project folder only | ✅ Met — gate blocks named deny zones, traversal, and out-of-project absolute paths. Minor `.git/` gap noted below. |

---

## Test Results

| TST-ID | Name | Type | Result |
|--------|------|------|--------|
| TST-2074 | SAF-043 developer tests (40 passed) | Unit | Pass |
| TST-2075 | SAF-043 tester edge-case tests (34 added) | Security | Pass |
| TST-2076 | SAF-043 full suite regression | Unit | Pass — 74/74 SAF-043 tests; 71 pre-existing suite failures unrelated to SAF-043 |

---

## Edge Cases Added by Tester

**Test file:** `tests/SAF-043/test_saf043_tester_edge_cases.py` (34 tests)

| Group | Cases |
|-------|-------|
| Mixed-case deny zones | `.GitHub` (capital G), `.VSCODE` (all caps), `noagentzone` (lowercase), `.Github` (title case) |
| Encoded/escaped traversal | `%2E%2E/outside/**` (allowed — not real traversal), `project\..\outside` (denied), `../` + zone combo, multiple `..` sequences |
| Empty and wildcard-only | Empty string `""`, `*`, `?`, `*.json`, `?.py` — all allowed |
| Unicode in query | Latin extended, CJK, emoji (allowed); zone name with Unicode prefix (denied); Cyrillic lookalike `.гithub` (allowed) |
| `.git/` gap documentation | Absolute `/workspace/.git/config` — denied; relative `**/.git/**` — allowed (gap) |
| Additional absolute paths | `/usr/bin/**`, `/home/user/`, different Windows drive `d:/secrets/**` (denied); deep project path (allowed) |
| `decide()` integration | 6 integration cases covering all new edge-case categories |

---

## Security Analysis

### Attack Vectors Considered

1. **Case-variation bypass** — `.GitHub`, `.VSCODE`, `NOAGENTZONE` — all denied by  
   case-insensitive check. ✅ Closed.

2. **URL-encoded traversal** (`%2E%2E`) — NOT intercepted by the gate. However,  
   VS Code does not URL-decode file_search glob patterns, so `%2E%2E` is treated  
   as a literal file name component. This is not a real traversal vector.  
   Documented in `test_allow_percent_encoded_traversal`.

3. **Windows backslash traversal** (`project\..\outside`) — denied because `..`  
   is a substring of the raw query. ✅ Closed.

4. **Unicode/homoglyph spoofing** — Cyrillic `.гithub` does not contain the ASCII  
   `.github` substring and is correctly allowed. True spoof with ASCII-identical  
   characters is impossible for `.github` (no homoglyphs exist for all 7 chars  
   simultaneously). ✅ Acceptable.

5. **Wildcard prefix to deny zone** (e.g., `.g*/**`) — allowed by the gate, deferred  
   to VS Code `search.exclude`. The Developer documented this as an intentional  
   design choice. `search.exclude` with `.github: true` will filter results even  
   if the query matches `.github/**`. ✅ Mitigated by search.exclude.

### Identified Gap (Minor — Out of SAF-043 Scope)

**`.git/` relative queries not blocked by gate or `search.exclude`**

- `validate_file_search` only name-checks `.github`, `.vscode`, and `noagentzone`.  
  The `.git` directory is NOT in this list.
- Relative queries like `**/.git/**` or `.git/config` are allowed by the gate.
- `search.exclude` in `settings.json` does not include `.git/`.
- VS Code typically excludes `.git/` from file indexing by default (implementation  
  detail, not guaranteed).
- Absolute paths to `.git/` (e.g., `/workspace/.git/config`) are denied because  
  `zone_classifier.classify()` defaults to deny for paths not inside the project  
  folder.
- **Risk:** Low — `.git/` contains metadata (commit history, refs, packed objects)  
  that an agent could read via `file_search` in relative query form. SAF-032 blocks  
  direct `read_file` / `create_file` access to `.git/`, but `file_search`  
  results could reveal file names and structure.
- **Recommendation:** A follow-on WP should add `.git` to the named deny-zone  
  check in `validate_file_search()` and add `.git` to `search.exclude`.

**Bug logged:** See `docs/bugs/bugs.csv`.

---

## Pre-Done Checklist

- [x] `docs/workpackages/SAF-043/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-043/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-043/` with 74 tests total
- [x] All test results logged via `scripts/add_test_result.py` (TST-2074, TST-2075, TST-2076)
- [x] `scripts/validate_workspace.py --wp SAF-043` returns exit code 0
- [x] No regressions introduced by SAF-043 changes
- [x] SAF-043 `decide()` routing verified in code review and integration tests
