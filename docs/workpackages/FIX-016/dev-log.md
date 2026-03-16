# FIX-016 Dev Log — Fix App Icon for Windows (.ico)

## Status
In Progress → Review

## Date
2026-03-16

## Assigned To
Developer Agent

## WP Summary
Create a `.ico` version of `TS-Logo.png` for use as the Windows executable icon.
Update `launcher.spec` icon parameter to reference `.ico`. Bundle the `.ico` file
in PyInstaller datas. Update the runtime window icon to use `iconbitmap` with the
`.ico` on Windows and fall back to `iconphoto` on non-Windows platforms.

Fixes BUG-044.

---

## Implementation

### Files Changed

| File | Change |
|------|--------|
| `TS-Logo.ico` | New file — multi-size ICO generated from TS-Logo.png via Pillow (16, 32, 48, 64, 128, 256 px) |
| `launcher.spec` | `icon=` parameter updated to `TS-Logo.ico`; `TS-Logo.ico` added to `datas` list |
| `src/launcher/config.py` | Added `LOGO_ICO_PATH` constant (parallel to `LOGO_PATH`) |
| `src/launcher/gui/app.py` | Windows: use `wm_iconbitmap` with `.ico`; non-Windows: fall back to `iconphoto` with `.png` |

### Decisions

1. **Multi-size ICO**: Generated with Pillow using sizes `[16, 32, 48, 64, 128, 256]` to
   ensure Windows renders a sharp icon at all DPI levels and contexts (taskbar, Alt-Tab,
   file explorer etc.).
2. **Runtime split by `sys.platform`**: Used `sys.platform == "win32"` to choose between
   `wm_iconbitmap` (Windows) and `iconphoto` (Linux/macOS). This matches Tkinter's
   documented best practice: `.ico` files work with `iconbitmap` on Windows; `iconphoto`
   works cross-platform with PNG/PhotoImage.
3. **Config constant `LOGO_ICO_PATH`**: Added alongside existing `LOGO_PATH` following
   the same `sys._MEIPASS` / development fallback pattern.
4. **Bundling**: Added `TS-Logo.ico` to the `datas` list in `launcher.spec` so it is
   accessible inside the bundled `.exe` at runtime.

---

## Tests Written

All tests live in `tests/FIX-016/test_fix016_ico_icon.py`.

| Test ID | Description |
|---------|-------------|
| TST-FIX016-001 | `TS-Logo.ico` file exists at repo root |
| TST-FIX016-002 | ICO file is readable as a valid ICO by Pillow |
| TST-FIX016-003 | ICO contains all required sizes (16, 32, 48, 64, 128, 256) |
| TST-FIX016-004 | `config.py` exports `LOGO_ICO_PATH` |
| TST-FIX016-005 | `LOGO_ICO_PATH` points to a `.ico` file |
| TST-FIX016-006 | `LOGO_ICO_PATH` resolves in development (file exists) |
| TST-FIX016-007 | `launcher.spec` icon parameter references `.ico` not `.png` |
| TST-FIX016-008 | `launcher.spec` datas list includes `TS-Logo.ico` entry |
| TST-FIX016-009 | `app.py` imports `LOGO_ICO_PATH` from config |
| TST-FIX016-010 | On Windows, `wm_iconbitmap` is called with the `.ico` path |
| TST-FIX016-011 | On non-Windows, `iconphoto` is called (`.png` path) |
| TST-FIX016-012 | Regression: `iconphoto` path unchanged for non-Windows platforms |

---

## Known Limitations

- `wm_iconbitmap` only affects the window titlebar icon on non-Windows systems running
  Tkinter. The Windows-specific branch is guarded by `sys.platform == "win32"`.
- ICO file is generated from a 232×255 RGBA PNG. Alpha channel is preserved in the
  multi-size ICO.
