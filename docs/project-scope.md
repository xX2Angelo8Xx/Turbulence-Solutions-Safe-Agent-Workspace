# Project Scope — Agent Environment Launcher

## Vision

A cross-platform desktop tool that lets developers spin up a pre-configured, safety-hardened VS Code workspace in seconds — with AI agent guardrails built in from day one.

---

## Target Users

- Developers and teams using GitHub Copilot or similar AI agents in VS Code
- Organizations that need to enforce strict boundaries on what AI agents can read, write, or execute

---

## What It Does

| # | Capability | Description |
|---|-----------|-------------|
| 1 | **Launcher GUI** | Desktop app (customtkinter); user picks project name, type, and destination |
| 2 | **Template Engine** | Copies a pre-built, safety-hardened project template to the destination |
| 3 | **Safety Gate** | Python-based `security_gate.py` enforces zone-based access control on every AI tool call |
| 4 | **Native Installer** | Packages the Launcher for Windows (.exe), macOS (.dmg), and Linux (.AppImage) |
| 5 | **Auto-Update** | Checks for newer versions on launch; downloads and applies updates from within the app |

---

## Components

### Installer (INS)

Packages the Launcher and bundled templates into native OS installers. A GitHub Actions CI/CD pipeline builds and publishes release artifacts automatically on version tags.

Key workpackages: INS-001 through INS-008.

---

### Safety System (SAF)

A Python `security_gate.py` replaces legacy PowerShell/Bash hooks. It parses VS Code `PreToolUse` hook JSON from stdin and returns an allow/deny/ask decision to stdout. Enforces:

| Control | Description |
|---------|-------------|
| Zone classification | **Allow**: `Project/` · **Deny**: `.github/`, `.vscode/`, `NoAgentZone/` · **Ask**: everything else |
| Tool parameter validation | Blocks bypass vectors for `grep_search` and `semantic_search` |
| Terminal sanitization | Allowlist-based command validation; prevents fragmentation and multi-interpreter bypasses |
| Recursive enumeration protection | Blocks `Get-ChildItem -Recurse`, `dir /s`, `tree`, `find`, `ls -R` targeting protected paths |
| Write restriction | Denies all file writes outside `Project/` |
| File integrity | SHA256 hash verification of `security_gate.py` and `settings.json` at startup |

Key workpackages: SAF-001 through SAF-010.

---

### GUI (GUI)

`customtkinter` desktop application providing:

- Project name input with real-time validation
- Project type dropdown dynamically populated from `templates/`
- Native OS folder browser for destination path selection
- "Open in VS Code" checkbox (greyed out if VS Code is not detected)
- Inline error messaging for all invalid states

Key workpackages: GUI-001 through GUI-007.

---

### Auto-Update (UPD)

The launcher checks for newer versions on startup by querying the GitHub Releases API. When an update is available, a non-blocking banner notifies the user. The user can also trigger a manual check. Updates are downloaded and applied from within the app — the launcher downloads the correct platform installer and hands off to it.

Key workpackages: GUI-008, GUI-009, GUI-010, INS-009, INS-010, INS-011.

---

## Templates

| Template | Folder | Description |
|----------|--------|-------------|
| Agent Workbench | `templates/agent-workbench/` | Standard AI-assisted coding workspace with full safety gate |
| Certification Pipeline | `templates/certification-pipeline/` | Planned — future template for certification and pipeline work |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| GUI | Python, `customtkinter` |
| Packaging | PyInstaller, `pyproject.toml` |
| Windows installer | Inno Setup |
| macOS installer | DMG build script |
| Linux installer | AppImage build script |
| CI/CD | GitHub Actions |
| Testing | `pytest` |
| Security hook | Python (cross-platform) |

---

## Out of Scope

- Cloud sync or remote storage
- Multi-user / team collaboration features
- IDE support outside VS Code
- Template marketplace
- AI model selection or configuration
