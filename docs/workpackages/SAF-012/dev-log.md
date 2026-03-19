# SAF-012 Dev Log — Redesign Zone Classifier for Deny-by-Default

## Overview

Rewrite `zone_classifier.py` to implement a 2-tier zone model: "allow" (project folder) and "deny" (everything else). Remove the "ask" return value. The classifier must auto-detect the project folder name at runtime and never return "ask".

- **WP ID:** SAF-012
- **User Story:** US-018
- **Branch:** SAF-012/deny-by-default-zone-classifier
- **Agent:** Developer Agent
- **Date started:** 2026-03-16

---

## Files Changed

| File | Change |
|------|--------|
| `Default-Project/.github/hooks/scripts/zone_classifier.py` | Rewrote 2-tier model; added `detect_project_folder()`; removed `_ALLOW_DIR` constant; removed "ask" return |
| `templates/coding/.github/hooks/scripts/zone_classifier.py` | Identical copy of above |

---

## Implementation Summary

### Changes Made

1. **Removed `_ALLOW_DIR = "project"` constant** — replaced with a runtime detection function.

2. **Added `detect_project_folder(workspace_root: Path) -> str`** — lists immediate subdirectories of `workspace_root`, filters out system folders (`.github`, `.vscode`, `noagentzone`) using case-insensitive comparison, and returns the first non-system folder alphabetically. Raises `RuntimeError` if none found.

3. **Changed `ZoneDecision = Literal["allow", "deny", "ask"]`** to `ZoneDecision = Literal["allow", "deny"]`.

4. **Updated `classify()` to never return "ask"** — any path not inside the detected project folder returns "deny". The `_DENY_DIRS` set is preserved for defense-in-depth (explicit deny for `.github`, `.vscode`, `noagentzone`).

5. **Updated Method 2 `_ALLOW_PATTERN`** — replaced the hardcoded `r"/project(/|$)"` with a dynamically-generated pattern based on the detected project folder name.

6. **Updated docstring** — reflects 2-tier model.

7. **Both copies identical** — `Default-Project/` and `templates/coding/` are kept in sync.

### Design Decisions

- The `detect_project_folder()` function is called inside `classify()` on each invocation. The workspace root is already passed in as a parameter. This avoids any module-level state and ensures the detection always reflects the actual filesystem.
- `_DENY_DIRS` is preserved as an explicit deny set (defense in depth). This means `.github/`, `.vscode/`, and `noagentzone/` paths are denied even if somehow they were selected as the "project folder" (which is prevented by the filtering).
- If no project folder is detected, `classify()` falls back to "deny" (fail-closed behavior).
- All existing bypass protections (path traversal, case variation, control character stripping) are preserved via `normalize_path()`.

---

## Tests Written

Tests are in `tests/SAF-012/test_saf012_zone_classifier.py`.

| Test | Category | Description |
|------|----------|-------------|
| `test_detect_project_folder_named_project` | Unit | Detects folder named "Project" |
| `test_detect_project_folder_named_matlabdemo` | Unit | Detects folder named "MatlabDemo" |
| `test_detect_project_folder_named_myapp` | Unit | Detects folder named "MyApp" |
| `test_detect_project_folder_first_alphabetically` | Unit | Multiple non-system folders → first alphabetically |
| `test_detect_project_folder_no_project_raises` | Unit | Edge: all system folders → RuntimeError |
| `test_detect_ignores_system_folders_case_insensitive` | Unit | Case-insensitive system folder exclusion |
| `test_classify_allow_project_root` | Unit | Path inside detected project folder → allow |
| `test_classify_allow_project_nested` | Unit | Nested path inside project folder → allow |
| `test_classify_deny_github` | Security | .github/ → deny |
| `test_classify_deny_vscode` | Security | .vscode/ → deny |
| `test_classify_deny_noagentzone` | Security | NoAgentZone/ → deny |
| `test_classify_deny_root_file` | Unit | Root-level file (README.md) → deny |
| `test_classify_deny_non_project_subdir` | Unit | Non-project subdirectory → deny |
| `test_classify_never_returns_ask` | Security | classify() never returns "ask" for any input |
| `test_classify_deny_when_no_project_folder` | Unit | Edge: no project folder → deny (fail-closed) |
| `test_classify_case_insensitive_deny` | Security | Case variation of deny dirs → deny |
| `test_bypass_path_traversal` | Security | Path traversal into deny zone → deny (bypass attempt) |
| `test_bypass_sibling_prefix` | Security | projectevil/ does not match project/ → deny |
| `test_detect_project_folder_uses_filesystem` | Unit | detect_project_folder() uses os.listdir (mocked) |

---

## Test Results

All tests passed. See `docs/test-results/test-results.csv` for logged results.

---

## Known Limitations

- `detect_project_folder()` only looks at immediate subdirectories (depth 1). This is intentional — the project folder is always a direct child of the workspace root.
- If multiple non-system folders exist, the first alphabetically is chosen. This is documented behavior.
- SAF-013 must update `security_gate.py` to remove all "ask" handling; this WP intentionally leaves `security_gate.py` unchanged.
