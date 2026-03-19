# FIX-022 to FIX-027 — Tester Report

**Reviewed by:** Tester Agent  
**Date:** 2026-03-17  
**Branch:** fix/FIX-022-to-027-path-resolution  
**Verdict:** ✅ PASS

---

## Summary

Six workpackages addressing relative-path resolution failures in the security gate were reviewed. FIX-022, FIX-023, and FIX-026 contain code changes. FIX-024, FIX-025, and FIX-027 are investigation-resolved (no code changes required).

The implementation introduces `_try_project_fallback()` and `_PROJECT_FALLBACK_VERBS` to allow read/execute commands with relative project-folder paths, while maintaining hard denials for destructive verbs, deny-zone targets, and wildcard patterns.

---

## Code Review Findings

### FIX-022 — Python/pip/venv terminal commands

**Changes reviewed:**
- `_PROJECT_FALLBACK_VERBS` frozenset: correctly excludes destructive verbs (`rm`, `del`, `erase`, `rmdir`, `remove-item`, `ri`)
- `_try_project_fallback()`: guards for absolute paths, tildes, empty paths, `.`/`..`, and deny-zone components — all correct
- Step 5 length gate: requires ≥2 segments OR single segment with trailing `/` — conservatively safe; trailing backslash `\` is not treated as a directory indicator (shlex/normpath limitation, documented)
- Activation script handler: correctly placed before allowlist lookup; normalises backslash before fallback

**Observations:**
1. `ruff`, `mypy`, `black`, `flake8`, `isort` are listed in `_PROJECT_FALLBACK_VERBS` but are NOT in `_COMMAND_ALLOWLIST`. These entries are dead code — fallback verbs have no effect unless the verb passes the allowlist lookup first. Non-blocking (no security impact), but worth cleaning up in a follow-up.
2. Trailing backslash on activation scripts (`.venv\Scripts\Activate.ps1\` with ADDITIONAL trailing backslash) causes `shlex` parse failure → `deny` via the "Command could not be parsed" path. This is correct safe-fail behaviour.

### FIX-023 — .venv directory creation fallback

**Changes reviewed:**
- Step 4 venv handler: `_step4_validated_indices` correctly skips already-validated venv target indices in step 5 — prevents double-checking
- Backslash venv targets: `.venv\Scripts` normalises correctly via `replace("\\", "/")`

### FIX-026 — get_errors project-folder fallback

**Changes reviewed:**
- `validate_get_errors()`: fallback applied correctly ONLY when `zone_classifier.classify()` returns deny (not on allow)
- All-or-nothing semantics preserved: if ANY path in the `filePaths` array is not fallback-recoverable, the entire call is denied

### FIX-024, FIX-025, FIX-027 — Investigation-resolved

Developer correctly identified that:
- FIX-024: Hash staleness (SAF-008) — no code change needed; running `update_hashes.py` resolves
- FIX-025: `cat`/`type` already in Category G allowlist — root cause was the FIX-022 relative-path issue, now fixed
- FIX-027: Absolute paths via zone_classifier Method 1 (pathlib `relative_to`) work correctly

---

## Security Invariant Verification

All critical MUST-DENY cases confirmed:

| Command | Expected | Actual | Notes |
|---------|----------|--------|-------|
| `rm src/app.py` | deny | ✅ deny | rm excluded from fallback verbs |
| `rm .` | deny | ✅ deny | rm excluded from fallback verbs |
| `rm ./root_config.json` | deny | ✅ deny | Single-segment, no trailing / |
| `rm ~/` | deny | ✅ deny | tilde guard in rm |
| `rm -rf .` | deny | ✅ deny | |
| `del src/app.py` | deny | ✅ deny | del excluded from fallback verbs |
| `remove-item src/app.py` | deny | ✅ deny | remove-item excluded |
| `cat .github/hooks/evil.py` | deny | ✅ deny | deny-zone guard |
| `cat .vscode/settings.json` | deny | ✅ deny | deny-zone guard |
| `python .github/hooks/script.py` | deny | ✅ deny | deny-zone guard |
| `ls -la .g*` | deny | ✅ deny | wildcard guard (via `_check_path_arg`) |
| `cat ./root_config.json` | deny | ✅ deny | single-segment ./ without trailing / |
| `type ./file.txt` | deny | ✅ deny | single-segment ./ without trailing / |

All critical MUST-ALLOW cases confirmed:

| Command | Expected | Actual | Notes |
|---------|----------|--------|-------|
| `python src/app.py` | allow | ✅ allow | multi-segment fallback |
| `python -m pytest tests/` | allow | ✅ allow | trailing / + fallback |
| `cat src/app.py` | allow | ✅ allow | multi-segment fallback |
| `type src/app.py` | allow | ✅ allow | multi-segment fallback |
| `ls src/` | allow | ✅ allow | trailing / heuristic |
| `python -m venv .venv` | allow | ✅ allow | step-4 venv fallback |
| `.venv/Scripts/Activate.ps1` | allow | ✅ allow | activation handler |
| `get_errors filePaths=["src/app.py"]` | allow | ✅ allow | validate_get_errors fallback |

---

## Tester Edge-Case Tests Added

### tests/FIX-022/test_fix022_tester_edge_cases.py (18 tests, TST-1736–TST-1753)
- **Backslash variants**: `python src\app.py`, `cat src\file.py`, `python src\main\app.py`, `get-content src\app.py` → all allow
- **Trailing backslash**: `ls tests\` → deny (trailing `\` not normalised as directory indicator — known limitation)
- **Single-segment heuristic boundary**: `ls tests` → allow (not path-like); `cat ./config` → deny
- **Chained deny-zone**: `cat src/app.py && cat .vscode/settings.json` → deny; `python src/app.py; python .github/hooks/evil.py` → deny; `ls src/ || ls noagentzone/` → deny
- **pip -r flag**: `pip install -r requirements.txt` (VIRTUAL_ENV set) → allow; `pip install -r ./requirements.txt` → deny; `pip install` (no VIRTUAL_ENV) → deny
- **Invariants**: `cat ./root_config.json` → deny; `ls -la .g*` → deny; `rm/del/remove-item src/utils.py` → all deny
- **Fallback verbs**: `pytest tests/` → allow; `ruff src/` → deny (ruff not in allowlist — dead entry in fallback verbs, noted)

### tests/FIX-023/test_fix023_tester_edge_cases.py (5 tests, TST-1754–TST-1758)
- `.venv\Scripts\Activate.ps1` (backslash) → allow
- `.venv\Scripts\activate.bat` (backslash) → allow
- `.venv\bin\activate` (backslash) → allow
- `python -m venv src\venv` (backslash, multi-segment) → allow
- `python -m venv .venv\` (trailing backslash) → deny (unparseable by shlex — correct safe-fail)

### tests/FIX-026/test_fix026_tester_edge_cases.py (6 tests, TST-1759–TST-1764)
- Multiple project paths → allow
- Mixed allow + deny paths → deny (any deny blocks entire call)
- Deny-zone only → deny
- Backslash path (`src\app.py`) → allow
- `None` in filePaths → deny (fail-closed on malformed input)
- Empty string in filePaths → deny (fail-closed on malformed input)

---

## Test Run Results

| Run | Tests | Result |
|-----|-------|--------|
| Developer tests (FIX-022 to FIX-026): 48 tests | Pass | 48/48 — 0 failures |
| Developer full regression: 3256 passed | Pass | 2 pre-existing failures unchanged |
| Tester edge-case suite: 29 tests | Pass | 29/29 — 0 failures |
| Tester full regression: 3285 passed | Pass | 2 pre-existing failures unchanged |

**Pre-existing failures (unchanged):**
1. `test_no_duplicate_tst_ids` — FIX-009/BUG-035 (duplicate TST-1557, TST-599)
2. `test_uninstall_delete_type_is_filesandirs` — INS-005/BUG-045

---

## Minor Observations (Non-blocking)

1. **Dead code in `_PROJECT_FALLBACK_VERBS`**: `ruff`, `mypy`, `black`, `flake8`, `isort` are listed but not in `_COMMAND_ALLOWLIST`. The fallback is unreachable for these verbs. These can be removed in a cleanup WP without any security impact.
2. **Trailing backslash behaviour**: `ls tests\` is denied because the trailing backslash does not trigger the trailing-`/` directory heuristic. This is a usability limitation on Windows but not a security regression — the correct form `ls tests/` works.
3. **`pip install -r ./requirements.txt`**: Denied even with VIRTUAL_ENV active because `./requirements.txt` is a single `.`-prefixed segment without trailing `/`. This is a conservative but correct security decision — if needed, users can use `pip install -r requirements.txt` (no leading `./`).

---

## Verdict

**PASS** — All security invariants hold. All new tests pass. Zero new regressions. The implementation correctly narrows path resolution for read/execute operations while maintaining hard denials for destructive operations and deny-zone targets.
