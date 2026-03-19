# FIX-013 Dev Log — Fix PyInstaller Template Path Resolution

## WP Info
- **ID:** FIX-013
- **Branch:** fix-013-pyinstaller-template-path
- **Status:** In Progress → Review
- **Assigned To:** Developer Agent
- **Date:** 2026-03-14

## Problem
`TEMPLATES_DIR` in `src/launcher/config.py` used:
```python
TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"
```
When running inside a PyInstaller bundle:
- `config.py` lives at `_MEIPASS/launcher/config.py`
- `.parent.parent.parent` walks up to the OS temp directory (above `_MEIPASS`)
- The bundled `templates/` is at `_MEIPASS/templates/`
- `list_templates(TEMPLATES_DIR)` returns `[]`
- `CTkOptionMenu(values=[])` displays its class name as default text

## Fix Applied
`src/launcher/config.py` — replaced the single-line `TEMPLATES_DIR` assignment with a conditional:

```python
import sys

# PyInstaller bundles templates/ at _MEIPASS/templates/.
# In development, templates/ is at repo_root/templates/ (3 levels up from config.py).
if getattr(sys, '_MEIPASS', None):
    TEMPLATES_DIR: Path = Path(sys._MEIPASS) / "templates"
else:
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"
```

## Files Changed
- `src/launcher/config.py` — conditional `TEMPLATES_DIR` using `sys._MEIPASS`

## Tests Written
File: `tests/FIX-013/test_fix013_template_path.py`

| Test | Category | Description |
|------|----------|-------------|
| `test_templates_dir_uses_meipass_when_set` | Regression | When `sys._MEIPASS` is set, `TEMPLATES_DIR` resolves to `Path(_MEIPASS) / "templates"` |
| `test_templates_dir_uses_file_path_when_no_meipass` | Unit | When `sys._MEIPASS` is not set, `TEMPLATES_DIR` is 3 parents up from `config.py` |
| `test_list_templates_returns_non_empty_for_real_templates_dir` | Integration | `list_templates()` returns non-empty list for the real dev templates directory |
| `test_ctk_option_menu_values_non_empty` | Unit | `CTkOptionMenu` gets a non-empty values list when `list_templates()` finds templates |

## Test Results
All 4 FIX-013 tests pass. Full regression suite also passes (see test-results.csv).

## Implementation Notes
- No changes outside `config.py` — minimal, focused fix.
- `import sys` was added at the top of `config.py`.
- The fix is backward-compatible: dev mode is unchanged.
- `getattr(sys, '_MEIPASS', None)` is used to avoid `AttributeError` on non-PyInstaller Python.
