# Test Report — INS-027

**Tester:** Tester Agent
**Date:** 2026-03-30
**Iteration:** 1

## Summary

INS-027 adds source-mode detection (`is_source_mode()`), git-based version
checking (`_get_local_git_version()`, `check_for_update_source()`), and
git-pull/pip-install update application (`apply_source_update()`) to the
launcher's updater and applier modules.  All 16 developer tests pass.  The
tester added 29 additional edge-case tests covering `_get_local_git_version()`
directly, `sys._MEIPASS` boundary values, subprocess timeout propagation
semantics, platform-specific pip path resolution (Windows vs Unix), and
security (shell=False, list args).  All 111 tests in INS-027 + INS-011 pass
with no regressions.

**Verdict: PASS**

## Tests Executed

| Test | Type | Result | Notes |
|------|------|--------|-------|
| TST-2270 — INS-027 developer unit tests (16) | Unit | Pass | Developer-written: is_source_mode, check_for_update_source, apply_source_update, apply_update dispatch |
| TST-2271 — INS-027 tester edge-case tests (29) | Unit | Pass | _get_local_git_version direct (8), MEIPASS boundary (3), update-source edge cases (4), pip path resolution Win/Unix (3), subprocess timeouts (2), backward compat (4), shell=False security (5) |
| TST-2272 — INS-027 + INS-011 regression (111) | Regression | Pass | 45 INS-027 + 66 INS-011; no regressions introduced |

## Code Review Findings

### Correct implementations
- `is_source_mode()`: truthiness check on `_MEIPASS` is correct; `.is_dir()` properly excludes worktree `.git` files.
- `_get_local_git_version()`: catches all exceptions including `TimeoutExpired` via bare `except Exception`; returns `"0.0.0"` fallback for all failure paths except the empty-stdout edge case (see bug below).
- `check_for_update_source()`: `check=False` on `git fetch` is correct — a fetch failure should not abort the update check.  The outer `except Exception` swallows network errors silently, matching the existing pattern in `check_for_update()`.
- `apply_source_update()`: all subprocess calls use list args and `shell=False` (default); timeouts are set (60 s for git pull, 120 s for pip install); `check=False` with explicit `returncode` inspection is the correct safe pattern.
- `apply_update()` backward compatibility: binary path is fully unchanged; `None` cleanly dispatches to source mode without touching `_validate_installer_path`.
- `_REPO_ROOT` injection via `repo_root` parameter makes all functions testable without filesystem side-effects.

## Bugs Found

- **BUG-153** — `apply_source_update` docstring contract: `TimeoutExpired` not wrapped as `RuntimeError` (Low, logged in docs/bugs/bugs.csv).  The docstring states "Raises RuntimeError on any failure", but `subprocess.TimeoutExpired` from `git pull` or `pip install` propagates to the caller unwrapped.  Non-blocking for this WP; callers that only expect `RuntimeError` on failure may be surprised.  Documented by two tester tests.

## TODOs for Developer

None — all acceptance criteria satisfied.  BUG-153 is logged for a future
workpackage if the developer wants to harden the exception contract.

## Verdict

**PASS — mark WP as Done.**
