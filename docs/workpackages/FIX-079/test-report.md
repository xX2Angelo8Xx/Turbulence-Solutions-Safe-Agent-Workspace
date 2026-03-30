# FIX-079 Test Report — Show NoAgentZone in VS Code File Explorer

**WP ID:** FIX-079  
**Tester:** Tester Agent  
**Date:** 2026-03-30  
**Verdict:** PASS  

---

## Summary

FIX-079 removes `**/NoAgentZone` from `files.exclude` in
`templates/agent-workbench/.vscode/settings.json` so the folder is visible
in the VS Code file explorer. The entry is preserved in `search.exclude`
to prevent VS Code search (and agent `grep_search` / `file_search` tools)
from indexing its contents. Integrity hashes in `security_gate.py` were
updated after the settings.json change.

All implementation requirements from US-064 are satisfied and BUG-146 is
correctly fixed.

---

## Requirements Traceability

| Acceptance Criterion (US-064) | Status | Evidence |
|-------------------------------|--------|---------|
| NoAgentZone removed from `files.exclude` | PASS | `test_noagentzone_not_in_files_exclude`, `test_files_exclude_has_exactly_github_and_vscode` |
| NoAgentZone remains in `search.exclude` | PASS | `test_noagentzone_in_search_exclude`, `test_search_exclude_noagentzone_value_is_strict_bool_true` |
| Security gate zone enforcement still denies agent access | PASS | `test_noagentzone_zone_deny_direct_path`, `test_noagentzone_zone_deny_nested_path`, gate tool deny tests |

---

## Code Review Findings

### `templates/agent-workbench/.vscode/settings.json`

- `files.exclude` now contains exactly `.github` and `.vscode` — NoAgentZone entry correctly removed.
- `search.exclude` contains `.github`, `.vscode`, and `**/NoAgentZone` — unchanged.
- File is valid JSON with no trailing commas.
- No other settings changed (chat tools, security trust, MCP settings all intact).
- File size is 1.1 KB — consistent with expected content.

### `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

- Only the hash constants changed — no security logic was modified.
- `_KNOWN_GOOD_SETTINGS_HASH` = `1786325dfd2a3e007112c63e0e82c50fe76e1e4e8c022439a6d3597bc2248447` — verified matches actual file.
- `_KNOWN_GOOD_GATE_HASH` = `9d4249569be46f2f6f97ca82afefb2f366c3fe502f321dc991e35146ea60caac` — verified against canonical hash.
- The `zone_classifier.classify()` function and `_DENY_DIRS` set are untouched.

### Updated Regression Tests

- `tests/SAF-022/test_saf022_noagentzone_exclude.py` — updated to assert NoAgentZone is **absent** from `files.exclude` (consistent with FIX-079). All 27 SAF-022 tests pass.
- `tests/SAF-022/test_saf022_edge_cases.py` — `TestExcludeSectionConsistency` updated to allow the intentional NoAgentZone-only-in-search-exclude divergence.
- `tests/SAF-045/test_saf045_grep_search_scoping.py` — `test_settings_files_exclude_noagentzone` and surrounding tests flipped to reflect FIX-079 state. All 53 SAF-045 tests pass.

---

## Test Execution

### Developer Tests (`tests/FIX-079/test_fix079_noagentzone_visible.py`)

| Test | Result |
|------|--------|
| `test_settings_json_is_valid_json` | PASS |
| `test_noagentzone_not_in_files_exclude` | PASS |
| `test_github_still_in_files_exclude` | PASS |
| `test_vscode_still_in_files_exclude` | PASS |
| `test_noagentzone_in_search_exclude` | PASS |
| `test_security_gate_settings_hash_valid` | PASS |
| `test_security_gate_gate_hash_valid` | PASS |
| `test_noagentzone_zone_deny_direct_path` | PASS |
| `test_noagentzone_zone_deny_nested_path` | PASS |

**Result: 9/9 PASS** (TST-2264)

### Tester Edge-Case Tests (`tests/FIX-079/test_fix079_tester_edge_cases.py`)

| Test | Result | Rationale |
|------|--------|-----------|
| `test_settings_json_no_trailing_comma_before_brace` | PASS | Invalid JSON hygiene check |
| `test_files_exclude_has_exactly_github_and_vscode` | PASS | Exact key set — no stray entries |
| `test_files_exclude_contains_no_noagentzone_variant` | PASS | Catches all capitalisation variants |
| `test_search_exclude_noagentzone_value_is_strict_bool_true` | PASS | No truthy-but-wrong type |
| `test_gate_read_file_noagentzone_direct_denied` | PASS | Gate denies read_file to NoAgentZone direct child |
| `test_gate_read_file_noagentzone_nested_denied` | PASS | Gate denies deep read into NoAgentZone |
| `test_gate_create_file_noagentzone_denied` | PASS | Gate denies write to NoAgentZone |
| `test_gate_replace_string_noagentzone_denied` | PASS | Gate denies write override to NoAgentZone |
| `test_zone_classifier_windows_path_noagentzone_denied` | PASS | Backslash paths not a bypass vector |
| `test_zone_classifier_case_insensitive_noagentzone_denied` | PASS | Case variations denied |
| `test_settings_json_not_empty` | PASS | File not accidentally cleared |
| `test_settings_json_roundtrip_stable` | PASS | No hidden byte corruption |

**Result: 12/12 PASS** (TST-2265)

### Regression — SAF-022 and SAF-045

- `tests/SAF-022/` — 27/27 PASS (TST-2266)
- `tests/SAF-045/` — 53/53 PASS (TST-2266)

### Full Test Suite

- 7191 passed, 72 failed (pre-existing), 33 skipped, 3 xfailed
- All 72 failures confirmed pre-existing on `main` branch; none caused by FIX-079.
- FIX-079 changes (`settings.json`, `security_gate.py` hashes, test/tracking files) do not touch any code path relevant to the failing tests.

---

## Security Analysis

| Concern | Finding |
|---------|---------|
| Does removing `files.exclude` give agent read access? | No. `files.exclude` controls explorer visibility only. Security gate zone enforcement is fully independent. |
| Does removing `files.exclude` let agents find NoAgentZone via search tools? | No. NoAgentZone is still in `search.exclude`. `grep_search` and `file_search` with `includePattern: NoAgentZone` are denied at the gate level (SAF-045). |
| Are integrity hashes correct? | Yes. `_KNOWN_GOOD_SETTINGS_HASH` and `_KNOWN_GOOD_GATE_HASH` both verified against actual file content. |
| Is the zone_classifier still effective? | Yes. `_DENY_DIRS` contains `"noagentzone"` (case-normalised). Direct-child, nested, Windows-style, and all-caps paths are all denied. |
| Could a future re-introduction of `files.exclude` bypass security? | No. Security gate is independent of VS Code settings. |

---

## Bugs Found

None. No new bugs introduced.

---

## Verdict

**PASS** — All acceptance criteria met, security posture unchanged, no regressions introduced.
