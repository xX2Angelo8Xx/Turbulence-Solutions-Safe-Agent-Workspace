# SAF-060 Dev Log — Investigate and Fix Memory Tool Still Blocked

**WP ID:** SAF-060  
**Branch:** SAF-060/memory-fix  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-30  
**Status:** In Progress

---

## Investigation Summary

### Root Cause Found: Wrong key checked in `validate_memory()`

**File:** `templates/agent-workbench/.github/hooks/scripts/security_gate.py`  
**Function:** `validate_memory(data, ws_root)`

#### What was checked:

**(a) Was test workspace built from commit including SAF-048?**
SAF-048 is clearly present — `validate_memory()` exists at line 2712 and `decide()` calls it at line 3093. Not a deployment issue.

**(b) Is `validate_memory()` actually reached in `decide()`?**
Yes — `decide()` has an explicit `if tool_name == "memory": return validate_memory(data, ws_root)` check at line 3093, reached before `_EXEMPT_TOOLS`. Always reachable when tool_name is "memory".

**(c) Does the memory tool input schema match what `validate_memory()` expects?**
**THIS IS THE BUG.** The VS Code memory tool sends:
```json
{"tool_name": "memory", "tool_input": {"path": "/memories/", "command": "view"}}
```
But `validate_memory()` extracts the path with this sequence:
1. `tool_input.get("filePath")` → `None` (key is `"path"`, not `"filePath"`)
2. `data.get("filePath")` → `None`
3. `data.get("path")` → `None` (path is nested in `tool_input`, not at top level)

It **never checks `tool_input.get("path")`**, so no path is found → fails closed → returns `"deny"`.

**(d) Is the integrity hash stale?**
Not relevant — the gate runs and produces output (correctly denying). Hash staleness would block all calls.

---

## Fix

Add `tool_input.get("path")` as a fallback in `validate_memory()` path extraction, immediately after `tool_input.get("filePath")` fails:

```python
# Prefer nested tool_input key (VS Code hook format)
raw_path = tool_input.get("filePath")
if not isinstance(raw_path, str) or not raw_path:
    raw_path = tool_input.get("path")    # <-- ADDED: VS Code memory tool uses "path" key
if not isinstance(raw_path, str) or not raw_path:
    raw_path = data.get("filePath")
if not isinstance(raw_path, str) or not raw_path:
    raw_path = data.get("path")
```

---

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — one-line fix in `validate_memory()`

## Tests Written

- `tests/SAF-060/test_saf060_memory_path_key.py` — tests verifying both `filePath` and `path` key in `tool_input` are extracted correctly, plus decide() integration tests and the complete memory usage scenarios from the WP.

## Test Results

All tests passed (see test-results.csv).

---

## Iteration 1

Implementation complete. Root cause confirmed and fixed. All 8 new tests pass. No regressions in full suite.
