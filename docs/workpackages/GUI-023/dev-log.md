# GUI-023 Dev Log — Rename template directories and update launcher code

**WP ID:** GUI-023  
**Branch:** GUI-023/template-rename  
**Assigned To:** Developer Agent  
**Date Started:** 2026-03-25  
**User Story:** US-041

---

## Objective

Rename `templates/coding/` to `templates/agent-workbench/` and `templates/creative-marketing/` to `templates/certification-pipeline/`. Update launcher GUI and core code to reflect the new names.

---

## Implementation Summary

### Changes Made

1. **Directory rename (git mv):**
   - `templates/coding/` → `templates/agent-workbench/`
   - `templates/creative-marketing/` → `templates/certification-pipeline/`

2. **`src/launcher/gui/app.py` — `_format_template_name()`:**
   - The existing generic implementation (`raw.replace("-", " ").replace("_", " ").title()`) already produces correct output:
     - `"agent-workbench"` → `"Agent Workbench"`
     - `"certification-pipeline"` → `"Certification Pipeline"`
   - No code change required; the function is generic and template-name–agnostic.

3. **`src/launcher/core/project_creator.py` — `list_templates()` and `is_template_ready()`:**
   - Both functions operate generically on any directory under `TEMPLATES_DIR`. No changes required.

4. **`src/launcher/config.py` — `TEMPLATES_DIR`:**
   - Points to `templates/` directory level; no subdirectory references. No changes required.

5. **`launcher.spec`:**
   - Bundles the entire `templates/` directory as-is: `(os.path.join(SPECPATH, 'templates'), 'templates')`. No changes required.

6. **`src/installer/windows/setup.iss`, `macos/build_dmg.sh`, `linux/build_appimage.sh`:**
   - Grepped for `coding` and `creative-marketing` references — none found. No changes required.

7. **`templates/certification-pipeline/README.md`:**
   - Updated content to reflect new name "Certification Pipeline - Coming Soon".

### Files Changed
- `templates/agent-workbench/` (renamed from `templates/coding/`)
- `templates/certification-pipeline/` (renamed from `templates/creative-marketing/`)
- `templates/certification-pipeline/README.md` — updated content
- `docs/workpackages/workpackages.csv` — status updated to In Progress → Review
- `docs/workpackages/GUI-023/dev-log.md` — this file

---

## Tests Written

- `tests/GUI-023/test_gui023_template_rename.py`
  - Tests that `templates/agent-workbench/` directory exists
  - Tests that `templates/coding/` directory does NOT exist
  - Tests that `templates/certification-pipeline/` directory exists
  - Tests that `templates/creative-marketing/` directory does NOT exist
  - Tests that `_format_template_name("agent-workbench")` returns `"Agent Workbench"`
  - Tests that `_format_template_name("certification-pipeline")` returns `"Certification Pipeline"`
  - Tests that `list_templates()` returns new names
  - Tests that agent-workbench is ready (has files beyond README)
  - Tests that certification-pipeline is NOT ready (only has README)
  - Tests that `TEMPLATES_DIR` resolves to a valid directory

---

## Known Limitations

- FIX-071 must update existing test files that reference the old `templates/coding/` path.
- DOC-017 must update documentation references.

---

## Iteration History

_(No iterations — initial implementation)_
