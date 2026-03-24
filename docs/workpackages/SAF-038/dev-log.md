# SAF-038 Dev Log — Allow memory and create_directory in project

**WP ID:** SAF-038  
**Branch:** SAF-038/memory-create-directory  
**Assigned To:** Developer Agent  
**Status:** Review  
**Date Started:** 2026-03-24  

---

## Objective

Update `security_gate.py` (in `templates/coding/.github/hooks/scripts/`) to allow the `memory` and `create_directory` tools when their target paths are inside the project folder. Both tools must be denied when targeting paths outside the project folder.

Satisfies ACs 1–2 and 5–6 of US-035.

---

## Implementation Plan

1. Add `memory` and `create_directory` to `_EXEMPT_TOOLS` with SAF-038 comment.
2. Add `validate_memory(data, ws_root)` — extracts `filePath` (via `tool_input` then top-level), zone-checks, allow only if zone == "allow".
3. Add `validate_create_directory(data, ws_root)` — extracts `dirPath` (via `tool_input` then top-level), zone-checks, allow only if zone == "allow".
4. In `decide()`, dispatch both tools before the `_EXEMPT_TOOLS` fallback.
5. Run `update_hashes.py` to re-embed SHA256 hash.
6. Write tests in `tests/SAF-038/`.

---

## Files Changed

- `templates/coding/.github/hooks/scripts/security_gate.py` — core implementation
- `tests/SAF-038/` — new test directory
- `tests/SAF-038/__init__.py` — package marker
- `tests/SAF-038/conftest.py` — zone_classifier patch fixture
- `tests/SAF-038/test_saf038_memory_create_directory.py` — test suite

---

## Implementation Summary

### `validate_memory(data, ws_root)`
- Extracts path from `filePath` in `tool_input` (VS Code hook format), then falls back to top-level `filePath` or `path`.
- Returns "deny" if no path found (fail closed).
- Zone-checks via `zone_classifier.classify()`.
- Blocks git internals even within the project folder.
- Returns "allow" only for paths in the project folder.

### `validate_create_directory(data, ws_root)`
- Extracts `dirPath` from `tool_input`, then from top-level data.
- Returns "deny" if no `dirPath` found (fail closed).
- Zone-checks via `zone_classifier.classify()`.
- Blocks git internals even within the project folder.
- Returns "allow" only for paths in the project folder.

### `decide()` additions
- Both handlers dispatched before the `_EXEMPT_TOOLS` fallback block.
- Both tool names added to `_EXEMPT_TOOLS` (for documentation consistency with `get_errors` pattern).

---

## Tests Written

See `tests/SAF-038/test_saf038_memory_create_directory.py`.

Test categories:
- Unit: `validate_memory()` direct calls
- Unit: `validate_create_directory()` direct calls
- Security: `decide()` dispatches correctly for both tools
- Bypass: adversarial payloads (missing path, wrong type, traversal, deny zones)
- Cross-platform: Windows/POSIX/WSL path variants

---

## Known Limitations

None — implementation is complete.

---

## Iteration 1

(Initial implementation — 2026-03-24)
