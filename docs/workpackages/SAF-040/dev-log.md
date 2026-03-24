# SAF-040 Dev Log — Add read-only commands to terminal allowlist

**Status:** In Progress  
**Branch:** SAF-040/read-only-commands  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-24  

---

## Objective

Add the following read-only commands to the terminal allowlist in
`templates/coding/.github/hooks/scripts/security_gate.py` with
`path_args_restricted=True`: `diff`, `fc`, `comp`, `sort`, `uniq`, `awk`, `sed`.

Note: `more` and `less` were already present in Category G from a prior WP.
This WP adds the remaining 7 commands to complete AC 1 of US-036.

All 9 commands (including the pre-existing `more`/`less`) are zone-checked:
allowed when targeting project folder, denied when targeting outside.

---

## Implementation

### Files Changed

- `templates/coding/.github/hooks/scripts/security_gate.py` — added 7 new
  Category G entries: `diff`, `fc`, `comp`, `sort`, `uniq`, `awk`, `sed`.
  Each uses `path_args_restricted=True` and `allow_arbitrary_paths=False`.
- `templates/coding/.github/hooks/scripts/security_gate.py` — `_KNOWN_GOOD_GATE_HASH`
  updated by `update_hashes.py` after the allowlist change.

### Design Decisions

- All 7 commands are placed in **Category G** (Read-only File Inspection) right
  after the existing `more` entry, consistent with the existing pattern.
- `path_args_restricted=True` ensures all path arguments are zone-checked.
- `fc` and `comp` are Windows-specific diff/compare utilities; included for
  cross-platform completeness (they are no-ops on Unix but safe to list).
- `awk` and `sed` accept file arguments as well as stdin — adding them to the
  allowlist with path restriction covers the file-argument case; stdin-piped
  usage passes through as it has no path args.

---

## Tests Written

- `tests/SAF-040/test_saf040_readonly_commands.py`
  - Each command allowed with project-folder path arg (7 commands × allow)
  - Each command denied with outside-project path arg (7 commands × deny)
  - Pre-existing `more`/`less` continue to be allowed in project (regression)
  - Piped usage (no path args) — allowed since no restricted path args present

---

## Test Results

All tests passed. See `docs/test-results/test-results.csv`.

---

## Known Limitations / Notes

None.
