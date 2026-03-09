# Workpackages

Single source of truth for all project tasks. See `copilot-instructions.md` for rules on how to use this file.

## Legend

**Statuses:** `Open` → `In Progress` → `Review` → `Done`

**Categories:**

| Prefix | Domain                                    |
|--------|-------------------------------------------|
| INS    | Installer — packaging, bundling, CI/CD    |
| SAF    | Safety — Python security gate, hook logic |
| GUI    | GUI — Launcher user interface             |

**Columns:**

| Column      | Description                                                    |
| ----------- | -------------------------------------------------------------- |
| ID          | Unique identifier: `<PREFIX>-<NNN>`                            |
| Name        | Short descriptive title                                        |
| Status      | Current lifecycle state                                        |
| Assigned To | Person or agent responsible (blank = unassigned)               |
| Description | What needs to be done                                          |
| Goal        | Measurable completion criteria                                 |
| Comments    | Notes, blockers, dependencies, review feedback                 |

---

## Installer (INS)

| ID      | Name                   | Status | Assigned To | Description                                                                                                                                    | Goal                                                              | Comments |
| ------- | ---------------------- | ------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------- |
| INS-001 | Project Scaffolding    | Open   |             | Create `src/` directory structure: `launcher/main.py`, `gui/app.py`, `gui/components.py`, `core/project_creator.py`, `core/vscode.py`, `core/os_utils.py`, `config.py`, `installer/` with per-platform subdirectories | Repository matches planned structure; `python src/launcher/main.py` runs without import errors | |
| INS-002 | Python Packaging       | Open   |             | Create `pyproject.toml` with project metadata, dependencies (`customtkinter`), dev dependencies (`pyinstaller`, `pytest`), and entry point     | `pip install -e .` succeeds; all dependencies installable         | |
| INS-003 | PyInstaller Config     | Open   |             | Create PyInstaller spec file; configure `--onedir` bundling; include `templates/` as bundled data                                              | `pyinstaller` produces working bundled output on the current OS   | Depends on INS-001, INS-002 |
| INS-004 | Template Bundling      | Open   |             | Copy `Default-Project/` as the "coding" template under `templates/coding/`; ensure all safety files (hooks, settings, instructions) are included | Templates discoverable and copyable at runtime from bundled app   | Depends on INS-001 |
| INS-005 | Windows Installer      | Open   |             | Create Inno Setup script (`src/installer/windows/setup.iss`) wrapping PyInstaller output                                                       | `.exe` installer installs the Launcher on Windows                 | Depends on INS-003 |
| INS-006 | macOS Installer        | Open   |             | Create DMG build script (`src/installer/macos/build_dmg.sh`) for both Intel and ARM architectures                                              | `.dmg` installer works on macOS Intel and Apple Silicon            | Depends on INS-003 |
| INS-007 | Linux Installer        | Open   |             | Create AppImage build script (`src/installer/linux/build_appimage.sh`)                                                                         | `.AppImage` runs on major Linux distributions                     | Depends on INS-003 |
| INS-008 | CI/CD Pipeline         | Open   |             | Create GitHub Actions workflow: 4 parallel jobs (Windows, macOS Intel, macOS ARM, Linux); build, package, and upload to GitHub Release          | Push to version tag triggers automated builds and release artifacts | Depends on INS-005, INS-006, INS-007 |

---

## Safety (SAF)

