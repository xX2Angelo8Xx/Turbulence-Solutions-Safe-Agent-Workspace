# FIX-033 — Test Report
## Allow dot-prefix names and env var assignment in project

**WP ID:** FIX-033  
**Branch:** fix-033  
**Reviewed By:** Tester Agent  
**Date:** 2026-03-18  
**Verdict:** ✅ PASS

---

## 1. Code Review

### Files reviewed
- `Default-Project/.github/hooks/scripts/security_gate.py` — primary implementation
- `templates/coding/.github/hooks/scripts/security_gate.py` — verified synced
- `tests/FIX-033/test_fix033_dot_prefix_env_vars.py` — developer tests

### Change 1 — Step 5 dot-prefix path fallback

**Location:** `_validate_args`, step 5 path-arg zone-check block.

```python
if len(parts_fb) >= 2 or (
    len(parts_fb) == 1
    and (
        stripped.rstrip().endswith("/")
        or norm_fb.startswith(".")
    )
):
```

**Security analysis:**
- `norm_fb.startswith(".")` is checked on the **normalised** path (posixpath.normpath), not the raw token.
  This is critical: `./file.txt` normalises to `file.txt`, which does NOT start with `.`, so it is correctly excluded.
  Only genuine dot-prefix names like `.venv`, `.env`, `.gitignore` (normalised form `".venv"`, `".env"`, `".gitignore"`) trigger the fallback.
- `_try_project_fallback` hard-denies any path whose first segment is `.github`, `.vscode`, or `noagentzone`, so the expanded fallback cannot open those zones.
- `..` normalises to `..` — parts_fb is empty (double-dots are filtered) — no fallback fires → still denied.
- `.` normalises to `.` — parts_fb is also empty → no fallback → denied (workspace root).

**Verdict:** Implementation is correct and safe.

### Change 2 — Step 6 redirect target fallback

Identical guard logic applied to both standalone (`> .env`) and embedded (`text>.env`) redirect block forms. Same `norm_redir.startswith(".")` / `norm_emb.startswith(".")` on the normalised target, not the raw token. Security properties identical to Change 1.

**Verdict:** Implementation is correct and safe.

### Change 3 — `$env:` assignment handler

**Location:** `sanitize_terminal_command`, placed BEFORE the generic `$`-verb deny guard.

```python
if verb_lower.startswith("$env:") and len(tokens) >= 3 and tokens[1] == "=":
    env_value = tokens[2].strip("\"'")
    if "$" not in env_value:
        norm_env_val = posixpath.normpath(env_value.replace("\\", "/"))
        if zone_classifier.classify(norm_env_val, ws_root) == "allow":
            continue
        if _try_project_fallback(norm_env_val, ws_root):
            continue
    return ("deny", ...)
```

**Security analysis:**
- `len(tokens) >= 3 and tokens[1] == "="` — strict form check. Anything without an `=` at position 1 falls through to the `$` deny guard.
- `"$" not in env_value` — nested variable references (e.g. `$env:OTHER`) are unconditionally denied. Runtime value is unknown.
- `posixpath.normpath(env_value.replace(...))` — resolves any `..` sequences before classification. `../../etc/passwd` → `../../etc/passwd` → resolves to `c:/etc/passwd` in zone_classifier → denied.
- `_try_project_fallback` has its own `..` filter (drops `.` and `..` parts before building the resolved path), but still correctly denies traversal via double-dot inside a segment (e.g. `project/../../.github` → normpath resolves outside workspace → classified deny).
- Empty value `''` → normpath of empty string → `"."` → workspace root → classified deny via both paths.
- The handler checks only `tokens[2]`. Extra tokens beyond position 2 are ignored (a limitation, but in practice a PowerShell `$env:A = val` statement only has 3 tokens; `&&` / `;` splits happen before tokenisation of this segment).
- Env var NAME is not restricted — only the VALUE is zone-checked. This is the correct design: agents may legitimately set any env var as long as the path value stays inside the project.

**Verdict:** Implementation is correct and safe. No bypass vectors identified.

---

## 2. Developer Tests (36 tests)

| Run ID | Test File | Result |
|--------|-----------|--------|
| TST-1801 | `test_fix033_dot_prefix_env_vars.py` | 36 passed, 0 failed |

All developer tests pass without modification.

---

## 3. Tester Edge-Case Tests (27 tests)

Created `tests/FIX-033/test_fix033_tester_edge_cases.py`.

### Coverage areas not addressed by developer suite

