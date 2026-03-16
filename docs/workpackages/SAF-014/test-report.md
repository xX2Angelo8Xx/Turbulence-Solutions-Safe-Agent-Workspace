# Test Report — SAF-014

**Tester:** Tester Agent
**Date:** 2026-03-16
**Iteration:** 1

## Summary

SAF-014 adds 8 read-only file inspection commands to the terminal allowlist
(`get-content`, `gc`, `select-string`, `findstr`, `grep`, `wc`, `file`, `stat`).
All 8 entries are configured with `path_args_restricted=True` and
`allow_arbitrary_paths=False`, meaning every path argument is zone-checked before
the command is allowed to proceed.

All 45 developer tests pass. All 16 Tester edge-case tests pass. Full regression
(2280 tests) introduces zero new failures — the 8 failures present are all
pre-existing, unrelated to this workpackage.

One known limitation is documented as BUG-048: Windows-style `/S`-prefixed flags
used with `findstr` (e.g. `findstr /S pattern project/file.py`) are incorrectly
denied because `_validate_args` only skips dash-prefixed (`-`) flag tokens. The
slash token `/S` is misidentified as an absolute path outside the workspace and
zone-checked to "deny". This is fail-safe (over-restrictive) and is a pre-existing
architectural limitation of `_validate_args` exposed by SAF-014 as the first WP
to add a Windows-native `/`-flag command.

**Verdict: PASS**

---

## Tests Executed

### Developer tests (45 tests — TST-1237 to TST-1281)

| Test | Type | Result | Notes |
|------|------|--------|-------|
| All 45 `test_saf014_read_commands.py` tests | Unit / Security | Pass | Confirmed by developer; re-verified by Tester |
| Full regression (TST-1282) | Regression | Pass | 2264 passed / 8 pre-existing failures / 29 skipped |

### Tester edge-case tests

| TST-ID | Test | Type | Result | Notes |
|--------|------|------|--------|-------|
| TST-1283 | `test_get_content_noagentzone_denied` | Security | Pass | NoAgentZone path correctly denied |
| TST-1284 | `test_gc_noagentzone_denied` | Security | Pass | PowerShell alias also denies NoAgentZone |
| TST-1285 | `test_grep_noagentzone_denied` | Security | Pass | Unix grep also denies NoAgentZone |
| TST-1286 | `test_path_traversal_project_to_github_denied` | Security | Pass | `project/../.github/secret` normalised to `.github/secret` → deny |
| TST-1287 | `test_path_traversal_stat_project_to_vscode_denied` | Security | Pass | `project/../.vscode/settings.json` normalised → deny |
| TST-1288 | `test_dollar_sign_unix_variable_denied` | Security | Pass | `$HOME/secret` → `$` in token → immediate deny |
| TST-1289 | `test_dollar_sign_powershell_env_variable_denied` | Security | Pass | `$env:APPDATA/file.txt` → `$` → deny |
| TST-1290 | `test_stat_absolute_unix_path_outside_workspace_denied` | Security | Pass | `/etc/passwd` outside workspace → deny |
| TST-1291 | `test_get_content_absolute_windows_path_outside_workspace_denied` | Security | Pass | `C:/Users/Administrator/secret.txt` outside workspace → deny |
| TST-1292 | `test_grep_recursive_flag_project_allowed` | Unit | Pass | `-r` skipped as dash-flag; `project/` zone-check → allow |
| TST-1293 | `test_grep_recursive_flag_github_denied` | Security | Pass | `-r` skipped; `.github/` zone-check → deny |
| TST-1294 | `test_grep_recursive_dot_workspace_root_denied` | Security | Pass | `.` is path-like (starts with `.`); workspace root → deny (2-tier model) |
| TST-1295 | `test_grep_multiple_project_paths_allowed` | Unit | Pass | Two project paths both zone-check to allow |
| TST-1296 | `test_wc_multiple_project_paths_allowed` | Unit | Pass | Two project files both allowed |
| TST-1297 | `test_findstr_slash_flag_is_denied_known_limitation` | Unit | Pass | `/S` misidentified as path → deny (documents BUG-048 behaviour) |
| TST-1298 | `test_wc_flag_only_no_path_allowed` | Unit | Pass | `wc -l` with no path → no zone-check → allow |
| TST-1299 | Full regression (Tester run) | Regression | Pass | 2280 passed / 8 pre-existing failures / 29 skipped — zero new failures |

---

## Bugs Found

- **BUG-048**: `findstr /S` (and any command using Windows-style `/FLAG` arguments)
  is incorrectly denied. `_validate_args` skips only dash-prefixed (`-`) flag tokens.
  A `/S` token is treated as a path, normalised to the absolute path `/s`, zone-checked
  to "deny" (outside workspace root), and the command is rejected. This is
  fail-safe but may surprise users who expect `findstr` to work with its native
  Windows flag syntax. Logged in `docs/bugs/bugs.csv`.

---

## TODOs for Developer

None. All acceptance criteria are met. BUG-048 is a known architectural limitation
and does not block the WP's goals (basic zone-restricted file inspection works
correctly for all 8 commands).

---

## Verdict

**PASS** — mark SAF-014 as Done.

All 61 tests pass (45 developer + 16 Tester edge-case). Full regression introduces
zero new failures. All 8 new allowlist commands correctly restrict path arguments
to the project zone, block restricted zones, prevent path traversal, block variable
injection, and reject absolute paths outside the workspace.
