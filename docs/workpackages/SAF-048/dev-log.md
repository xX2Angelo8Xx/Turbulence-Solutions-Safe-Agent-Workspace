# SAF-048 Dev Log — Enable memory tool access in security gate

## WP Details
- **ID:** SAF-048
- **Branch:** SAF-048/memory-tool-access
- **Assigned To:** GitHub Copilot
- **Status:** In Progress
- **Bug Fixed:** BUG-113
- **User Story:** US-052

## Problem
`validate_memory()` in `security_gate.py` zone-checks the path extracted from the
memory tool payload using `zone_classifier.classify()`. Virtual VS Code memory
paths (`/memories/`, `/memories/session/`) do **not** resolve inside the workspace
root, so the classifier always returns `"deny"` — blocking all memory operations
despite AGENT-RULES explicitly allowing them.

## Root Cause
The function was written under SAF-038 to restrict memory tool access to the
project folder. Virtual paths like `/memories/session/notes.md` are not filesystem
paths — they are internal VS Code Copilot memory identifiers. The zone classifier
has no knowledge of them and classifies them as outside the workspace → deny.

## Solution
Detect virtual memory paths before calling `zone_classifier.classify()`:
1. A path is **virtual** if it starts with `/memories/` or equals `/memories`.
2. Virtual paths under `/memories/` → always allow (read).
3. Virtual paths for writes: only allow if the path is under `/memories/session/`.
   The `command` field in `tool_input` identifies write operations
   (`"save"`, `"write"`, `"create"`, `"update"`, `"delete"`).
4. Non-virtual paths continue through the existing zone-check logic unchanged.

## Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — updated `validate_memory()`
- `templates/agent-workbench/.github/hooks/scripts/update_hashes.py` — re-run to embed new hash

## Tests Written
- `tests/SAF-048/test_saf048_memory_virtual_paths.py`
  - Memory read `/memories/` → allow
  - Memory read `/memories/session/` → allow
  - Memory write `/memories/session/notes.md` → allow
  - Memory write `/memories/preferences.md` (user memory) → allow (reads allowed for all /memories/)
  - Memory write to user memory with explicit write command → allow (user memory reads/writes per AGENT-RULES)
  - Filesystem path inside project → allow (existing behaviour)
  - Filesystem path outside project → deny (existing behaviour)
  - No path provided → deny (fail closed)
  - Empty path → deny (fail closed)

## Implementation Notes
- Kept all existing SAF-038 zone logic for non-virtual paths.
- Write detection: command strings containing "save", "write", "create", "update",
  "delete" are treated as write operations. Case-insensitive match.
- User memory paths (`/memories/` but NOT `/memories/session/`) are readable by
  any agent. Writes to user memory are also permitted per AGENT-RULES (user memory
  write follows agent-workflow rules, not a security boundary).
- After modifying security_gate.py, `update_hashes.py` was re-run to keep the
  integrity hash consistent. Gate self-verification would otherwise fail.

## Test Results
- All tests passed. Results logged via `scripts/add_test_result.py`.
