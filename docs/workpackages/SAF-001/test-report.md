# Test Report — SAF-001

**Tester:** Tester Agent
**Date:** 2026-03-10
**Iteration:** 2

---

## Summary

**PASS — WP set to Done.**

All four blocking issues from Iteration 1 are resolved. `security_gate.py` and `test_saf001_security_gate.py` exist as committed source files. `dev-log.md` is present. `query` and `pattern` are not in `_PATH_FIELDS`. All 96 tests pass (36 INS-001/INS-002 + 60 SAF-001). No regressions. The security gate is correct, fail-closed, and exits 0 unconditionally.

---

## Pre-flight Checks

| Check | Result | Evidence |
|---|---|---|
| `Default-Project/.github/hooks/scripts/security_gate.py` exists as `.py` source | **PASS** | File read in full; committed to git (not in `git status --short`) |
| `tests/test_saf001_security_gate.py` exists as `.py` source | **PASS** | 60 tests collected and run by pytest |
| `docs/workpackages/SAF-001/dev-log.md` exists | **PASS** | File read; Iteration 2 section present |
| `query` and `pattern` NOT in `_PATH_FIELDS` | **PASS** | `_PATH_FIELDS = ("filePath", "file_path", "path", "directory", "target")` — confirmed |
| Null-byte sanitization in `normalize_path` | **PASS** | `p = p.replace("\x00", "")` is first operation in `normalize_path` |
| Stdin size guard | **PASS** | `_STDIN_MAX_BYTES = 1_048_576`; fail-closed if `len(raw) >= _STDIN_MAX_BYTES` |

---

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| Full suite — 96 tests (pytest tests/ -v) | Regression | **PASS** | 96/96 in 0.54 s; Windows 11 + Python 3.11 |
| TST-033 to TST-081 (49 core SAF-001 tests) | Unit/Security/Integration | **PASS** | All green on live source |
| TST-093 to TST-103 (11 Tester edge cases) | Security/Cross-platform | **PASS** | All green |
| INS-001 regression suite (23 tests) | Regression | **PASS** | No regressions |
| INS-002 regression suite (13 tests) | Regression | **PASS** | No regressions |

**Logged as:** TST-118 in `docs/test-results/test-results.csv`

---

## Code Review — security_gate.py

### Fail-closed behaviour ✓
- `main()` wraps the entire logic in `try/except Exception → deny + exit 0`. No exception can escape without a deny response.
- `parse_input()` returns `None` for any parse failure (malformed JSON, JSON null, non-dict); `main()` converts `None` to `deny`.
- Oversized stdin (`len(raw) >= _STDIN_MAX_BYTES`) immediately returns `deny` before parsing.

### Exit 0 guarantee ✓
- `sys.exit(0)` is called in two locations: inside `main()` after the normal flow, and unconditionally at the script's bottom level (after `if __name__ == "__main__": main()`).
- The `except Exception` branch explicitly calls `sys.exit(0)` through the outer unconditional call.
- Confirmed by `test_integration_exit_code_always_zero`: tested across 4 inputs including empty, malformed, null, and valid.

### Zone classification ✓
- **allow**: `project/` (Method 1 first-segment match; Method 2 `_ALLOW_PATTERN`)
- **deny**: `.github/`, `.vscode/`, `noagentzone/` (Method 1 first-segment match against `_BLOCKED_NAMES`; Method 2 `_BLOCKED_PATTERN` for cross-root and mismatched-root cases)
- **ask**: everything else (default)
- Dual-method defense ensures sibling-prefix bypass (`project-evil/.github/x`) is caught by Method 2 when Method 1's first-segment is `project-evil` (not in blocked set, not `project`).

### Path traversal protection ✓
- `posixpath.normpath()` is applied after backslash normalization, lowercasing, and WSL/Git-Bash prefix conversion.
- Null bytes stripped before all other normalization.
- `..` components resolved before zone classification.
- Confirmed: `project/../../../../.github/x` → `deny` (TST-103).

### False-positive fix (`query`/`pattern`) ✓
- `_PATH_FIELDS` contains only: `filePath`, `file_path`, `path`, `directory`, `target`.
- `grep_search(query=".github/secret", filePath="project/main.py")` → `allow` (path is `project/main.py`; query ignored).
- Confirmed by TST-097.

### Terminal tool scanning ✓
- Full JSON payload serialized, `\\\\` and `\\` normalized, lowercased, then scanned for `.github`, `.vscode`, `noagentzone`.
- Catches mixed-case (`.GITHUB`), JSON-escaped backslashes.

### Always-allow set ✓
- `vscode_ask_questions`, `ask_questions`, `TodoWrite`, `TodoRead`, `todo_write`, `manage_todo_list`, `runSubagent`, `search_subagent`, `Agent`, `agent` bypass all zone checks. Correct: these tools don't access file paths.

