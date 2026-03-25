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

---

## Iteration 2 — Security Fixes (2026-03-25)

### Tester Findings (Iteration 1)
Tester returned WP with 18 security failures across 4 categories:
- **BUG-121 (High):** Path traversal READ bypass — `/memories/../../.github/secrets` bypasses virtual check
- **BUG-122 (High):** `session/../` WRITE bypass — `/memories/session/../preferences.md` escapes session boundary
- **BUG-123 (Medium):** Null bytes and Unicode control/format characters (RLO U+202E, BOM U+FEFF) passed through unchecked
- **BUG-124 (Low):** No `.lower()` — `/MEMORIES/session/` denied instead of allowed

### Root Cause
`norm_virtual = raw_path.replace("\\", "/")` normalised backslashes but did not resolve `..` segments, reject bad characters, or lowercase the path before the `/memories/` prefix check.

### Fixes Applied
In `validate_memory()` in `templates/agent-workbench/.github/hooks/scripts/security_gate.py`:

1. **BUG-123:** Added character validation immediately after backslash normalization — rejects paths containing null bytes (`\x00`) or any Unicode character in category `Cc` (control) or `Cf` (format), using `unicodedata.category()`. Added `import unicodedata` to module imports.

2. **BUG-121 / BUG-122:** Applied `posixpath.normpath()` after bad-character check to resolve all `..` and `.` segments before the `/memories/` prefix check. This collapses `/memories/../../.github` to `/.github` (not a memory path → zone classifier → deny) and `/memories/session/../preferences.md` to `/memories/preferences.md` (not a session path → write denied).

3. **BUG-124:** Applied `.lower()` to `norm_virtual` after `normpath()` so `/MEMORIES/session/` and `/Memories/Session/` are recognized as virtual memory paths identical to `/memories/session/`.

4. Re-ran `update_hashes.py` to update `_KNOWN_GOOD_GATE_HASH`.

### Files Changed
- `templates/agent-workbench/.github/hooks/scripts/security_gate.py` — fixed `validate_memory()`; added `import unicodedata`
- `docs/bugs/bugs.csv` — BUG-121, BUG-122, BUG-123, BUG-124 marked Closed with Fixed In WP = SAF-048

### Tests
- All 57 SAF-048 tests pass (33 developer + 24 tester edge-case tests including the 18 previously failing)
- Results logged as TST-2188

---

## Iteration 3 — SAF-038 Regression Fix (2026-03-25)

### Tester Findings (Iteration 2)
Tester returned WP with 1 regression (BUG-125, High):
- `tests/SAF-038/test_saf038_edge_cases.py::TestNullByteInjection::test_memory_null_byte_in_project_path_allow` expected `allow`, got `deny`.
- Root cause: SAF-048 Iteration 2 BUG-123 fix adds a null-byte check in `validate_memory()` that fires before `zone_classifier`. The old behaviour relied on `zone_classifier.normalize_path` stripping the null byte and then allowing the path — an accidental weakness.

### Resolution — Option A (policy clarification)
Updated `tests/SAF-038/test_saf038_edge_cases.py`:
- Renamed `test_memory_null_byte_in_project_path_allow` → `test_memory_null_byte_in_project_path_deny`.
- Changed assertion from `allow` to `deny`.
- Updated docstring to document this as an intentional security improvement: null bytes have no legitimate use in any file path and should be denied regardless of whether the rest of the path resolves inside the project folder.

No changes to `security_gate.py` — the SAF-048 null-byte check is correct and intentional.

### BUG-125 Closed
BUG-125 marked Closed in `docs/bugs/bugs.csv` with Fixed In WP = SAF-048.

### Files Changed
- `tests/SAF-038/test_saf038_edge_cases.py` — test renamed and assertion updated

### Tests
- All SAF-048 tests pass; all SAF-038 tests pass (0 failures).