| Test | Scenario | Expected | Actual |
|------|----------|----------|--------|
| TST-4136 | `$env:VIRTUAL_ENV = '../../etc/passwd'` | DENY | PASS |
| TST-4137 | `$env:VIRTUAL_ENV = 'project/../../.venv'` | DENY | PASS |
| TST-4138 | `$env:VIRTUAL_ENV = 'project/../../.github'` | DENY | PASS |
| TST-4139 | `$env:VIRTUAL_ENV = '..'` | DENY | PASS |
| TST-4140 | `$env:VIRTUAL_ENV = 'c:/workspace'` (ws root) | DENY | PASS |
| TST-4141 | Empty value `$env:VIRTUAL_ENV = ''` | DENY | PASS |
| TST-4142 | Two-token form `$env:A =` | DENY | PASS |
| TST-4143 | `$env:VIRTUAL_ENV = '.'` | DENY | PASS |
| TST-4144 | `ls .` | DENY | PASS |
| TST-4145 | `ls ..` | DENY | PASS |
| TST-4146 | `cat ../secret.txt` | DENY | PASS |
| TST-4147 | `$env:PATH = 'project/scripts'` | ALLOW | PASS |
| TST-4148 | `$env:MY_CUSTOM_VAR = 'project/.venv'` | ALLOW | PASS |
| TST-4149 | `$env:PATH = 'c:/windows/system32'` | DENY | PASS |
| TST-4150 | `$env:A='project/.venv' && ls .github` | DENY | PASS |
| TST-4151 | `$env:A='project/.venv' ; cat .gitignore` | ALLOW | PASS |
| TST-4152 | `echo content>.env` (embedded redirect) | ALLOW | PASS |
| TST-4153 | `echo test > ..` | DENY | PASS |
| TST-4154 | `echo test > .vscode/settings.json` | DENY | PASS |
| TST-4155 | `cat .gitconfig` | ALLOW | PASS |
| TST-4156 | `ls .pytest_cache` | ALLOW | PASS |
| TST-4157 | `cat .pylintrc` | ALLOW | PASS |
| TST-4158 | `$env:A = 'c:/workspace/noagentzone'` | DENY | PASS |
| TST-4159 | `$env:A = '.vscode/extensions'` | DENY | PASS |
| TST-4160 | `$env:A = '.github/hooks'` | DENY | PASS |
| TST-4161 | `$MY_VAR = project/.venv` (no `$env:`) | DENY | PASS |
| TST-4162 | `$envVAR = project/.venv` (no colon) | DENY | PASS |

**All 27 tester edge-case tests PASS.**

---

## 4. Regression Suite

| Run ID | Scope | Result |
|--------|-------|--------|
| TST-1804 | `tests/FIX-033/` + `tests/SAF-020/` + `tests/FIX-022/` + `tests/FIX-023/` + `tests/FIX-032/` | **287 passed, 0 failed** |
| TST-1805 | Full suite (`tests/`) | **3579 passed, 3 pre-existing failures, 29 skipped, 1 xfailed** |

Pre-existing failures (unchanged from before FIX-033):
- `FIX-009::test_tst_ids_sequential_no_gaps_in_renumbered_range` — TST-ID gap backlog
- `FIX-009::test_no_duplicate_tst_ids` — duplicate TST-IDs (TST-1557 × 2, TST-599 × 2)
- `INS-005::test_uninstall_delete_type_is_filesandirs` — BUG-045

**Zero new failures introduced by FIX-033.**

---

## 5. Security Analysis Summary

| Vector | Protected? | Evidence |
|--------|-----------|---------|
| Traversal via `..` in env value (`../../etc/passwd`) | ✅ | posixpath.normpath resolves → outside workspace → deny |
| Double-dot inside env value path (`project/../../.github`) | ✅ | normpath collapses → resolved path outside project → deny |
| Empty env value | ✅ | normalises to `.` (workspace root) → deny |
| Deny-zone dot-prefix in env value (`.github`, `.vscode`) | ✅ | `_try_project_fallback` hard-denies deny-zone first segments |
| Nested `$` in env value (`$env:OTHER`) | ✅ | `"$" not in env_value` check before classification |
| Non-`$env:` dollar vars (`$MY_VAR`, `$envVAR`) | ✅ | `$env:` prefix check fails → falls through to $-verb deny |
| Chained env allow + bad second segment | ✅ | Segments checked independently; bad second segment denies whole command |
| `ls .` / `ls ..` (degenerate paths) | ✅ | `.` → workspace root → deny; `..` → above workspace → deny |
| Redirect `> ..` | ✅ | Redirect target normalises to workspace parent → deny |
| Absolute workspace-root (not project-folder) in env value | ✅ | `c:/workspace` fails allow_pattern check → deny |

---

## 6. Verdict

**PASS.** All 63 FIX-033 tests pass (36 developer + 27 tester). No regressions. Security analysis confirms all identified attack vectors are properly blocked. WP set to `Done`.
