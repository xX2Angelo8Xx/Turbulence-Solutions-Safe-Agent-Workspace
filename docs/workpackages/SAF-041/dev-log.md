# SAF-041 Dev Log — Add shell utility commands to terminal allowlist

## Status
Review

## Assigned To
Developer Agent

## Branch
`SAF-041/shell-utility-commands`

## User Story
US-036 — Expand the Allowed Terminal Command Set

## Goal
Add `touch`, `chmod` (non-Windows), and `ln` to the terminal allowlist in
`security_gate.py` under Category J (Shell Utilities). All three commands use
`path_args_restricted=True` so that every path argument is zone-checked. For
`ln`, both the source and destination path must resolve inside the project folder.

---

## Implementation Summary

### Files Changed
- `templates/coding/.github/hooks/scripts/security_gate.py`
  - Added `touch`, `chmod`, `ln` entries to `_COMMAND_ALLOWLIST` under Category J.
  - Added `touch`, `chmod`, `ln` to `_PROJECT_FALLBACK_VERBS` so relative
    path arguments work when CWD is the project folder.
- `templates/coding/.github/hooks/scripts/update_hashes.py` run to re-embed
  SHA256 hashes after the above change.
- `docs/workpackages/workpackages.csv` — status updated to `In Progress` / `Review`.
- `tests/SAF-041/` — new test files (see Tests section).

### Design Decisions
1. **touch** — `path_args_restricted=True`, no denied flags. Allows creating files
   inside the project folder; all path args zone-checked by `_validate_args` step 5.
2. **chmod** — `path_args_restricted=True`, no denied flags. Non-Windows only in
   practice (not installed on Windows); security gate allows it when the targeted
   file is inside the project folder. The gate is platform-agnostic; if `chmod` were
   invoked on Windows it would simply not be found by the shell.
3. **ln** — `path_args_restricted=True`, no denied flags. `ln [options] target
   link_name` — both arguments are file-system paths; the existing `_validate_args`
   step 5 checks EVERY path-like arg in the token list, so both source and
   destination are zone-checked automatically. Cross-zone links (either endpoint
   in `.github/`, `.vscode/`, `NoAgentZone/`, or outside the project) are denied.
4. All three verbs added to `_PROJECT_FALLBACK_VERBS` so that relative paths like
   `src/file.txt` typed from the project CWD resolve correctly.

---

## Tests Written

### `tests/SAF-041/test_saf041_shell_utilities.py`
- `touch` allowed in project, denied outside, denied for `.github/`
- `chmod` allowed in project, denied outside, denied for `.vscode/`
- `ln` both paths in project — allowed
- `ln` source outside project — denied
- `ln` target (link name) in `.github/` — denied (cross-zone bridge attempt)
- `ln` target in `NoAgentZone/` — denied
- `ln -s` (soft link) both in project — allowed

---

## Test Results
- All tests pass (see `docs/test-results/test-results.csv`).

---

## Known Limitations
- `chmod` is a POSIX command and has no effect on Windows. The gate allows it
  for zone-compliance purposes; whether it executes is determined by the OS.
- `ln -sf` (force-recreate soft link) is allowed as long as both paths are in the
  project folder — no special flag denial is added.
