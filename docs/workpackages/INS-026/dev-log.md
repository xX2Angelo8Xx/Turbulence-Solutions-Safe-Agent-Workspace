# Dev Log — INS-026: Create macOS source install script and documentation

**Status:** Review  
**Assigned To:** Developer Agent  
**Branch:** INS-026/macos-source-install  
**User Story:** US-065  
**Bug References:** BUG-147, BUG-148, BUG-149  

---

## Objective

Create `scripts/install-macos.sh` and a `Makefile` that automate macOS source
installation. Update `docs/macos-installation-guide.md` to make source install
the primary method, with DMG as an alternative (pending code signing).

---

## Implementation Summary

### Files Created

| File | Purpose |
|------|---------|
| `scripts/install-macos.sh` | Bash install script (check Python, create venv, pip install, deploy shims, PATH setup) |
| `Makefile` | Targets: `install-macos`, `update-macos`, `uninstall-macos` |

### Files Modified

| File | Change |
|------|--------|
| `docs/macos-installation-guide.md` | Source install promoted to primary method; DMG moved to alternative |

### Design Decisions

1. **Idempotent script** — re-running install-macos.sh is safe; existing venv is reused.
2. **Shell profile detection** — script detects `~/.zshrc` (default on macOS 10.15+)
   and falls back to `~/.bashrc`. PATH addition is guarded to avoid duplicates.
3. **Apple Silicon + Intel** — no arch-specific logic needed; Python venvs are
   native to whichever arch the Python binary is.
4. **ts-python shim** — a wrapper shell script that delegates to the venv Python,
   so the shim itself has no arch dependency.
5. **agent-launcher symlink** — symlink to the venv's `bin/agent-launcher` entry
   point installed by pip.
6. **No dangerous operations** — script never uses `rm -rf` on arbitrary paths;
   `uninstall-macos` Makefile target only removes
   `~/.local/share/TurbulenceSolutions/` after explicit user confirmation prompt
   (not used in automated context — documented as interactive-only).

---

## Tests Written

See `tests/INS-026/test_ins026_install_script.py`

| Test | Category |
|------|---------|
| test_install_script_exists | Unit |
| test_install_script_has_shebang | Unit |
| test_install_script_is_executable_flag | Unit |
| test_python_version_check_present | Unit |
| test_git_check_present | Unit |
| test_venv_path_in_script | Unit |
| test_pip_install_present | Unit |
| test_ts_python_shim_deployment | Unit |
| test_agent_launcher_setup_present | Unit |
| test_path_setup_present | Unit |
| test_no_dangerous_rm_rf | Unit |
| test_no_sudo_required | Unit |
| test_makefile_exists | Unit |
| test_makefile_has_install_target | Unit |
| test_makefile_has_update_target | Unit |
| test_makefile_has_uninstall_target | Unit |
| test_guide_source_install_is_primary | Unit |
| test_guide_has_prerequisites_section | Unit |
| test_guide_has_troubleshooting_section | Unit |
| test_guide_dmg_documented_as_alternative | Unit |

---

## Known Limitations

- The install script cannot be executed on this Windows dev machine; CI on macOS
  is handled by INS-028.
- `uninstall-macos` in Makefile prints a manual instruction to avoid accidental
  automated destructive operations.
- BUG-147, BUG-148, BUG-149 are all addressed by moving to source install
  (no PyInstaller bundle = no SIGKILL, no signature corruption, no Gatekeeper block).
