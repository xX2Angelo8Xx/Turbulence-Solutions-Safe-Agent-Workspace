# Test Report — SAF-063: Add tool name normalization to security gate

## Verdict: PASS

## Date
2026-04-01

## Tester
Tester Agent

---

## Scope

Reviewed and tested the implementation that:
1. Adds `vscode_askQuestions` (camelCase) to `_ALWAYS_ALLOW_TOOLS`
2. Adds 13 more tool names to `_ALWAYS_ALLOW_TOOLS`
3. Adds `insert_edit_into_file` to `_WRITE_TOOLS` and `_EXEMPT_TOOLS` with `decide()` routing
4. Adds `edit_notebook_file` and `create_new_jupyter_notebook` to `_WRITE_TOOLS`
5. Adds `view_image`, `edit_notebook_file`, `create_new_jupyter_notebook`, `read_notebook_cell_output`, `run_notebook_cell` to `_EXEMPT_TOOLS`
6. Updates `require-approval.sh` and `require-approval.ps1` always-allow regexes
7. Updates TST-416 in `tests/SAF-007/` to reflect intentional behaviour change
8. Updates `_KNOWN_GOOD_GATE_HASH` via `update_hashes.py`

---

## Code Review

### security_gate.py
- `vscode_askQuestions` correctly placed in `_ALWAYS_ALLOW_TOOLS` alongside the existing `vscode_ask_questions` (snake_case backward-compat entry).
- All 13 new always-allow tool names are in the frozenset with appropriate comments.
- `insert_edit_into_file` is in both `_WRITE_TOOLS` and `_EXEMPT_TOOLS`. The `decide()` routing at line 3210 handles it before the generic `_WRITE_TOOLS` check — functionally identical but explicitly documented.
- `edit_notebook_file` and `create_new_jupyter_notebook` are in both `_WRITE_TOOLS` and `_EXEMPT_TOOLS` — correct; write tools that also appear in `_EXEMPT_TOOLS` are handled by the `_WRITE_TOOLS` branch first (lines 3213–3214), which calls `validate_write_tool()`.
- `view_image`, `read_notebook_cell_output`, `run_notebook_cell` are in `_EXEMPT_TOOLS` only — these are read-only tools, correct.
- `_KNOWN_GOOD_GATE_HASH` was updated after all edits — hash integrity tests pass.

### require-approval.sh / require-approval.ps1
- Always-allow regex updated with all 14 new tool names (including `vscode_askQuestions`).
- The `EXEMPT_REGEX` in these shell scripts was NOT updated with the new notebook tools (`insert_edit_into_file`, `view_image`, etc.). This is intentional scoping: the shell scripts are a fast first-pass layer; `security_gate.py` is the authoritative Python gate. New exempt tools that are not in the shell `EXEMPT_REGEX` will return "ask" from the shell script, which causes VS Code to invoke the Python gate for a more precise decision. Security posture is preserved (fail-safe).

### require-approval.sh regex
The always-allow regex now covers 21 tool names including both `vscode_askQuestions` (camelCase) and `vscode_ask_questions` (snake_case). Verified line 121.

### TST-416 update in SAF-007
The comment and assertion were correctly updated to reflect that `edit_notebook_file` is now a write tool (zone-checked) rather than an unknown tool. The test logic itself remains correct — project path allowed, outside path denied.

---

## Test Execution

### Test suite: `tests/SAF-063/` — 50 tests
**Result: 50 passed, 0 failed**

Developer tests (22):
- `vscode_askQuestions` camelCase: allowed + in frozenset ✓
- `vscode_ask_questions` snake_case backward compat ✓
- All 13 new always-allow tool names in frozenset and `decide()` returns allow ✓
- `insert_edit_into_file` allowed in project zone (mocked) ✓
- `insert_edit_into_file` denied outside project ✓
- `insert_edit_into_file` denied with no path (fail-closed) ✓
- `insert_edit_into_file` in `_WRITE_TOOLS` ✓
- `view_image` in `_EXEMPT_TOOLS`, allowed in project zone ✓
- `edit_notebook_file` in `_WRITE_TOOLS` and `_EXEMPT_TOOLS`, denied outside ✓
- `create_new_jupyter_notebook` in `_WRITE_TOOLS` and `_EXEMPT_TOOLS` ✓
- `read_notebook_cell_output` in `_EXEMPT_TOOLS` ✓
- `run_notebook_cell` in `_EXEMPT_TOOLS` ✓
- Unknown tools denied ✓
- Unknown camelCase tools denied (bypass prevention) ✓

