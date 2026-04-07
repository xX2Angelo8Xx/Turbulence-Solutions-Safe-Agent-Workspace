# Dev Log — MNT-030: Add --retag mode to release.py

## Status
In Progress

## Assigned To
Developer Agent

## Date
2026-04-07

## ADR Review
- **ADR-001** (Use Draft GitHub Releases for Pre-Release Testing) — relevant. The `--retag` mode creates an annotated tag and pushes it to origin, which triggers the CI/CD workflow that enforces draft-only GitHub Releases. The new mode is consistent with ADR-001: retagging does not bypass the draft-release constraint.

---

## Implementation Plan

Add a `--retag` flag to `scripts/release.py` that handles the scenario where all version files already match the target version (e.g., after fixing bugs post-tag without bumping the version number).

### Scope
- `scripts/release.py` — add `--retag` argument and `retag_release()` function
- `tests/MNT-030/` — new test file covering all 5 test cases

### New CLI Flag
`--retag` is mutually exclusive with normal release mode. When set, the script skips all version file updates and instead:
1. Validates version format (X.Y.Z)
2. Checks we are on `main` branch (unless `--dry-run`)
3. Checks working tree is clean (unless `--dry-run`)
4. Verifies all 5 version files already contain the target version — aborts if any don't match
5. Deletes existing local tag (tolerates missing local tag)
6. Deletes existing remote tag (tolerates missing remote tag)
7. Creates new annotated tag on HEAD
8. Pushes new tag to origin

### Dry-run
`--retag --dry-run` prints the plan without making any changes.

---

## Implementation Summary

Added `--retag` support to `scripts/release.py` with the following changes:

1. **`_run_git_optional()`** — new helper that runs a git command and returns `None` instead of raising on non-zero exit. Used for delete-local-tag and delete-remote-tag, which must tolerate absence gracefully.

2. **`retag_release()`** — new function encapsulating the full retag workflow:
   - Validates branch and clean working tree (skipped in dry-run)
   - Verifies all 5 version files already contain the target version; aborts if any don't match
   - Deletes local tag (tolerates absence)
   - Deletes remote tag (tolerates absence)
   - Creates new annotated tag on HEAD
   - Pushes new tag to origin
   - Supports dry-run (no-op, prints plan)

3. **`main()`** — added `--retag` argparse argument; dispatches to `retag_release()` before entering normal release flow. Version format validation runs before the dispatch.

Normal release flow is unchanged.

## Files Changed

- `scripts/release.py` — added `_run_git_optional()`, `retag_release()`, and `--retag` CLI flag
- `tests/MNT-030/test_mnt030_retag.py` — 10 unit tests covering all acceptance criteria
- `docs/workpackages/MNT-030/dev-log.md` — this file
- `docs/workpackages/workpackages.jsonl` — status updated to In Progress → Review

## Tests Written

| Test | Description |
|------|-------------|
| `test_retag_all_files_match_succeeds` | All version files match → completes, correct git command sequence |
| `test_retag_version_mismatch_aborts` | All files wrong version → SystemExit(1) with clear error |
| `test_retag_partial_mismatch_aborts` | One file wrong version → SystemExit(1) naming the offending file |
| `test_retag_dry_run_no_git_calls` | dry_run=True → no git calls, prints plan |
| `test_retag_dry_run_aborts_on_mismatch` | dry_run=True + mismatch → still aborts |
| `test_normal_mode_dry_run_still_works` | Normal --dry-run still works (regression) |
| `test_normal_mode_retag_flag_absent` | main() without --retag never calls retag_release() |
| `test_retag_missing_local_tag_continues` | Missing local tag → skips gracefully |
| `test_retag_missing_remote_tag_continues` | Missing remote tag → skips gracefully |
| `test_retag_both_tags_missing_is_fine` | Both tags absent → succeeds, 2× "did not exist" messages |

All 10 tests pass (logged as TST-2748).

## Known Limitations

None.
