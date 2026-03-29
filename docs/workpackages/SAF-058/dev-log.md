# SAF-058 Dev Log — Move get_changed_files from always-allow to conditional check

## WP Details
- **ID:** SAF-058
- **Category:** SAF
- **Status:** In Progress
- **Assigned To:** Developer Agent
- **User Story:** US-062
- **Depends On:** SAF-057
- **Bug Reference:** BUG-136

## Problem
`get_changed_files` was added to `_ALWAYS_ALLOW_TOOLS` in SAF-052 as a quick fix.
This bypasses all zone enforcement — if a git repo exists at workspace root, the tool
can expose file paths from denied zones (.github/, .vscode/, NoAgentZone/).

## Solution
Remove `get_changed_files` from `_ALWAYS_ALLOW_TOOLS`. Add a dedicated
`validate_get_changed_files()` function in `security_gate.py` with the following logic:

1. Check if `.git/` exists at workspace root (outside the project folder) → **deny**
   (git tracks the entire workspace, including denied zones)
2. Check if `.git/` exists inside the project folder → **allow**
   (git is scoped to the project folder only; no denied zone exposure)
3. If no `.git/` exists anywhere → **allow**
   (tool returns a harmless "no repository" message)

Integrate into `decide()` before the `_ALWAYS_ALLOW_TOOLS` check is replaced.

## Implementation

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py`
  - Removed `get_changed_files` from `_ALWAYS_ALLOW_TOOLS`
  - Added `validate_get_changed_files(ws_root: str) -> str` function
  - Added `if tool_name == "get_changed_files"` branch in `decide()`

### Key Design Decisions
- Fail-closed: on any OS error checking for `.git/`, deny.
- The `.git` check only looks one level: `ws_root/.git` vs `ws_root/<project>/.git`.
  This avoids traversing deeper and matches the threat model (workspace root git).
- No path arguments to extract — the tool takes no filePath parameter; the
  validation is purely based on `.git/` placement.

## Tests Written
- `tests/SAF-058/test_saf058_get_changed_files_conditional.py`
  - `get_changed_files` with `.git/` at workspace root → denied
  - `get_changed_files` with `.git/` inside project folder → allowed
  - `get_changed_files` with no `.git/` at all → allowed
  - `get_changed_files` is NOT in `_ALWAYS_ALLOW_TOOLS`
  - OS error during `.git/` check → denied (fail-closed)

## Test Results
- All tests passed (see test-results.csv)

## Known Limitations
- None

---

## Iteration 1 — Initial Implementation
- Date: 2026-03-30
- Changes: Initial implementation complete
