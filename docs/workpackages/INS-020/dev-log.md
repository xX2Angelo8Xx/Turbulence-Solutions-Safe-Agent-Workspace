# Dev Log — INS-020

**WP:** INS-020  
**Category:** Installer  
**Name:** Update require-approval.json template for ts-python  
**Status:** Review  
**Assigned To:** Developer Agent  
**Date:** 2026-03-19  

---

## Summary

Updated `templates/coding/.github/hooks/require-approval.json` to use the `ts-python` shim instead of bare `python` for both the `command` (Unix) and `windows` fields.

This ensures new workspaces created by the launcher invoke the security gate via the bundled Python runtime provided by the `ts-python` shim (INS-019), rather than relying on a system-wide Python installation.

---

## Files Changed

| File | Change |
|------|--------|
| `templates/coding/.github/hooks/require-approval.json` | Replaced `python .github/hooks/scripts/security_gate.py` with `ts-python .github/hooks/scripts/security_gate.py` in both `command` and `windows` fields |
| `docs/workpackages/workpackages.csv` | Status → In Progress → Review; Assigned To → Developer Agent |
| `docs/test-results/test-results.csv` | Added TST-1853 result row |

---

## Hash Impact

Confirmed that `security_gate.py` only integrity-checks two files:
- `.claude/settings.json` (`_KNOWN_GOOD_SETTINGS_HASH`)
- Itself (`_KNOWN_GOOD_GATE_HASH`)

`require-approval.json` is **not** hash-checked. No hash update was needed.

---

## Tests Written

**Location:** `tests/INS-020/test_ins020_require_approval.py`  
**Count:** 8 tests  
**Result:** 8 passed / 0 failures

| Test | Description |
|------|-------------|
| `test_file_exists` | File exists at expected template path |
| `test_json_is_valid` | File parses as valid JSON |
| `test_command_field_uses_ts_python` | `command` field starts with `ts-python ` |
| `test_windows_field_uses_ts_python` | `windows` field starts with `ts-python ` |
| `test_no_bare_python_references` | No bare `python .github/...` (regex with negative lookbehind to avoid false positive on `ts-python`) |
| `test_command_points_to_security_gate` | Both fields still end with `security_gate.py` |
| `test_hook_type_is_command` | `type` field remains `command` |
| `test_timeout_preserved` | `timeout` remains 15 |

---

## Known Limitations

None. This is a single-file template change with no runtime or cross-platform complexity.