### Known limitations (documented, within scope)

| Limitation | Impact | Deferred To |
|---|---|---|
| `ws_root` derived from `os.getcwd()` — may be wrong if VS Code changes directory before hook invocation | Zone decisions could be incorrect if cwd ≠ workspace root | Future iteration |
| Non-exempt / unknown tools return `ask` even for blocked-zone paths | Blocked-zone access requires user approval rather than automatic deny | Acceptable: `ask` is still a security control; known tool list covers all standard VS Code tools |
| Symlinks inside `project/` pointing to blocked zones are not detected | Pure string-based analysis cannot follow symlinks | SAF scope limitation |
| `grep_search` / `semantic_search` parameter validation (`includePattern`, `includeIgnoredFiles`) not implemented | Search tools could be used to index protected files | SAF-003 |

---

## Bugs Found

No new bugs. BUG-003 and BUG-004 confirmed closed.

---

## Verdict

**PASS**

SAF-001 is complete and correct. All 60 tests pass. All four blocking TODOs from Iteration 1 are resolved. The implementation is fail-closed, exits 0 unconditionally, uses dual-method zone detection, handles path traversal, null bytes, UNC paths, oversized stdin, and cross-platform path formats. Known limitations are documented and scoped to future WPs.

WP status set to `Done`.

---

## Previous Iteration

### Iteration 1 — FAIL (2026-03-10)

The Iteration 1 test report (FAIL) content is preserved below for record.

---

**FAIL — Returned to Developer.**

SAF-001 cannot be accepted in its current state. The primary deliverable (`security_gate.py`) and the test file (`test_saf001_security_gate.py`) are both **missing from the repository**. Only compiled `.pyc` cache files exist, proving the code was written and executed locally but was **never committed to git**. Additionally, the `dev-log.md` is absent, the WP status was never updated from `Open` to `Review`, and the 49 test results logged in `docs/test-results/test-results.csv` (TST-033 to TST-081) **cannot be reproduced** — the test suite only collects 32 tests (INS-001 and INS-002). No SAF-001 tests are runnable.

**Blocking TODOs (all resolved in Iteration 2):**
- BLOCKING-1: Restore `security_gate.py` source — **RESOLVED**
- BLOCKING-2: Restore `tests/test_saf001_security_gate.py` source — **RESOLVED**
- BLOCKING-3: Create `dev-log.md` — **RESOLVED**
- BLOCKING-4: Set WP status to `Review` — **RESOLVED**
- REQUIRED-1: Remove `query` and `pattern` from `_PATH_FIELDS` — **RESOLVED**
- REQUIRED-2: Add null-byte sanitization test + fix — **RESOLVED**
- REQUIRED-3: Add UNC path tests — **RESOLVED**
- REQUIRED-4: Add stdin size guard — **RESOLVED**

---

## Summary

**FAIL — Returned to Developer.**

SAF-001 cannot be accepted in its current state. The primary deliverable (`security_gate.py`) and the test file (`test_saf001_security_gate.py`) are both **missing from the repository**. Only compiled `.pyc` cache files exist, proving the code was written and executed locally but was **never committed to git**. Additionally, the `dev-log.md` is absent, the WP status was never updated from `Open` to `Review`, and the 49 test results logged in `docs/test-results/test-results.csv` (TST-033 to TST-081) **cannot be reproduced** — the test suite only collects 32 tests (INS-001 and INS-002). No SAF-001 tests are runnable.

---

## Investigation Results

### File State

| Expected File | Status | Evidence |
|---|---|---|
| `Default-Project/.github/hooks/scripts/security_gate.py` | **MISSING** | Only `__pycache__/security_gate.cpython-311.pyc` exists |
| `tests/test_saf001_security_gate.py` | **MISSING** | Only `tests/__pycache__/test_saf001_security_gate.cpython-311-pytest-9.0.2.pyc` exists |
| `docs/workpackages/SAF-001/dev-log.md` | **MISSING** | SAF-001 folder was empty |
| WP status = `Review` in workpackages.csv | **MISSING** | Status field shows `Open` |

### Git State

`git log --oneline -20` shows no SAF-001 commit exists. The most recent commit is `c3bdbfd` (`INS-002`). No branch for SAF-001 was created or merged.

### Test Suite Run — 2026-03-10

```
platform win32 -- Python 3.11.9, pytest-9.0.2
collected 32 items

tests/test_ins001_structure.py  [22 tests — PASSED]
tests/test_ins002_packaging.py  [10 tests — PASSED]

32 passed in 0.17s
```

