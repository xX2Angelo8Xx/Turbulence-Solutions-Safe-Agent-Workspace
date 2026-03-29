# SAF-055 — Test Report: Whitelist .github/ agent-facing subdirectories read-only

## Verdict: PASS ✅

**Date:** 2026-03-30  
**Tester:** Tester Agent  
**Branch:** `SAF-055/github-read-whitelist`  
**WP Status:** → Done

---

## Test Summary

| Run | Tests | Passed | Failed | Notes |
|-----|-------|--------|--------|-------|
| SAF-055 developer suite | 41 | 41 | 0 | All developer tests |
| SAF-055 tester edge-cases | 33 | 33 | 0 | Tester-added coverage |
| Full regression suite | 7,018 | 6,908 | 75 | 75 failures are pre-existing (identical to `main` baseline) |

**Total SAF-055 tests:** 74 (41 developer + 33 tester)  
**SAF-055 pass rate:** 100%  
**Regressions introduced by SAF-055:** 0

---

## Requirements Verification (US-060 Acceptance Criteria)

| Criterion | Verified | Test(s) |
|-----------|----------|---------|
| `read_file` on `.github/agents/` → allow | ✅ | `test_read_file_agents_allowed` |
| `read_file` on `.github/skills/` → allow | ✅ | `test_read_file_skills_allowed` |
| `read_file` on `.github/prompts/` → allow | ✅ | `test_read_file_prompts_allowed` |
| `read_file` on `.github/instructions/` → allow | ✅ | `test_read_file_instructions_allowed` |
| `list_dir` on those four dirs → allow | ✅ | `TestListDirAllowedSubdirs` (4 tests) |
| `create_file` on allowed dirs → deny | ✅ | `test_create_file_agents_denied` |
| `edit_file` on allowed dirs → deny | ✅ | `test_edit_file_prompts_denied` |
| `.github/hooks/` fully denied (read + write) | ✅ | `TestHooksFullyDenied` (4 tests) |
| `.github/instructions/copilot-instructions.md` specifically allowed | ✅ | `test_read_file_copilot_instructions_allowed`, `test_read_alias_copilot_instructions_allowed` |

---

## Bug References (dev-log)

| Bug | Status |
|-----|--------|
| BUG-138: `copilot-instructions.md` wasting Block 1 | Fixed — instructions/ now whitelisted |
| BUG-139: Skill files inaccessible | Fixed — skills/ now whitelisted |

---

## Code Review

**File changed:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

The implementation is correct and well-structured:

1. **`_READ_ONLY_TOOLS`** — narrow frozenset (`read_file`, `Read`, `list_dir`). Write tools are handled earlier by `validate_write_tool()` and never reach this code path. Defense-in-depth is explicit.

