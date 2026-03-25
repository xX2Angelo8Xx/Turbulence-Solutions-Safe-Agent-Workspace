# Dev Log — SAF-050

**WP:** SAF-050  
**Title:** Prevent grep_search information leak on workspace root files  
**Branch:** SAF-050/grep-search-leak  
**Assigned To:** Developer Agent  
**Status:** Review  

---

## Summary

BUG-115 reported that `grep_search` returned content from workspace root files (e.g. `README.md`) that `read_file` denied. After SAF-046 enables workspace root reads for `read_file`, the original leak is resolved (both tools now allow workspace root files). However, an inconsistency remained: `grep_search` with an explicit `includePattern` targeting a workspace root file was denied by `_validate_include_pattern` even though `read_file` on the same file was allowed.

**Root cause:** `_validate_include_pattern` used `zone_classifier.classify()` to validate patterns. Since `classify()` only returns `"allow"` for paths inside the project folder, any `includePattern` that does not start with the project folder name was blocked — including legitimate general globs (`*.py`, `**/*.ts`) and workspace root file patterns (`pyproject.toml`, `README.md`).

---

## Analysis

After SAF-046:
- `read_file "pyproject.toml"` → ALLOWED via `is_workspace_root_readable()`
- `grep_search` with no `includePattern` → ALLOWED (trusts VS Code `search.exclude`)
- `grep_search` with `includePattern: "pyproject.toml"` → DENIED ❌ (inconsistency)
- `grep_search` with `includePattern: "*.py"` → DENIED ❌ (over-restriction)

The `search.exclude` settings in `.vscode/settings.json` already exclude `.github`, `.vscode`, and `**/NoAgentZone` from VS Code search results, providing defense-in-depth.

**Principle (from WP):** no file accessible via one tool but denied via another.

---

## Implementation

### Change 1 — `templates/agent-workbench/.github/hooks/scripts/security_gate.py`

**Added:** `_include_pattern_targets_deny_zone(norm_pattern, ws_root)` helper function.

Replaces the broad `zone_classifier.classify()` check in `_validate_include_pattern` with a targeted deny-zone check:
- For **relative patterns**: denies only if the first path component is a deny zone name (`.github`, `.vscode`, `noagentzone`). General globs like `*.py` and workspace root files like `pyproject.toml` pass.
- For **absolute patterns**: uses `zone_classifier.classify()` first (allows project folder paths), then `zone_classifier.is_workspace_root_readable()` (allows workspace root files per SAF-046), then denies anything else.

**Modified:** `_validate_include_pattern` to call the new helper instead of `zone_classifier.classify()`.

**Modified:** `validate_grep_search` — added `is_workspace_root_readable` fallback to the `filePath` zone check path, making it consistent with `read_file`'s SAF-046 behavior.

---

## Files Changed

- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — core fix
- `docs/workpackages/workpackages.csv` — status update
- `docs/bugs/bugs.csv` — BUG-115 Fixed In WP set to SAF-050
- `tests/SAF-050/` — new test suite

---

## Tests Written

See `tests/SAF-050/test_saf050_grep_search_leak.py`.

Test coverage:
1. `includePattern: "pyproject.toml"` → allow (SAF-046 consistency)
2. `includePattern: "README.md"` → allow (workspace root file)
3. `includePattern: "*.py"` → allow (general glob, no deny zone)
4. `includePattern: "**/*.ts"` → allow (general glob)
5. `includePattern: "src/**"` → allow (relative path, not a deny zone)
6. `includePattern: ".github/**"` → deny (explicit deny zone, unchanged)
7. `includePattern: ".vscode/settings.json"` → deny (explicit deny zone)
8. `includePattern: "NoAgentZone/**"` → deny (explicit deny zone)
9. No `includePattern` → allow (search.exclude handles protection)
10. Absolute path to workspace root file → allow
11. Absolute path to denied zone → deny  
12. `includeIgnoredFiles: True` → deny (unchanged)
13. `decide()` integration: workspace root file pattern → allow
14. `decide()` integration: denied zone pattern → deny
15. Regression: SAF-046 consistency — read_file-allowed paths also grep_search-allowed  

---

## Known Limitations

The no-`includePattern` case relies on VS Code's `search.exclude` to exclude `.github/`, `.vscode/`, and `**/NoAgentZone/**`. This is intentional: the security gate can only allow or deny the grep_search call as a whole, not filter individual results. The `search.exclude` configuration is under the security system's control.

---

## Iteration 2 — BUG-127 & BUG-128 Fixes

**Tester findings (from test-report.md):**
- **BUG-127** — `_include_pattern_targets_deny_zone` used `any(c in _WILDCARD_DENY_ZONES for c in components)` which incorrectly denied patterns like `project/.github/**` (deny zone nested inside the agent's project folder).
- **BUG-128** — `update_hashes.py` was not run after modifying `security_gate.py`, leaving `_KNOWN_GOOD_GATE_HASH` stale.

**Fix for BUG-127:** Replaced the `any()` check with a left-to-right component walk. A deny-zone component is only blocked when no project-folder anchor precedes it. A "project-folder anchor" is specifically the agent's project folder name (from `zone_classifier.detect_project_folder(ws_root)`), not any arbitrary concrete directory. This ensures:
- `project/.github/**` → ALLOWED (project folder anchors the deny zone)
- `project/src/.vscode/**` → ALLOWED (project folder anchor seen first)
- `src/.github/**` → DENIED (`src` is not the project folder)
- `**/.github/**` → DENIED (wildcard is not a project folder anchor)
- `*/.github/**` → DENIED (wildcard is not a project folder anchor)

**Fix for BUG-128:** Ran `update_hashes.py` after fixing BUG-127.

**Tests added:** `tests/SAF-050/test_saf050_tester_edge_cases.py` (8 tests — written by Tester, verified by Developer).

**All 49 SAF-050 tests pass. SAF-003 brace-expansion regression also verified (57/57 passing).**
