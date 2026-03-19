# FIX-011 Dev Log — Fix CI Spec File and Drop Intel Mac Build

## Summary

Fixes BUG-039: `launcher.spec` was untracked from git by FIX-005 (ran `git rm --cached launcher.spec`) to satisfy an INS-012 test. However, `launcher.spec` is a manually maintained PyInstaller spec file that CI needs to build the app. The `.gitignore` `*.spec` rule prevented re-adding it, causing all CI build jobs to fail with `ERROR: Spec file "launcher.spec" not found!`.

Also drops the `macos-intel-build` CI job per user decision — GitHub's macOS 14+ runners are ARM-only and Intel Python cannot be installed on Apple Silicon.

## Status

In Progress → Review

## Date

2026-03-14

## Files Changed

| File | Change |
|------|--------|
| `.gitignore` | Added `!launcher.spec` negation rule after `*.spec` |
| `.github/workflows/release.yml` | Removed entire `macos-intel-build` job block; updated `release` job `needs` to `[windows-build, macos-arm-build, linux-build]` |
| `tests/INS-012/test_ins012_gitignore.py` | Updated `test_gitignore_git_recognises_spec` to verify `launcher.spec` is TRACKED by git (not ignored) |
| `tests/INS-015/test_ins015_macos_build_jobs.py` | Marked intel-job-specific tests as skip; updated `test_macos_intel_job_exists` to assert absence |
| `tests/INS-015/test_ins015_edge_cases.py` | Marked intel-job-specific tests as skip; updated `test_macos_runners_are_distinct` to remove intel dependency |
| `docs/bugs/bugs.csv` | Added BUG-039 |
| `docs/workpackages/workpackages.csv` | Added FIX-011 row |
| `docs/test-results/test-results.csv` | Added TST-985 through TST-989 for FIX-011 tests |

## Git Operations

- `git add -f launcher.spec` — force-added launcher.spec back to git tracking
- Committed all changes on branch `fix-011`

## Tests Written

Located in `tests/FIX-011/test_fix011_spec_tracking.py`:

| Test | Description |
|------|-------------|
| `test_gitignore_has_spec_negation` | `.gitignore` contains `!launcher.spec` after `*.spec` |
| `test_launcher_spec_exists_on_disk` | `launcher.spec` exists at repository root |
| `test_release_yml_no_macos_intel_job` | `release.yml` has no `macos-intel-build` job |
| `test_release_job_needs_no_intel` | `release` job `needs` does not include `macos-intel-build` |
| `test_release_job_needs_exact` | `release` job `needs` is exactly `[windows-build, macos-arm-build, linux-build]` |

## Decisions Made

1. **`!launcher.spec` negation approach**: Rather than removing the `*.spec` rule (which would cause all auto-generated PyInstaller spec files to be tracked), we added a specific negation `!launcher.spec`. This preserves the intent of the original `*.spec` rule while allowing the one manually-maintained file to be tracked.

2. **Dropping macos-intel-build entirely**: Per user decision. GitHub Actions macOS 14+ runners are ARM-only (Apple Silicon). There is no path to running Intel x64 Python on these runners. The Intel Mac market share is declining rapidly and this build cannot be fixed without GitHub providing Intel runners, which they have deprecated.

3. **INS-015 intel-specific tests**: Tests for the now-removed `macos-intel-build` job are marked as skipped with explanatory reason. The `test_macos_intel_job_exists` test is updated to assert absence (the correct regression test for this change). ARM build tests are unaffected.

## Known Limitations

None. The fix is complete and all 3 remaining CI build jobs will find `launcher.spec`.
