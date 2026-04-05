# Test Report — FIX-112

## Workpackage
**ID:** FIX-112  
**Name:** Add PowerShell skip to SAF-074 tests  
**Tester:** Tester Agent  
**Date:** 2026-04-06  
**Verdict:** PASS

---

## Review Summary

Reviewed `tests/SAF-074/test_saf074.py` and `tests/FIX-112/test_fix112.py`. The implementation correctly adds a module-level `pytestmark = pytest.mark.skipif(...)` that:
- Uses `shutil.which("powershell") is None and shutil.which("pwsh") is None` — checks both Windows (`powershell`) and cross-platform core (`pwsh`).
- Applies automatically to all 29 SAF-074 tests via the module-level mark.
- Is verified by 4 AST/text-scan tests in `tests/FIX-112/`.

No ADR conflicts found. `dev-log.md` is complete and accurate.

---

## Test Results

### SAF-074 Tests (29 tests)
```
python -m pytest tests/SAF-074/ -v
29 passed in 10.49s
```
All 29 tests **PASSED** on Windows (PowerShell available). On platforms without PowerShell, all 29 would skip gracefully.

### FIX-112 Verification Tests (4 tests)
```
python -m pytest tests/FIX-112/ -v
4 passed in 0.22s
```
- `test_pytestmark_present` — PASSED
- `test_pytestmark_checks_powershell` — PASSED
- `test_pytestmark_checks_pwsh` — PASSED
- `test_shutil_which_used` — PASSED

### Full Suite
```
python scripts/run_tests.py --wp FIX-112 --type Regression --env Windows --full-suite
82 failed, 8921 passed, 345 skipped, 5 xfailed, 66 errors (TST-2645)
```
All failures and errors confirmed to be pre-existing entries in `tests/regression-baseline.json`. **Zero new regressions** introduced by this WP.

### Workspace Validation
```
python scripts/validate_workspace.py --wp FIX-112
All checks passed. (exit code 0)
```

---

## Regression Check

- All 82 failed tests and 66 errors are present in `tests/regression-baseline.json`.
- No new failures introduced by FIX-112.
- FIX-112 does not touch `security_gate.py` or `zone_classifier.py` — snapshot tests not required.

---

## Security Review

No security concerns. The change is purely additive (decorating existing tests with a skip condition). `shutil.which` is a safe, read-only operation. No input validation concerns.

---

## Edge Cases Considered

1. **Both `powershell` and `pwsh` absent** — all 29 tests skip with descriptive reason message. Verified by AST tests.
2. **`pwsh` present but `powershell` absent** (Linux/macOS with PowerShell Core) — tests run normally since the condition uses `and` (both must be None to skip).
3. **`powershell` present but `pwsh` absent** (Windows without pwsh) — tests run normally.
4. **Both present** (standard Windows) — tests run and pass as verified above.
5. **`import shutil` conflicts** — no conflict; `shutil` was already used in the file for `shutil.which` calls within test logic.

---

## Verdict: PASS

All acceptance criteria met. WP status set to `Done`.
