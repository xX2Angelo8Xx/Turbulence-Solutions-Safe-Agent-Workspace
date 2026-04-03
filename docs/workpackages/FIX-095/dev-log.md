# Dev Log — FIX-095: Fix update_architecture.py Exit Code

**WP ID:** FIX-095  
**Branch:** FIX-095/fix-update-arch-exit-code  
**Status:** In Progress  
**Assigned To:** Developer  
**Date:** 2026-04-04  

---

## ADR Check

No relevant ADRs found in `docs/decisions/index.csv`. ADR-001 through ADR-006 cover release, CI, templates, and ADR management — none pertain to the architecture sync script.

---

## Problem Statement

`scripts/update_architecture.py` — the `main()` function always calls `return 0` regardless of whether `update_architecture()` succeeded or failed. The inner `update_architecture()` function returns `False` on two failure conditions:

1. `docs/architecture.md` does not exist
2. The `## Repository Structure` pattern/section is not found in the file

`scripts/finalize_wp.py` calls `update_architecture.py` as a subprocess via `_sync_architecture()`, which checks `result.returncode`. Because `main()` always returned 0, the failure branch in `_sync_architecture()` was unreachable — sync failures were silently treated as successes.

Additionally, `update_architecture()` also returned `False` for non-error conditions (already up to date, dry-run), which would have incorrectly triggered a failure exit code if `main()` had used the return value naively.

---

## Implementation

### Changes to `scripts/update_architecture.py`

**`update_architecture()` function:** Changed the two non-error `False` returns to `True`:
- "Already up to date" case → `return True` (success, nothing to do)
- Dry-run case → `return True` (success, no write performed)

This makes `False` an unambiguous error signal from the function.

**`main()` function:** Changed from unconditional `return 0` to:
```python
result = update_architecture(args.dry_run)
return 0 if result else 1
```

This propagates the failure correctly to the calling process (e.g. `finalize_wp.py`).

---

## Files Changed

- `scripts/update_architecture.py` — fix exit code logic in `main()`, clarify return semantics of `update_architecture()`

---

## Tests Written

- `tests/FIX-095/test_fix095_update_arch_exit_code.py`
  - `test_exit_code_file_not_found` — main() returns 1 when architecture.md is absent
  - `test_exit_code_pattern_not_found` — main() returns 1 when section header is missing
  - `test_exit_code_success_no_change` — main() returns 0 when already up to date
  - `test_exit_code_success_updated` — main() returns 0 when file is successfully updated
  - `test_exit_code_dry_run` — main() returns 0 in dry-run mode (no write)

---

## Known Limitations

None.