2. **`_GITHUB_READ_ALLOWED_RE`** — compiled regex `(?:^|/)\.github/(?:agents|skills|prompts|instructions)(?:/|$)` correctly:
   - Handles both relative and absolute paths
   - Uses `(?:/|$)` to prevent prefix matching (`.github/agents-extra` doesn't match `.github/agents`)
   - The `.github/hooks/` alternative is NOT present — hooks remain blocked

3. **Path traversal defense** — `normalize_path()` resolves `..` before the regex check. Verified with three traversal test cases (agents→hooks, skills→hooks, instructions→.vscode).

4. **Placement in `decide()`** — The SAF-055 block is positioned after `validate_write_tool()` (so write tools never reach it) and after zone/workspace-root checks (last resort before global deny). Correct ordering.

5. **Integrity hash** — `_KNOWN_GOOD_GATE_HASH` has been updated (SAF-025 hash sync tests all pass).

---

## Security Analysis

### Attack Vectors Tested

| Attack | Expected | Result | Test |
|--------|----------|--------|------|
| Path traversal: `.github/agents/../hooks/security_gate.py` | deny | ✅ deny | `test_traversal_via_agents_to_hooks` |
| Path traversal via skills: `.github/skills/../../.github/hooks/` | deny | ✅ deny | `test_traversal_via_skills_to_hooks` |
| Double traversal to `.vscode`: `.github/instructions/../../.vscode/settings.json` | deny | ✅ deny | `test_double_traversal_denied` |
| Backslash traversal: `.github\agents\..\hooks\security_gate.py` | deny | ✅ deny | `test_backslash_traversal_to_hooks_denied` |
| Prefix extension: `.github/agents-extra/foo.md` | deny | ✅ deny | `test_agents_extra_prefix_not_matched` |
| Write tool on allowed path: `create_file .github/agents/evil.md` | deny | ✅ deny | `test_create_file_agents_denied` |
| Non-read tool: `edit_notebook_file .github/instructions/` | deny | ✅ deny | `test_edit_notebook_instructions_denied` |
| Case variation: `.GitHub/agents/` | allow (normalize lowercases) | ✅ allow | `test_uppercase_github_agents_allowed` |
| Case variation: `.GITHUB/HOOKS/` | deny | ✅ deny | `test_uppercase_hooks_still_denied` |
| WSL prefix: `/mnt/c/workspace/.github/hooks/` | deny | ✅ deny | `test_wsl_mount_prefix_hooks_denied` |
| Git Bash prefix: `/c/workspace/.github/hooks/` | deny | ✅ deny | `test_git_bash_prefix_hooks_denied` |
| Null byte injection: `.github/hooks/\x00sg.py` | deny | ✅ deny | `test_null_byte_injected_hooks_still_denied` |
| Empty path | deny | ✅ deny | `test_empty_path_denied` |
| Unknown `grep_search` tool on `.github/agents/` | deny | ✅ deny | `test_grep_search_agents_denied` |
| `file_search` with query=`.github/agents/foo.md` | deny | ✅ deny | `test_file_search_query_github_denied` |
| `get_errors` with filePaths=[`.github/agents/`] | deny | ✅ deny | `test_get_errors_file_paths_github_denied` |

### Finding: URL-Encoded Path Behavior (BUG-150)

**Severity:** Low  
**Introduced by SAF-055?** No — pre-existing SAF-046 behavior

When a path is URL-encoded (e.g., `%2egithub%2fhooks%2fsecurity_gate.py`), `normalize_path()` does not URL-decode it. The encoded string becomes a single-component filename at the workspace root (no forward slashes after URL encoding), which `is_workspace_root_readable()` passes because the token is not in `_DENY_DIRS`.

**Impact:** None in practice. The OS has no file named `%2egithub%2fhooks%2fsecurity_gate.py`, so any `read_file` call would fail with "file not found". No data exfiltration is possible.

**Logged as:** BUG-150. Suggested fix: apply `urllib.parse.unquote()` in `normalize_path()` before zone classification. Not a blocker for SAF-055.

---

## Test Files

| File | Tests | Description |
|------|-------|-------------|
| `tests/SAF-055/test_saf055_github_read_whitelist.py` | 41 | Developer-written: all four allowed subdirs, write denied, hooks denied, traversal, constants |
| `tests/SAF-055/test_saf055_tester_edge_cases.py` | 33 | Tester-added: case variants, backslash paths, WSL/Git Bash prefixes, correct tool payloads, copilot-instructions.md, malformed paths, regex boundary conditions |

---

## Pre-Existing Test Failures (not caused by SAF-055)

75 pre-existing failures exist on `main` and are unchanged on this branch. None are related to SAF-055. Sample affected WPs: FIX-039, FIX-042, FIX-049, INS-004, INS-014, INS-015, INS-017, INS-019, MNT-002, SAF-010, SAF-025 (pycache side-effect).

---

## Pre-Done Checklist

- [x] `docs/workpackages/SAF-055/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-055/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-055/` with tests (41 + 33 = 74 tests)
- [x] All test results logged via `scripts/add_test_result.py` (TST-2235, TST-2236, TST-2237)
- [x] `scripts/validate_workspace.py --wp SAF-055` returns clean (exit 0)
- [x] No `tmp_` files in WP folder or test folder
