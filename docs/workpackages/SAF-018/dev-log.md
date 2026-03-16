# SAF-018 Dev Log — Fix multi_replace_string_in_file Tool Recognition

**Status:** In Progress  
**Assigned To:** Developer Agent  
**Branch:** SAF-018/multi-replace-tool  
**Date Started:** 2026-03-16

---

## Problem Statement

`multi_replace_string_in_file` was already present in both `_EXEMPT_TOOLS` and `_WRITE_TOOLS`
in `security_gate.py`. However, the `validate_write_tool()` function called by the
`_WRITE_TOOLS` branch uses `extract_path()` to find a single `filePath` field in the
tool payload. For `multi_replace_string_in_file`, the file paths are nested inside a
`replacements` array, not at the top level of `tool_input`. This caused `extract_path()`
to return `None`, and `validate_write_tool` to always return `"deny"`.

---

## Root Cause

`multi_replace_string_in_file` payload structure:
```json
{
  "tool_name": "multi_replace_string_in_file",
  "tool_input": {
    "replacements": [
      {"filePath": "path/to/file1", "oldString": "...", "newString": "..."},
      {"filePath": "path/to/file2", "oldString": "...", "newString": "..."}
    ],
    "explanation": "..."
  }
}
```

`extract_path()` only looks for `filePath` as a direct key in `data` or `data["tool_input"]`,
not inside the `replacements` array. Result: all `multi_replace_string_in_file` calls were
denied by `validate_write_tool` returning "deny" on `None` path.

---

## Implementation

### Changes to `Default-Project/.github/hooks/scripts/security_gate.py`

1. **Added `validate_multi_replace_tool(data, ws_root)` function.**
   - Extracts the `replacements` list from `tool_input` (falls back to top-level `data`).
   - Fails closed (`"deny"`) if `replacements` is absent, not a list, or empty.
   - For every replacement entry, extracts `filePath` and zone-checks it.
   - If ANY filePath is outside the project folder (`zone != "allow"`), returns `"deny"`.
   - Only returns `"allow"` when ALL filePaths pass zone checks.

2. **Updated `decide()` to route `multi_replace_string_in_file`** to the new function
   BEFORE the general `_WRITE_TOOLS` block.

3. **Ran `update_hashes.py`** to re-embed the new canonical SHA256 hash of `security_gate.py`.

### Files Changed

- `Default-Project/.github/hooks/scripts/security_gate.py`
- `templates/coding/.github/hooks/scripts/security_gate.py` (mirror)

---

## Tests Written

`tests/SAF-018/test_saf018_multi_replace.py`

| Category | Test Count | Description |
|----------|-----------|-------------|
| Unit | 12 | `validate_multi_replace_tool()` direct calls |
| Security | 6 | Tool recognized and zone-checked via `decide()` |
| Bypass | 8 | Mixed paths, path traversal, empty/malformed payloads |
| Cross-platform | 4 | Windows/POSIX path variants |
| Integration | 5 | Full `decide()` pipeline |

Total: **35 tests**

---

## Iteration 1 Results

*(To be filled in after test run)*
