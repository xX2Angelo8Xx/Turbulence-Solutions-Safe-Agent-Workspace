# Dev Log — INS-027: Add source-mode detection and git-based update to updater

## Status
Review

## Assigned To
Developer Agent

## Summary
Modify `src/launcher/core/updater.py` and `src/launcher/core/applier.py` to
detect source-mode installs and use `git pull` + `pip install .` instead of
downloading a binary release when running from a clone.

## Implementation Plan
1. Add `is_source_mode() -> bool` to `updater.py` — checks `sys._MEIPASS` absence + `.git` presence.
2. Add `check_for_update_source() -> tuple[bool, str]` to `updater.py` — uses `git describe --tags` vs GitHub API.
3. Modify `check_for_update()` to delegate to source-mode path when appropriate.
4. Add `apply_source_update() -> None` to `applier.py` — runs `git pull --ff-only` + `pip install .`.
5. Modify `apply_update()` in `applier.py` to delegate to source path when `is_source_mode()`.

## Files Changed
- `src/launcher/core/updater.py`
- `src/launcher/core/applier.py`
- `tests/INS-027/test_ins027_source_mode.py`
- `docs/workpackages/workpackages.csv`

## Tests Written
See `tests/INS-027/test_ins027_source_mode.py`

## Decisions
- `is_source_mode()` checks `not getattr(sys, '_MEIPASS', None)` AND `.git` dir present at repo root.
- Repo root is resolved as 3 levels up from `config.py` (consistent with existing config.py pattern).
- `apply_source_update()` receives an explicit `repo_root: Path` and `pip_executable: str` so tests can inject these without touching the filesystem.
- `apply_update()` signature is preserved (accepts `installer_path: Path`) — in source mode `installer_path` is ignored and the git path is taken instead.

## Known Limitations
- Source-mode update check uses `git describe --tags` which requires at least one tag in the repo.
- `pip install .` is run synchronously; long installs will block.
