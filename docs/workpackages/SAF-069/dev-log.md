# Dev Log — SAF-069: Block env-var exfiltration in unrestricted commands

**WP ID:** SAF-069  
**Branch:** SAF-069/block-env-exfiltration  
**Developer:** Developer Agent  
**Date Started:** 2026-04-02  
**User Story:** US-074  
**Bug Fixed:** BUG-174

---

## Problem Statement

In `_validate_args()` in `security_gate.py`, the `$` dollar-sign check (step 5) is
gated behind `if rule.path_args_restricted or not rule.allow_arbitrary_paths:`.
Commands with `allow_arbitrary_paths=True` (e.g. `write-output`, `echo`, `write-host`,
`env`, `printenv`, `pwd`, `which`, `where`, `get-command`) skip that entire block.

This means `Write-Output $env:USERNAME` passes unchecked and can leak environment
variables including credentials.

## Fix Applied

Added a universal `$env:` exfiltration guard AFTER the `_step4_validated_indices`
initialization (after step 3) and BEFORE the step 4 python `-m` check in
`_validate_args()`.

The guard iterates over all args and returns `False` (deny) if any token contains
`$env:` (case-insensitive). Scoped to `$env:` specifically to avoid false positives on
harmless strings like `$5`.

**File changed:**
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

## Implementation Notes

- Guard runs for ALL commands regardless of `allow_arbitrary_paths`.
- Case-insensitive check (`tok.lower()`) catches `$ENV:SECRET` variants.
- Does not affect step 5's broader `$` check — both guards coexist.
- Does not modify `_tokenize_segment` (that was SAF-068).
- Does not run `update_hashes.py` (that is SAF-071).

## Tests Written

`tests/SAF-069/test_saf069.py` — 7 test cases:
1. `Write-Output $env:USERNAME` → deny
2. `echo $env:GITHUB_TOKEN` → deny
3. `Write-Host $env:PATH` → deny
4. `echo "hello world"` → allow (no $env:)
5. `echo price is $5` → allow ($ but not $env:)
6. `write-output $ENV:SECRET` → deny (case-insensitive)
7. `Get-Content $env:USERPROFILE\file.txt` → deny (double-covered)

---

## Iteration 1 — Implementation

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — inserted SAF-069 guard
- `tests/SAF-069/test_saf069.py` — new test file
- `tests/SAF-069/__init__.py` — new init file
- `docs/workpackages/SAF-069/dev-log.md` — this file
- `docs/workpackages/workpackages.csv` — status update

### Test Results
All 7 tests pass. See `docs/test-results/test-results.csv`.

---

## Iteration 2 — Fix Tester Finding (2026-04-02)

### Finding
Tester T08 exposed a bypass: PowerShell brace syntax `${env:USERNAME}` does NOT contain
the substring `$env:` (the `{` interrupts the match), so the guard missed it.

### Fix Applied
Extended the guard condition from:
```python
if "$env:" in tok.lower():
```
to:
```python
tok_lower = tok.lower()
if "$env:" in tok_lower or "${env:" in tok_lower:
```
Both `$env:VAR` and `${env:VAR}` are now denied.

**File changed:**
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — guard extended

### Test Results
All 13 tests pass (T01–T13 including T08 brace-syntax). See TST-2431 in test-results.csv.