| ID      | Name                              | Status | Assigned To | Description                                                                                                                                                                                            | Goal                                                                 | Comments |
| ------- | --------------------------------- | ------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------- |
| SAF-001 | Python Security Gate — Core       | Open   |             | Design and implement `security_gate.py` replacing `.ps1`/`.sh` hooks. Parse VS Code hook JSON input (stdin), determine tool name and target path, return allow/deny/ask JSON to stdout. Cross-platform. | Single Python script handles PreToolUse hook on Windows, macOS, Linux | |
| SAF-002 | Zone Enforcement Logic            | Open   |             | Implement 3-tier zone classification: allow = `Project/`, deny = `.github/`, `.vscode/`, `NoAgentZone/`, ask = everything else. Port and harden logic from current shell hooks.                        | Zone checks match or exceed current shell implementation              | Depends on SAF-001 |
| SAF-003 | Tool Parameter Validation         | Open   |             | Extract and validate `includePattern`, `includeIgnoredFiles` for `grep_search`. Block `semantic_search` when it could expose protected files. Addresses audit findings 2 and 3.                        | `grep_search` and `semantic_search` bypass vectors are closed         | Depends on SAF-001 |
| SAF-004 | Terminal Sanitization — Design    | Open   |             | Write a design document specifying the allowlist approach for terminal commands: define permitted command patterns, document edge cases, specify how string fragmentation / variable concatenation / multi-interpreter bypasses are prevented. | Written design document reviewed and approved before implementation   | Addresses audit finding 1. Must be completed before SAF-005 |
| SAF-005 | Terminal Command Sanitization     | Open   |             | Implement the terminal allowlist defined in SAF-004. Replace string-literal pattern matching with the approved allowlist approach.                                                                      | Terminal string fragmentation attack vector fully eliminated          | **Blocked by SAF-004** |
| SAF-006 | Recursive Enumeration Protection  | Open   |             | Detect and block recursive listing commands (`Get-ChildItem -Recurse`, `dir /s`, `tree`, `find`, `ls -R`) targeting ancestors of protected directories. Addresses audit finding 4.                     | Recursive directory enumeration of protected zones is blocked         | Depends on SAF-001 |
| SAF-007 | Write Restriction Outside Project | Open   |             | Deny all file write operations (`create_file`, `replace_string_in_file`, `multi_replace_string_in_file`) targeting paths outside `Project/`. Addresses audit finding 6.                                 | No file writes possible outside the designated working directory      | Depends on SAF-002 |
| SAF-008 | Hook File Integrity               | Open   |             | On startup, verify SHA256 hashes of `security_gate.py` and `settings.json` against known-good values embedded in the script. Alert or refuse to run if modified. Addresses audit finding 5.             | Tampering with safety-critical files is detectable at hook startup    | Depends on SAF-001 |
| SAF-009 | Cross-Platform Test Suite         | Open   |             | Create automated tests (`pytest`) validating all security zones, all bypass vectors from the audit report, and all tool types. Tests must run on Windows, macOS, and Linux.                             | Every audit finding has a regression test; CI runs tests on all 3 OSes | Depends on SAF-002, SAF-003, SAF-005, SAF-006, SAF-007, SAF-008 |
| SAF-010 | Hook Integration Config           | Open   |             | Create `require-approval.json` pointing to the new Python security gate. Ensure VS Code discovers and invokes it for every PreToolUse event.                                                           | Python hook is activated via standard VS Code hook mechanism          | Depends on SAF-001 |

---

## GUI (GUI)

| ID      | Name                          | Status | Assigned To | Description                                                                                                                                                      | Goal                                                                  | Comments |
| ------- | ----------------------------- | ------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------- |
| GUI-001 | Main Window Layout            | Open   |             | Create the main `customtkinter` window with: project name text input, project type dropdown, destination path field with browse button, "Open in VS Code" checkbox, "Create Project" button | Window renders correctly on Windows, macOS, and Linux                 | Depends on INS-001 |
| GUI-002 | Project Type Selection        | Open   |             | Populate the project type dropdown dynamically by listing subdirectories of `templates/`. Initial types: "Coding" and "Creative / Marketing".                    | Dropdown shows all available template types; adding a template folder automatically adds a new option | Depends on GUI-001, INS-004 |
| GUI-003 | Folder Name Input             | Open   |             | Text field for the user to enter a custom project folder name. Validate: not empty, no special characters that break file systems, no duplicate folder at target path | User can name their project freely; invalid names are rejected with a clear message | Depends on GUI-001 |
| GUI-004 | Location Browser              | Open   |             | Folder browser dialog (native OS dialog) for selecting the destination path. Validate: path exists, path is writable.                                            | User can browse to and select any writable folder on their system      | Depends on GUI-001 |
| GUI-005 | Project Creation Logic        | Open   |             | On "Create Project" click: copy the selected template directory to `<destination>/<folder_name>/`. Show success message or error feedback in the UI.              | Template is copied correctly; user sees confirmation or actionable error | Depends on GUI-002, GUI-003, GUI-004 |
| GUI-006 | VS Code Auto-Open             | Open   |             | Detect VS Code executable (platform-specific paths + PATH lookup). When "Open in VS Code" is checked and project creation succeeds, launch VS Code with the new folder as workspace. Grey out checkbox if VS Code is not detected. | VS Code opens the new workspace automatically; graceful fallback if VS Code not found | Depends on GUI-005 |
| GUI-007 | Input Validation & Error UX   | Open   |             | Validate all user inputs before project creation. Display clear, inline error messages for: empty name, invalid characters, path not found, write permission denied, duplicate folder name. | All invalid states produce user-friendly error messages; no silent failures | Depends on GUI-003, GUI-004, GUI-005 |
