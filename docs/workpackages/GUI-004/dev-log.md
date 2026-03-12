# Dev Log — GUI-004

**Developer:** Developer Agent
**Date started:** 2026-03-12
**Iteration:** 1

## Objective
Folder browser dialog (native OS dialog) for selecting the destination path. Validate: path exists, path is writable.

## Implementation Summary

Added `validate_destination_path(path)` to `src/launcher/gui/validation.py`:
- Rejects empty / whitespace paths.
- Rejects paths that do not exist on disk.
- Rejects paths that are not directories (i.e., files).
- Rejects paths that are not writable (`os.access` check).

Updated `src/launcher/gui/app.py` to import `validate_destination_path` and add `destination_error_label` (inline red label) below the destination entry.

The native browse dialog (`filedialog.askdirectory`) was already present from GUI-001; this WP adds validation on top.

## Files Changed
- `src/launcher/gui/validation.py` — `validate_destination_path` added
- `src/launcher/gui/app.py` — `destination_error_label` added (merged with GUI-003, GUI-011, GUI-012)

## Tests Written
- `tests/GUI-004/test_gui004_destination_validation.py`
  - Empty / whitespace rejection
  - Non-existent path rejection
  - File-not-directory rejection
  - Valid writable directory acceptance
  - Non-writable directory rejection (monkeypatched `os.access`)
  - App `destination_error_label` attribute and red color
  - Browse dialog populate and cancel behaviour

## Known Limitations
- Write-permission check uses `os.access`; on some network filesystems this may not reflect actual permissions. Out of scope for this WP.