**No SAF-001 tests were collected.** The 49 test results logged as "Pass" in `test-results.csv` (TST-033 to TST-081) are **unverified and unrunnable**.

---

## Implementation Analysis (from .pyc bytecode)

Despite the missing source file, the compiled bytecode was inspected via `dis`/`marshal` to assess what was implemented. This analysis is informational only — it cannot substitute for code review of the source.

### Functions Identified in `security_gate.cpython-311.pyc`

`build_response`, `parse_input`, `extract_tool_name`, `extract_path`, `normalize_path`, `get_zone`, `decide`, `main`

### Positive Findings (from bytecode)

| Requirement | Observed Behaviour |
|---|---|
| Fail closed on error | `main()` wraps entire logic in `try/except Exception → deny`. `parse_input()` returns `None` on any parse failure, triggering deny. |
| Always exits with code 0 | `sys.exit(0)` called unconditionally at end of `main()`. |
| No external dependencies | Module-level imports: `__future__`, `json`, `os`, `posixpath`, `re`, `sys`, `typing` — stdlib only. |
| Cross-platform path normalization | `normalize_path()` handles: JSON-escaped `\\`, single `\`, WSL `/mnt/c/`, Git Bash `/c/`, lowercases, strips trailing `/`, applies `posixpath.normpath`. |
| Path traversal via `..` resolved | `posixpath.normpath` is applied after backslash conversion and lowercasing. `..` components are resolved before zone classification. |
| Dual-method zone detection | `get_zone()` uses Method 1 (prefix-strip → first-segment check against `_BLOCKED_NAMES`) AND Method 2 (regex scan of `/`-anchored full path) for defense in depth. |
| Terminal tool scanning | `decide()` serialises full JSON to string, normalises, and regex-scans for `.github`, `.vscode`, `noagentzone` before making any zone decision. |
| stdout flush | `print(..., flush=True)` used. |

### Security Concerns Identified (from bytecode + analysis)

These issues **must be addressed before the WP can pass**:

#### CONCERN 1 — `query` and `pattern` treated as paths (False Positive / Semantic Error)

`_PATH_FIELDS = ('filePath', 'file_path', 'path', 'directory', 'pattern', 'target', 'query')`

The `query` field is extracted for tools such as `grep_search` and `semantic_search`. These fields contain **search strings**, not file system paths. If an agent legitimately calls `grep_search(query=".github/commit-branch-rules.md")`, the security gate would extract `.github/commit-branch-rules.md` as a "path", run `get_zone()` on it, classify it as `deny`, and block the call — even though no protected file was accessed.

This is both:
- A **false positive** that degrades usability
- A potential **bypass**: an attacker who knows this behaviour could craft a `grep_search` query to trigger a deny and obscure what they are actually attempting in a separate tool call

`query` and `pattern` should be removed from `_PATH_FIELDS`. Search-content validation belongs in SAF-003.

#### CONCERN 2 — Null byte in path bypasses first-segment check

A path like `project\x00.github/secret` would normalize to `project\x00.github/secret` (null byte preserved by `lower()` and `posixpath.normpath`). The first-segment after splitting on `/` is `project\x00.github`, which is **not** in `_BLOCKED_NAMES`. Method 2 (pattern scan on `/project\x00.github/secret`) checks `'/(\\.github|\\.vscode|noagentzone)(/|$)'`. The `\x00` precedes `.github` but the regex looks for `/.github` so the pattern **would match** and the path would be denied.

The pattern fallback appears to save this case, but it is not explicitly tested. A dedicated test must be written.

#### CONCERN 3 — UNC paths not normalized

Windows UNC paths (`\\\\server\\share\\.github\\file`) would be normalized to `//server/share/.github/file` (after backslash conversion). `posixpath.normpath` converts `//server/share/.github` to `/server/share/.github` (double leading slash collapses to single). The first-segment would be `server` (not in `_BLOCKED_NAMES`). Method 2 (pattern) would match `/.github/` and return deny. Coverage is incidental, not deliberate, and needs an explicit test.

#### CONCERN 4 — Very large stdin input — no resource guard

`sys.stdin.read()` reads the entire stdin into memory. No size limit is applied. A crafted input of several megabytes could cause excessive memory use. While VS Code hook invocations are bounded in practice, this should be documented as a known limitation or guarded with a read limit.

#### CONCERN 5 — Relative path prepension uses `os.getcwd()` not workspace root from config

`ws_root = normalize_path(os.getcwd())` — the workspace root is derived from the current working directory at the time the hook runs. If the VS Code extension or hook executor changes directory before invoking the script, `ws_root` will be wrong and zone decisions will be incorrect. The root should ideally be derived from the hook input or a stable config source.

---

## Tests Executed

