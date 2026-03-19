# FIX-035 Dev Log — Allow deferred development tools

## Summary
Added `install_python_packages`, `configure_python_environment`, and `fetch_webpage` to the `_EXEMPT_TOOLS` set in `security_gate.py`, allowing these VS Code/Copilot development tools to function without security gate interference.

## Changes
- **`security_gate.py`**: Added 3 tool names to `_EXEMPT_TOOLS`
- **Hash updated** via `update_hashes.py`
- **Template synced** to `templates/coding/`

## Test Results
- FIX-035: 14/14 passed
- Regression (SAF-001 + FIX-034 + FIX-033): 194/194 passed
- No regressions
