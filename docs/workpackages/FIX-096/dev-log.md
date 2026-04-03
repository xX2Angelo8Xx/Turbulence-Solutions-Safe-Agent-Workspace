# Dev Log — FIX-096: Fix MANIFEST CI Check Missing File

## Status
Review

## Developer
Developer Agent

## Date
2026-04-04

## Related ADRs
- **ADR-002 — Mandatory CI Test Gate Before Release Builds** (Active): Directly applicable. This fix enforces the CI gate by converting a silent pass (exit 0) into a failure (exit 1) when MANIFEST.json is absent, in line with ADR-002's requirement that CI must fail on integrity issues.
- **ADR-003 — Template Manifest and Workspace Upgrade System** (Active): The MANIFEST.json is the integrity artifact described by ADR-003. Allowing CI to pass silently when the manifest is missing contradicts ADR-003's mandate that the manifest must always be present and validated.

## Problem Summary
Both `.github/workflows/test.yml` and `.github/workflows/staging-test.yml` contained inline Python manifest-check steps that called `sys.exit(0)` (success) when `MANIFEST.json` was missing. This caused CI to pass silently instead of failing, hiding the missing-manifest condition. This was identified as bug skip point #10.

## Implementation

### Files Changed
1. `.github/workflows/test.yml` — Line 113: Changed `sys.exit(0)` (with a WARNING print) to `sys.exit(1)` with an ERROR message directing the developer to run `scripts/generate_manifest.py`.
2. `.github/workflows/staging-test.yml` — Line 69: Same fix — changed `sys.exit(0)` (SKIP print) to `sys.exit(1)` with the same ERROR message.

### Change Detail
**Before (test.yml):**
```python
print("WARNING: MANIFEST.json not found — skipping manifest check")
sys.exit(0)
```
**After (test.yml):**
```python
print("ERROR: MANIFEST.json not found — run scripts/generate_manifest.py")
sys.exit(1)
```

**Before (staging-test.yml):**
```python
print("SKIP: No MANIFEST.json yet")
sys.exit(0)
```
**After (staging-test.yml):**
```python
print("ERROR: MANIFEST.json not found — run scripts/generate_manifest.py")
sys.exit(1)
```

## Tests Written
- `tests/FIX-096/test_fix096_manifest_ci_check.py` — Contains 4 unit tests:
  1. Verifies test.yml no longer contains `sys.exit(0)` in the missing-manifest path.
  2. Verifies test.yml contains `sys.exit(1)` in the missing-manifest path.
  3. Verifies staging-test.yml no longer contains `sys.exit(0)` in the missing-manifest path.
  4. Verifies staging-test.yml contains `sys.exit(1)` in the missing-manifest path.

## Regression Baseline
No entry for FIX-096 exists in `tests/regression-baseline.json` — no action required.

## Test Results
- Run via `scripts/run_tests.py --wp FIX-096 --type Unit --env "Windows 11 + Python 3.11"`
- Result: **6 passed, 0 failed** (logged as TST-2491)

## Known Limitations
None. The fix is minimal and targeted — only the two `sys.exit(0)` calls in the missing-manifest branches were changed.
