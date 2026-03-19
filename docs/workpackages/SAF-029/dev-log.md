# SAF-029 Dev Log — Fix dot-prefix path matching for delete operations

## Status
In Progress → Review

## WP Summary
Fix `security_gate.py` so that PowerShell delete cmdlets (`Remove-Item`, `ri`)
targeting dot-prefix paths like `.venv`, `.git`, `.pytest_cache`, `.env` inside
the project folder are correctly allowed, while `.github`, `.vscode`, and
`NoAgentZone` remain denied. Unix `rm`/`del`/`erase`/`rmdir` retain their
current deny-all behavior (FIX-033 requirement).

## Root Cause Analysis

The deny originates from `_validate_args` step 5 (path argument zone-check).

For a relative path like `.venv`:
1. `_is_path_like(".venv")` → `True` (starts with `.`)
2. `_check_path_arg(".venv", ws_root)` → `False` — `zone_classifier.classify`
   resolves `.venv` against the workspace root → `ws_root/.venv`, which is
   outside the project folder. Default deny applies.
3. `verb.lower()` (`remove-item`) is **not** in `_PROJECT_FALLBACK_VERBS`.
4. No fallback tried → command denied.

## Design Decision

The previous attempt (failed) added all delete verbs to `_PROJECT_FALLBACK_VERBS`.
This caused 14 regressions:
- `rm src/app.py` → incorrectly fell back to `project/src/app.py` → allowed
- `rm .env` → incorrectly allowed (FIX-033 requires `rm .env` → denied)

The correct fix: introduce a **separate** constant `_DELETE_DOT_FALLBACK_VERBS`
containing **only** `remove-item` and `ri` (PowerShell cmdlets). This set enables
project-folder fallback **exclusively** for single-segment dot-prefix non-deny-zone
paths. Multi-segment paths remain denied for ALL delete verbs (FIX-022 intact).
`rm`/`del`/`erase`/`rmdir` remain on no-fallback (FIX-033 intact).

## Fix Implemented

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`

1. Added `_DELETE_DOT_FALLBACK_VERBS` constant after `_PROJECT_FALLBACK_VERBS`:
```python
# SAF-029: PowerShell delete cmdlets that receive project-folder fallback for
# single-segment dot-prefix paths only (e.g. .venv, .git, .pytest_cache, .env).
# Unix rm/del/erase/rmdir are intentionally excluded — FIX-033 requires
# `rm .env` to be denied and the full rm family must not get path fallback.
_DELETE_DOT_FALLBACK_VERBS: frozenset[str] = frozenset({"remove-item", "ri"})
```

2. Added `elif` branch in `_validate_args` step 5 (after `_PROJECT_FALLBACK_VERBS` block):
```python
elif verb.lower() in _DELETE_DOT_FALLBACK_VERBS:
    # SAF-029: allow single-segment dot-prefix non-deny-zone
    # paths (e.g. .venv, .git) via project-folder fallback.
    # Multi-segment paths remain denied (FIX-022 intact).
    if "*" not in stripped and "?" not in stripped and "[" not in stripped:
        norm_fb = posixpath.normpath(stripped.replace("\\", "/"))
        parts_fb = [p for p in norm_fb.split("/") if p and p not in (".", "..")]
        if len(parts_fb) == 1 and norm_fb.startswith("."):
            if _try_project_fallback(norm_fb, ws_root):
                _prev_was_flag = False
                continue
```

**File:** `templates/coding/.github/hooks/scripts/security_gate.py`
Synced (copied from Default-Project after update_hashes.py).

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`
Hash updated via `update_hashes.py` → `_KNOWN_GOOD_GATE_HASH = 4f7c1fb7bc4918dffecdc1d688d1a4e45d6fb122e21e3a55a64f4577ccd3c91b`

## Security Analysis

| Path | Verb | Expected | Reason |
|------|------|----------|--------|
| `.venv` | Remove-Item | allow | Not a deny zone; resolves `project/.venv` via `_DELETE_DOT_FALLBACK_VERBS` |
| `.git` | Remove-Item | allow | Not a deny zone; fallback succeeds |
| `.pytest_cache` | Remove-Item | allow | Not a deny zone; fallback succeeds |
| `.env` | Remove-Item | allow | Not a deny zone; fallback succeeds |
| `.venv` | rm | deny | rm not in `_DELETE_DOT_FALLBACK_VERBS` (FIX-033 requirement) |
| `.env` | rm | deny | rm not in `_DELETE_DOT_FALLBACK_VERBS` (FIX-033 explicit requirement) |
| `.github` | Remove-Item | deny | `_try_project_fallback` rejects deny-zone names |
| `.vscode` | Remove-Item | deny | `_try_project_fallback` rejects deny-zone names |
| `.g*` / `.v*` | any | deny | SAF-020 wildcard prefix match (unchanged) |
| `src/app.py` | Remove-Item | deny | Multi-segment: `len(parts_fb) == 1` condition fails |
| `./root_config.json` | Remove-Item | deny | normpath strips `./`; `norm_fb = root_config.json`; no leading `.` |

## Tests Written / Updated

`tests/SAF-029/test_saf029_delete_dot_prefix.py`

**Allowed (Remove-Item and ri):**
- TST-5300 to TST-5303: Remove-Item .venv/.git/.pytest_cache/.env
- TST-5308: ri .venv
- TST-5309–5313: Remove-Item .gitignore/.editorconfig/-Recurse/-Force/-Recurse -Force

