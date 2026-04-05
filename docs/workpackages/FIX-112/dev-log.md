# Dev Log — FIX-112

## Workpackage
**ID:** FIX-112  
**Name:** Add PowerShell skip to SAF-074 tests  
**Status:** Review  
**Assigned To:** Developer Agent  

## Prior Art Check
No relevant ADRs found in `docs/decisions/index.jsonl` for this domain (PowerShell test skipping).

## Implementation Summary

Added a module-level `pytestmark` to `tests/SAF-074/test_saf074.py` so that all 29 SAF-074 tests skip gracefully on platforms without PowerShell (e.g., Ubuntu CI runners) instead of failing with `FileNotFoundError`.

### Change
- Added `import shutil` to the existing imports.
- Added `pytestmark = pytest.mark.skipif(shutil.which("powershell") is None and shutil.which("pwsh") is None, reason="PowerShell not available")` immediately after the `import pytest` line.

The decorator checks for both `powershell` (Windows) and `pwsh` (cross-platform PowerShell Core) so that environments with either flavour will still run the tests.

## Files Changed
- `tests/SAF-074/test_saf074.py` — added `import shutil` and module-level `pytestmark`
- `tests/FIX-112/test_fix112.py` — new test file verifying the decorator is present and correct

## Tests Written
- `tests/FIX-112/test_fix112.py`
  - `test_pytestmark_present` — asserts `pytestmark` assignment exists via AST
  - `test_pytestmark_checks_powershell` — asserts `"powershell"` string is referenced
  - `test_pytestmark_checks_pwsh` — asserts `"pwsh"` string is referenced
  - `test_shutil_which_used` — asserts `shutil.which` is used

**Result:** 4 passed (TST-2644)

## Known Limitations
None.
