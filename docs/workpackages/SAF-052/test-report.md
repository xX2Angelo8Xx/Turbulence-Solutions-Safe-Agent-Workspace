# SAF-052 Test Report

**WP ID:** SAF-052  
**Name:** Add get_changed_files to security gate tool sets  
**Branch:** SAF-052/get-changed-files  
**Tester:** Tester Agent  
**Test Date:** 2026-03-26  
**Verdict:** PASS

---

## Summary

SAF-052 adds `"get_changed_files"` to the `_ALWAYS_ALLOW_TOOLS` frozenset in
`templates/agent-workbench/.github/hooks/scripts/security_gate.py` and updates
the `_KNOWN_GOOD_GATE_HASH` constant accordingly.

The implementation is minimal, correct, and correctly placed. All 25 tests pass
(12 developer, 13 tester edge-cases). No regressions detected in security-gate
related test suites.

---

## Code Review

### Change 1 — `security_gate.py`

- `"get_changed_files"` added to `_ALWAYS_ALLOW_TOOLS` with comment `# SAF-052`.
- Placement is correct: `_ALWAYS_ALLOW_TOOLS` is checked first in `decide()`; tools
  in this set bypass all zone checks and return `"allow"` immediately.
- `get_changed_files` has no path arguments susceptible to zone-check bypass abuse.
- `_KNOWN_GOOD_GATE_HASH` updated to `efb12c39547fa322c4e869fc9c888625c40c34185e927344dbd806ec95159576`.
- Hash independently verified: computed hash matches embedded constant. ✓

### Change 2 — `tests/SAF-052/test_saf052_get_changed_files.py`

- 12 tests across 5 classes: membership, `decide()` return value, set placement,
  hash integrity, and unknown-tool regression guard.
- All tests pass.

### Change 3 — `docs/bugs/bugs.csv` — BUG-132 marked Fixed. ✓

### Change 4 — `docs/workpackages/workpackages.csv` — SAF-052 → Review. ✓

### Change 5 — `docs/test-results/test-results.csv` — TST-2227 logged by Developer. ✓

---

## Tests Run

| Test Run ID | Scope | Type | Result | Notes |
|-------------|-------|------|--------|-------|
| TST-2228 | Full suite (--full-suite) | Regression | 6841 passed, 72 failed | 72 failures are pre-existing (confirmed on stash) |
| TST-2229 | SAF-052 targeted suite | Unit | 25 passed | All developer + edge-case tests |

---

## Edge Cases Tested (Tester-Added)

| Test | Class | Finding |
|------|-------|---------|
| `GET_CHANGED_FILES` (all-caps) | Case sensitivity | Correctly denied — frozenset lookup is exact |
| `Get_Changed_Files` (mixed case) | Case sensitivity | Correctly denied |
| `"get_changed_files "` (trailing space) | Whitespace | Correctly denied |
| `" get_changed_files"` (leading space) | Whitespace | Correctly denied |
| Not in `_EXEMPT_TOOLS` | Set placement | Correct — only in `_ALWAYS_ALLOW_TOOLS` |
| `frozenset.add()` raises | Immutability | Correctly raises AttributeError |
| `repositoryPath` pointing outside workspace | Zone bypass analysis | Returns `allow` — expected, zone checks skipped for always-allow |
| Path-traversal string in `repositoryPath` | Zone bypass analysis | Returns `allow` — correct, always-allow tier |
| `sourceControlState` with valid filters | Input variation | All return `allow` |
| `None` as tool_name | Null input | Handled gracefully — does not crash |
| Unicode characters in `tool_input` | Input variation | Returns `allow` |
| 4096-char `repositoryPath` | Large input | Returns `allow` |
| `templates/coding` absent | Stale parallel gate | Confirmed absent — no second gate to update |

---

## Security Analysis

**Concern: Always-allow bypasses zone checks for `repositoryPath`**  
`_ALWAYS_ALLOW_TOOLS` provides an early exit in `decide()` before any path validation.
A payload `{"tool_name": "get_changed_files", "tool_input": {"repositoryPath": "/etc"}}` 
returns `"allow"`. This is **intentional and acceptable** because:
1. `get_changed_files` is a read-only VS Code API (lists git-modified files).
2. The `repositoryPath` value is passed to the VS Code engine, not executed as a shell command.
3. No file content is read or written by this tool.
4. The tool does not traverse paths itself — it queries the VS Code git extension.

**Concern: Set mutability**  
`_ALWAYS_ALLOW_TOOLS` is a `frozenset` (confirmed). An attacker cannot modify it at runtime
via `.add()`. Confirmed by edge-case test `test_immutable_always_allow_frozenset`.

**Concern: Parallel `templates/coding` gate**  
Confirmed absent. No out-of-sync gate file exists.

---

## Pre-Existing Failures (not caused by SAF-052)

The following 72 failures are present on the base branch (confirmed by running with stash):
- `tests/SAF-025/test_saf025_hash_sync.py::test_no_pycache_in_templates_coding` — `__pycache__` created when tests import from templates directory
- `tests/SAF-010/test_saf010_hook_config.py` — hooks use `ts-python`, tests expect `python`
- `tests/INS-019/` — installer shim tests failing
- `tests/FIX-039/`, `tests/FIX-042/`, `tests/FIX-049/`, `tests/INS-014/`, `tests/INS-015/`, `tests/INS-017/`, `tests/MNT-002/` — various pre-existing failures

None of these failures are related to or caused by SAF-052.

---

## Verdict: PASS

All acceptance criteria met:
- [x] `get_changed_files` is in `_ALWAYS_ALLOW_TOOLS`
- [x] `decide({"tool_name": "get_changed_files"}, ws_root)` returns `"allow"`
- [x] Hash updated and verified independently
- [x] Unknown tools still denied (regression guard passes)
- [x] No regressions in security-gate test suites
- [x] Edge-case tests added and passing
- [x] BUG-132 marked Fixed
- [x] `validate_workspace.py --wp SAF-052` returns exit code 0