Tester edge cases (28):
- `run_notebook_cell` + project zone: allowed ✓
- `run_notebook_cell` + deny zone: denied ✓
- `run_notebook_cell` + docs zone: denied ✓
- `run_notebook_cell` + no path: fail-closed ✓
- `read_notebook_cell_output` + project zone: allowed ✓
- `read_notebook_cell_output` + deny zone: denied ✓
- `read_notebook_cell_output` + no path: fail-closed ✓
- `view_image` + deny zone: denied ✓
- `view_image` + non-project zone: denied ✓
- `view_image` + no path: fail-closed ✓
- `insert_edit_into_file` + `.github` zone: denied ✓
- `insert_edit_into_file` + docs zone: denied ✓
- `insert_edit_into_file` + project zone: allowed ✓
- `edit_notebook_file` + no path: fail-closed ✓
- `edit_notebook_file` + `.github` zone: denied ✓
- `edit_notebook_file` + project zone: allowed ✓
- `create_new_jupyter_notebook` + no path: fail-closed ✓
- `create_new_jupyter_notebook` + `.github` zone: denied ✓
- `create_new_jupyter_notebook` + project zone: allowed ✓
- `create_new_jupyter_notebook` + docs zone: denied ✓
- New always-allow tools not in `_WRITE_TOOLS` (4 checks) ✓
- `_WRITE_TOOLS` ∩ `_ALWAYS_ALLOW_TOOLS` = ∅ ✓
- `_TERMINAL_TOOLS` ∩ `_ALWAYS_ALLOW_TOOLS` = ∅ ✓
- `insert_edit_into_file` not in `_ALWAYS_ALLOW_TOOLS` ✓
- `run_in_terminal` not in `_ALWAYS_ALLOW_TOOLS` ✓

### Regression: `tests/SAF-007/` — 54 tests
**Result: 54 passed, 0 failed**
TST-416 updated correctly; all prior write-restriction tests still pass.

### All SAF tests (SAF-001 through SAF-063, excluding SAF-053/054 which don't exist)
**Result: PASS** (no regressions in any SAF workpackage)

---

## Security Analysis

### Attack vectors considered

1. **CamelCase tool name injection for bypass**: Tested — only explicitly listed camelCase names (`vscode_askQuestions`) are allowed. `runInTerminal` (camelCase of `run_in_terminal`) is denied. Confirmed by `test_camel_case_variant_of_terminal_tool_denied`.

2. **Write tool auto-allow bypass**: `_WRITE_TOOLS ∩ _ALWAYS_ALLOW_TOOLS = ∅` verified — no write tool can slip past zone checking by appearing in the always-allow set.

3. **`insert_edit_into_file` to sensitive zones**: Denied for `.github`, `docs/`, and any non-project zone. Only Project/ writes allowed.

4. **Fail-closed on missing path**: All new tools (notebook tools, `insert_edit_into_file`) return "deny" when no `filePath` is present in the payload.

5. **`run_notebook_cell` security**: Not in `_WRITE_TOOLS` (correct — it doesn't write files at the OS level via this gate). However it is zone-checked via the exempt path, so executing a notebook in `.github/` would be denied.

6. **Tool name set exhaustiveness**: All 14 new names verified in the correct classification set.

7. **Hash integrity**: `_KNOWN_GOOD_GATE_HASH` updated. Integrity tests pass (SAF-008 tests).

### Observations (non-blocking)

- The shell scripts' `EXEMPT_REGEX` was not updated with new notebook/insert_edit tools. This is a safe gap: unrecognised exempt-zone tools fall through to "ask" in the shell, then Python gate decides authoritatively. Security posture maintained.
- `copilot_getNotebookSummary` (camelCase) is in `_ALWAYS_ALLOW_TOOLS`. It is NOT in `_WRITE_TOOLS`, which is correct — it is a read-only notebook metadata tool.

---

## Pre-Done Checklist

- [x] `docs/workpackages/SAF-063/dev-log.md` exists and is non-empty
- [x] `docs/workpackages/SAF-063/test-report.md` written by Tester
- [x] Test files exist in `tests/SAF-063/` with 50 tests across 2 files
- [x] Test results logged via `scripts/add_test_result.py` (TST-2390)
- [x] `scripts/validate_workspace.py --wp SAF-063` returns exit code 0
- [x] All tests pass (50/50 SAF-063; SAF-001 through SAF-063 clean; SAF-007 regression clean)
- [ ] `git add -A` and commit/push — pending (next step)
