# FIX-033 — Dev Log
## Allow dot-prefix names and env var assignment in project

**WP ID:** FIX-033  
**Branch:** fix-033  
**Assigned To:** Developer Agent  
**Status:** In Progress → Review  
**Date:** 2026-03-18

---

## Problem Statement

Two related gaps in `security_gate.py`:

1. **Dot-prefix single-segment paths** (`.venv`, `.env`, `.gitignore`, `.editorconfig`):
   When an agent runs `ls .venv`, `cat .gitignore`, or `cat .env` from within the project
   folder context, the path `.venv` is classified as "deny" (it resolves to
   `{ws_root}/.venv`, outside the project folder). The project-folder fallback was
   gated by `len(parts_fb) >= 2 or stripped.endswith("/")`, which excluded bare
   single-segment dot-prefix names that don't have a trailing slash.

2. **`$env:VIRTUAL_ENV = 'value'` assignments (PowerShell)**: The primary verb was
   `$env:VIRTUAL_ENV` which starts with `$`, triggering the "dynamic primary verb"
   deny guard unconditionally. These assignments are safe when the value points inside
   the project folder.

Addresses audit findings L7, L10, L11 from Security Audit V2.0.0 (2026-03-17).

---

## Root Cause Analysis

### Issue 1 — Dot-prefix paths denied in step 5 of `_validate_args`

The condition triggering the project-folder fallback in step 5:
```python
if len(parts_fb) >= 2 or (len(parts_fb) == 1 and stripped.rstrip().endswith("/")):
```
For `.venv` (single segment, no trailing `/`): both sub-conditions are False → fallback
never fires → returns False → DENY.

Note: `python -m venv .venv` was already correctly handled (step 4 calls
`_try_project_fallback` directly without the single-segment restriction). The gap only
affected generic path args in step 5 and redirect targets in step 6.

The same gap existed in step 6 (redirect target blocks) for both standalone (`>`) and
embedded (`text>.env`) redirect forms.

### Issue 2 — `$env:` assignment denied before zone check

```python
if verb.startswith("$") or "${" in verb or "$(" in verb:
    return ("deny", ...)
```
`$env:VIRTUAL_ENV` starts with `$` → unconditional deny. No zone check of the value.

---

## Implementation

### Change 1 — Step 5 dot-prefix fallback (`_validate_args`)

Added `or stripped.startswith(".")` to the single-segment fallback condition:
```python
if len(parts_fb) >= 2 or (
    len(parts_fb) == 1
    and (
        stripped.rstrip().endswith("/")
        or stripped.startswith(".")
    )
):
```
`_try_project_fallback` already rejects deny-zone names (`.github`, `.vscode`,
`noagentzone`), so this cannot open new bypass vectors.

### Change 2 — Step 6 redirect fallback

Same `or target.startswith(".")` addition for both standalone and embedded redirect
target blocks. Preserves all existing deny behavior for non-dot-prefix single-segment
names.

### Change 3 — `$env:` assignment handler

Added before the `$`-verb deny guard in `sanitize_terminal_command`:
```python
if verb_lower.startswith("$env:") and len(tokens) >= 3 and tokens[1] == "=":
    env_value = tokens[2].strip("\"'")
    if "$" not in env_value:
        norm_env_val = posixpath.normpath(env_value.replace("\\", "/"))
        if zone_classifier.classify(norm_env_val, ws_root) == "allow":
            continue
        if _try_project_fallback(norm_env_val, ws_root):
            continue
    return ("deny", f"$env: assignment value is outside allowed zone: ...")
```

Values containing `$` (nested variable references) are always denied (unknown
runtime path). Values that are neither in the allow zone nor resolve via project
fallback are denied.

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/security_gate.py` | Three targeted changes (step 5, step 6 ×2, $env handler) |
| `templates/coding/.github/hooks/scripts/security_gate.py` | Synced from Default-Project |
| `docs/workpackages/workpackages.csv` | Status → In Progress, Assigned To filled |

---

## Tests Written

`tests/FIX-033/test_fix033_dot_prefix_env_vars.py`

Coverage:
- `ls .venv` → allow
- `cat .gitignore` → allow
- `cat .env` → allow
- `cat .editorconfig` → allow
- `python -m venv .venv` → allow (regression from FIX-023)
- `ls Project/.venv` → allow
- `cat Project/.gitignore` → allow
- `.venv outside project` → deny
- `ls .github` → deny
- `ls .vscode` → deny
- `$env:VIRTUAL_ENV = 'project/.venv'` → allow
- `$env:VIRTUAL_ENV = 'c:/workspace/project/.venv'` → allow (absolute)
- `$env:VIRTUAL_ENV = '.venv'` → allow (via fallback)
- `$env:VIRTUAL_ENV = '.github'` → deny
- `$env:VIRTUAL_ENV = 'noagentzone'` → deny
- `$env:VIRTUAL_ENV = '/etc/passwd'` → deny
- `$env:VIRTUAL_ENV = '$env:OTHER'` (nested $) → deny
- `$env:VIRTUAL_ENV` without `=` → deny (no assignment syntax)
- Redirect `echo test > .env` → allow (in project context)
- Redirect `echo test > .github/f` → deny

---

## Test Results

All tests pass. See `docs/test-results/test-results.csv` for TST-IDs.
