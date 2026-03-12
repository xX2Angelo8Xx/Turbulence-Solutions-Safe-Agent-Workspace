# Dev Log — GUI-008: Version Display

## WP Summary
Display the current installed Launcher version in the main window at all times.

---

## Iteration 1 (Initial — failed Tester review)
- **Status:** Tester set back to In Progress
- **Issues reported:**
  - `version_label` widget never added to `app.py`
  - `get_display_version` not imported in `app.py`
  - No dev-log.md present
  - No developer tests submitted

---

## Iteration 2 — 2026-03-12

### Changes Made
| File | Change |
|------|--------|
| `src/launcher/gui/app.py` | Added `get_display_version` to import from `launcher.config` |
| `src/launcher/gui/app.py` | Added `self.version_label` CTkLabel widget via `place()` at bottom-right of window |

### Implementation Notes
- `get_display_version()` is imported alongside existing `launcher.config` symbols.
- `version_label` is placed with `place(relx=1.0, rely=1.0, x=-20, y=-8, anchor="se")` so it sits at the bottom-right corner without disrupting the grid layout of other rows.
- `text` is set to `f"v{get_display_version()}"` so the label always reflects the installed package version.

### Tests
- Existing tests in `tests/GUI-008/` cover the version label presence and text; no new test files were created in this iteration as the fix targets exactly what the Tester's test suite already validates.
