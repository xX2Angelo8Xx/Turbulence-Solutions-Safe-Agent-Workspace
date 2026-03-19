# FIX-034 Dev Log — Allow venv activation in project folder

## Summary
Added early venv activation detection in `sanitize_terminal_command()` that runs BEFORE Stage 3 obfuscation pre-scan, preventing false positives from P-22 (`source`) and P-23 (POSIX dot-source) patterns on legitimate venv activations.

## Changes
- **`security_gate.py`**: Added `_VENV_ACTIVATION_SEG_RE` regex pattern matching venv activation commands (`source .venv/bin/activate`, `& .venv/Scripts/Activate.ps1`, `.\venv\Scripts\activate`, etc.)
- **`security_gate.py`**: Added early venv activation pass before Stage 3 — validates venv path is inside project folder via zone classifier + project fallback, then excludes validated segments from obfuscation scanning
- **Hash updated** via `update_hashes.py`
- **Template synced** to `templates/coding/`

## Test Results
- FIX-034: 40/40 passed
- Regression (FIX-033 + FIX-023 + SAF-020 + FIX-032): 277/277 passed
- No regressions
