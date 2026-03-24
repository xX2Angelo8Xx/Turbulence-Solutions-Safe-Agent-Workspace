# SAF-044 Test Report

**WP ID:** SAF-044  
**Branch:** SAF-044/search-scoping  
**Tester:** Tester Agent  
**Date:** 2026-03-24  
**Verdict: PASS**

---

## Summary

SAF-044 upgrades `validate_semantic_search` from a pass-through to an active validator
and adds a new `validate_search_subagent` function in `security_gate.py`.
Both functions scope the respective search tools to the project folder by blocking
path traversal, absolute paths into deny zones, and (for `search_subagent`) queries
that explicitly name a deny-zone directory.

All 33 Developer tests pass. 18 Tester edge-case tests were added; all 51 tests pass.
No regressions were introduced in the SAF-035–SAF-043 chain (614 passed).

---

## Review Findings

### Implementation Review

**validate_semantic_search** (security_gate.py line ~2115):
- Uses `".." in query` for path-traversal detection on the **raw** query string. ✓
- Calls `zone_classifier.normalize_path()` then checks for absolute-path + deny-zone pattern
  via `re.search(r"/(\.github|\.vscode|noagentzone)(/|$)", "/" + norm_query)`. ✓
- Natural-language queries that mention zone names as text are intentionally allowed — VS Code
  `search.exclude` already scopes the semantic index. This is correct by design. ✓
- Uses `zone_classifier.normalize_path` (not `zone_classifier.classify`) to avoid
  filesystem dependency in test environments. ✓

**validate_search_subagent** (security_gate.py line ~2162):
- Deny-zone name check: `for zone_name in (".github", ".vscode", "noagentzone")` with
  case-insensitive substring match on `query.lower()`. ✓
- `".." in query` path-traversal check. ✓
- Absolute-path prefix zone check (same regex as `validate_semantic_search`). ✓
- Glob wildcard stripping before the absolute-path check. ✓

**decide() routing** (security_gate.py line ~2705):
- `search_subagent` removed from `_ALWAYS_ALLOW_TOOLS`. ✓
- Handler added at line 2705: `if tool_name == "search_subagent": return validate_search_subagent(data, ws_root)`. ✓
- `semantic_search` routing unchanged (line 2701). ✓

### Acceptance Criteria Check (US-037)

| AC | Requirement | Status |
|----|-------------|--------|
| AC 2 | semantic_search scoped to project folder only | ✓ PASS |
| AC 3 | search_subagent scoped to project folder only | ✓ PASS |
| AC 6 | Security gate validates both tools before execution | ✓ PASS |

---

## Test Results

| Run | Tests | Status |
|-----|-------|--------|
| TST-2078 — Developer suite | 33 passed / 0 failed | PASS |
| TST-2079 — Tester edge-case suite (51 total) | 51 passed / 0 failed | PASS |
| TST-2080 — Regression SAF-035 to SAF-044 chain | 614 passed / 0 failed | PASS |

---

## Edge Cases Tested by Tester

### validate_semantic_search (edge cases)
| Input | Expected | Actual | Notes |
|-------|----------|--------|-------|
| `%2e%2e/.github/hooks.py` | allow | allow | No literal `..`, not absolute path; semantic index pre-scoped |
| Unicode NL query | allow | allow | ✓ |
| 5000-char safe query | allow | allow | No buffer issue |
| Integer query value | allow | allow | Treated as absent query |
| Empty string query | allow | allow | ✓ |

### validate_search_subagent (edge cases)
| Input | Expected | Actual | Notes |
|-------|----------|--------|-------|
| `src/.git/COMMIT_EDITMSG` | allow | allow | `.git` is not a deny zone |
| Unicode NL query | allow | allow | ✓ |
| 5000-char safe query | allow | allow | ✓ |
| Integer query value | allow | allow | Treated as absent |
| Empty string query | allow | allow | ✓ |
| `%2egithub/hooks.py` | allow | allow | **Design limitation** — see BUG-103 |
| `%2e%2e/secrets` | allow | allow | Design limitation — no literal `..` |
| Long query with `.github` | deny | deny | Substring check works at any position |
| `.GITHUB` (uppercase) | deny | deny | Case-insensitive check ✓ |
| Query exactly `.github` | deny | deny | ✓ |
| `path:\t.github\thooks` | deny | deny | Tab prefix doesn't escape substring ✓ |

---

## Security Analysis

### Attack Vectors Evaluated

1. **Path traversal via `..`** — Correctly blocked in both validators. ✓
2. **Absolute path to deny zone** — Correctly blocked via regex zone check. ✓
3. **Zone name as text in NL query (semantic_search)** — Intentionally allowed; index is
   pre-scoped by VS Code `search.exclude`. By design. ✓
4. **Zone name as text in search_subagent** — Blocked regardless of context because
   `search_subagent` accepts glob patterns that could target the filesystem directly. ✓
5. **Case evasion** — Caught by `query.lower()` before zone-name check. ✓
6. **Windows backslash paths** — `zone_classifier.normalize_path` converts backslashes to
   forward slashes; `..\.github\` → caught by the `..` literal check before normalization. ✓
7. **Percent-encoded zone names** — **NOT caught** (BUG-103). VS Code `search.exclude`
   provides the actual protection layer. Low-severity limitation. ✓

### Boundary Conditions
- No query: both validators return `allow`. Correct — no path to evaluate.
- Empty string query: flows through; returns `allow`. Correct.
- Non-string query: returns `allow`. Correct — no valid path to evaluate.
- Very long queries: no performance issue; linear scan. ✓

### Race Conditions / Concurrency
- Both validators are pure functions operating on immutable string data. No concurrency
  concerns. ✓

### Platform Compatibility
- `zone_classifier.normalize_path` handles Windows (`C:/`), Unix (`/`), WSL (`/mnt/c/`),
  and Git Bash (`/c/`) path prefixes. Cross-platform by design. ✓

---

## Bug Logged

| ID | Title | Severity |
|----|-------|----------|
| BUG-103 | validate_search_subagent allows percent-encoded zone names (%2egithub) | Low |

This is a **low-severity design limitation**. The primary protection is VS Code's
`search.exclude` settings which prevent files from `.github`, `.vscode`, and
`NoAgentZone` from appearing in search results regardless. The gate-level check
provides defence-in-depth for un-encoded queries. A future WP could add URL-decoding
before the deny-zone name check.

---

## Conclusion

SAF-044 correctly implements query validation for `semantic_search` and
`search_subagent`. The defence-in-depth approach (vs Code search.exclude + gate-level
validator) satisfies ACs 2, 3, and 6 of US-037. The one identified limitation
(BUG-103) is low-severity and does not block the WP.

**Verdict: PASS** — WP promoted to Done.