| Test | Type | Result | Notes |
|---|---|---|---|
| Full test suite (32 tests: INS-001 + INS-002) | Unit / Integration / Security | PASS | No regressions |
| SAF-001 test suite (49 tests, TST-033 to TST-081) | All | BLOCKED | Test source file missing; tests cannot be collected |
| Manual: pytest --collect-only | N/A | FAIL | 0 SAF-001 tests collected |
| git log for SAF-001 commit | Process | FAIL | No SAF-001 commit found |

---

## Bugs Found

- **BUG-003**: `security_gate.py` source file missing from repository — only compiled `.pyc` cache exists (logged in `docs/bugs/bugs.csv`)
- **BUG-004**: `tests/test_saf001_security_gate.py` source file missing from repository — only compiled `.pyc` cache exists (logged in `docs/bugs/bugs.csv`)

---

## TODOs for Developer

### Blocking (must resolve before re-submitting for review)

- [ ] **Restore `security_gate.py`**: Commit source file to `Default-Project/.github/hooks/scripts/security_gate.py`. The `.pyc`-only state means VS Code hooks cannot be distributed and the code cannot be code-reviewed or tested.
- [ ] **Restore `tests/test_saf001_security_gate.py`**: Commit source file to `tests/test_saf001_security_gate.py`. Without this, SAF-001 tests are not runnable and TST-033 to TST-081 in the CSV are unverified.
- [ ] **Create `docs/workpackages/SAF-001/dev-log.md`**: The dev-log is mandatory for handoff (agent-workflow Step 6). Create it documenting what was implemented, decisions made, tests written, and known limitations.
- [ ] **Set WP status to `Review` before handoff**: The workpackages.csv must show `Review` status when the WP is handed off. Currently shows `Open`.
- [ ] **Verify TST-033 to TST-081 are reproducible**: Re-run the full test suite after restoring source files and confirm all 49 SAF-001 tests pass. Update test-results.csv with a new dated run.

### Required Fixes (before re-submitting for review)

- [ ] **Remove `query` and `pattern` from `_PATH_FIELDS`**: These are search-content fields, not file paths. Extracting them for zone classification causes false positives on legitimate `grep_search` calls. Search parameter validation is SAF-003's responsibility.
- [ ] **Add null-byte path test**: Add `test_null_byte_in_path` — a path containing `\x00` before a blocked segment. Must confirm deny is returned and document which method (1 or 2) catches it.
- [ ] **Add UNC path test**: Add `test_unc_path_windows` — a Windows UNC path `\\\\server\\share\\.github\\file` must be denied. Document normalization behavior.
- [ ] **Add resource guard or document limitation for large stdin**: Either limit `stdin.read()` to a reasonable maximum (e.g., 1 MB) and fail-closed if exceeded, or document this as a known limitation in `dev-log.md`.

### Edge-Case Tests to Add (new tests beyond the Developer's 49)

- [ ] `test_null_byte_in_path` — Security — `filePath = "project\x00/../.github/x"` must return `deny`
- [ ] `test_unc_path_always_denied` — Cross-platform — `\\\\server\\share\\.github\\secret` must return `deny`
- [ ] `test_unc_path_project_asks` — Cross-platform — `\\\\server\\share\\project\\file` returns `ask` (pattern fallback for allow also needs test)
- [ ] `test_very_large_input_fails_closed` — Security — 2 MB garbage stdin must return `deny` within reasonable time
- [ ] `test_query_field_not_treated_as_path` — Security — `grep_search` with `query=".github/secret"` should NOT be auto-denied based on query content (once `query` is removed from `_PATH_FIELDS`)
- [ ] `test_empty_tool_name` — Unit — `tool_name = ""` falls through to non-exempt → `ask`
- [ ] `test_tool_name_not_string` — Security — `tool_name = 42` must not raise; must return `ask` or `deny` (fail closed)
- [ ] `test_ws_root_with_trailing_slash` — Unit — workspace root ending in `/` is handled correctly by `get_zone()`
- [ ] `test_response_hookSpecificOutput_exact_structure` — Integration — allow response has `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}`, deny/ask responses additionally include `permissionDecisionReason`
- [ ] `test_decide_project_sibling_prefix_bypass` — Security — path `project-evil/.github/x` must not match `project` zone and must be denied by pattern fallback
- [ ] `test_normalize_deep_traversal` — Security — `project/../../../../.github` normalizes and is denied

---

## Verdict

**FAIL — Return to Developer.**

The primary deliverable and test file are missing from the repository. No SAF-001 code can be reviewed or tested. The WP was never properly committed or handed off. All blocking TODOs above must be resolved before re-review. At re-review, the full test suite (32 existing + 49 SAF-001 + the 11 additional edge-case tests listed above = minimum 92 total) must pass.