**Denied (deny zones, wildcards, boundaries):**
- TST-5320–5325: Remove-Item/rm on .github/.vscode/noagentzone
- TST-5330–5335: Wildcard .g*/.v*/.*
- TST-5340–5342: ./root_config.json, absolute outside-workspace paths
- TST-5343–5347: rm .venv/.git/.pytest_cache/.env denied; Remove-Item src/app.py denied

**Regressions (all pass):**
- FIX-022: test_remove_item_src_app_deny, test_chain_python_and_rm_deny
- FIX-022 tester: test_rm_family_never_get_fallback
- FIX-033: test_rm_dot_env_fallback_not_allowed

## Test Results

All 34 SAF-029 tests: PASS
All 4 critical regression tests: PASS
Full SAF/FIX regression suite: 1182 passed, 8 pre-existing SAF-022 failures (unrelated)
See `docs/test-results/test-results.csv` → TST-1832

## Files Changed

1. `Default-Project/.github/hooks/scripts/security_gate.py` — add `_DELETE_DOT_FALLBACK_VERBS` and `elif` branch in `_validate_args`
2. `templates/coding/.github/hooks/scripts/security_gate.py` — synced from Default-Project
3. `tests/SAF-029/test_saf029_delete_dot_prefix.py` — updated test file: rm .xxx tests moved to DENY boundary class

## Root Cause Analysis

The deny originates from `_validate_args` step 5 (path argument zone-check).

For a relative path like `.venv`:
1. `_is_path_like(".venv")` → `True` (starts with `.`)
2. `_check_path_arg(".venv", ws_root)` → `False` — `zone_classifier.classify` resolves
   `.venv` against the workspace root → `ws_root/.venv`, which is outside the project
   folder. Default deny applies.
3. `verb.lower()` (`remove-item`) is **not** in `_PROJECT_FALLBACK_VERBS`.
4. Fallback never tried → command denied.

Delete verbs were intentionally excluded from `_PROJECT_FALLBACK_VERBS` (FIX-022 comment)
to prevent `rm ./root_config.json` from being mis-classified as project-local. However,
that concern is already handled by the fallback conditions in step 5:

- `posixpath.normpath("./root_config.json")` → `root_config.json` (no leading `.`)
- The condition `norm_fb.startswith(".")` is False → fallback never tried for `./file`.

So adding delete verbs to `_PROJECT_FALLBACK_VERBS` is safe.

The `_try_project_fallback` function uses **exact** deny-zone name matching:
```python
if any(p.lower() in (".github", ".vscode", "noagentzone") for p in parts):
    return False
```
This means `.github` and `.vscode` are still blocked, while `.git`, `.venv`, `.env`,
`.pytest_cache` pass through and resolve correctly inside the project folder.

## Fix Implemented

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`

Added delete verbs to `_PROJECT_FALLBACK_VERBS`:

```python
# SAF-029: Delete commands — project-folder fallback for dot-prefix paths
# (.venv, .git, .pytest_cache, .env); exact deny-zone names (.github, .vscode,
# noagentzone) are still blocked by _try_project_fallback.
# ./root_config.json is safe: posixpath.normpath strips "./" so norm_fb
# does not start with "." and the fallback is not tried.
"remove-item", "ri", "rm", "del", "erase", "rmdir",
```

**File:** `templates/coding/.github/hooks/scripts/security_gate.py`
Synced with the same change.

**File:** `Default-Project/.github/hooks/scripts/security_gate.py`
Hash updated via `update_hashes.py` after the fix.

## Security Analysis

| Path | Expected | Reason |
|------|----------|--------|
| `.venv` | allow | Not a deny zone; resolves to `project/.venv` via fallback |
| `.git` | allow | Not a deny zone; resolves to `project/.git` via fallback |
| `.pytest_cache` | allow | Not a deny zone; resolves to `project/.pytest_cache` via fallback |
| `.env` | allow | Not a deny zone; resolves to `project/.env` via fallback |
| `.github` | deny | Exact deny zone match in `_try_project_fallback` |
| `.vscode` | deny | Exact deny zone match in `_try_project_fallback` |
| `.g*` | deny | SAF-020 wildcard prefix match (unchanged) |
| `.v*` | deny | SAF-020 wildcard prefix match (unchanged) |
| `./root_config.json` | deny | `normpath` strips `./`; `norm_fb = root_config.json` doesn't start with `.` |

## Tests Written

`tests/SAF-029/test_saf029_delete_dot_prefix.py`

Tests:
- `Remove-Item .venv` inside project → allowed
- `Remove-Item .git` inside project → allowed
- `Remove-Item .pytest_cache` inside project → allowed
- `Remove-Item .github` → denied
- `Remove-Item .vscode` → denied
- `Remove-Item .env` inside project → allowed
- Wildcard patterns `.g*`, `.v*` still denied (SAF-020 intact)
- `rm .venv`, `rm .git` aliases also allowed
- `rm ./root_config.json` still denied
- `rm .github` still denied

## Test Results

All SAF-029 tests: PASS
Full test suite: see `docs/test-results/test-results.csv`

## Files Changed

1. `Default-Project/.github/hooks/scripts/security_gate.py` — add delete verbs to `_PROJECT_FALLBACK_VERBS`
2. `templates/coding/.github/hooks/scripts/security_gate.py` — sync
3. `tests/SAF-029/test_saf029_delete_dot_prefix.py` — new test file
4. `tests/SAF-029/__init__.py` — package marker
5. `tests/SAF-029/conftest.py` — zone classifier mock
6. `docs/workpackages/SAF-029/dev-log.md` — this file
7. `docs/workpackages/workpackages.csv` — status updated
8. `docs/test-results/test-results.csv` — test run logged
