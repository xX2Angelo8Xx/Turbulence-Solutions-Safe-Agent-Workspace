# Turbulence Solutions — Agent Environment Launcher

Cross-platform installer and launcher that creates pre-configured, safety-hardened VS Code workspaces for AI-assisted development. Each generated project includes a Python-based security gate that enforces tool access controls, zone-based file protection, and terminal command sanitization — ensuring AI agents operate within defined boundaries.

## Architecture

```
Installer (.exe / .dmg / .AppImage)
  └── Launcher GUI (customtkinter)
        ├── User selects: project name, type, destination
        ├── Copies template to destination folder
        └── Optionally opens VS Code with the new workspace

Templates (bundled inside Launcher)
  └── coding/          ← Default-Project template
  └── creative/        ← Future: marketing/creative template
```

## Repository Structure

```
├── .github/
│   └── instructions/
│       └── copilot-instructions.md   # Hard rules for all agents
├── Default-Project/                  # "Coding" template (shipped to users)
│   ├── .github/                      # Hook scripts, Copilot config
│   ├── .vscode/                      # VS Code security settings
│   ├── NoAgentZone/                  # Blocked from all AI access
│   └── Project/                      # Agent working directory
├── src/                              # Launcher source (planned)
│   ├── launcher/
│   │   ├── main.py                   # Entry point
│   │   ├── gui/                      # UI components
│   │   ├── core/                     # Business logic
│   │   └── config.py                 # Constants
│   └── installer/                    # Per-platform installer scripts
├── templates/                        # Bundled project templates (planned)
├── README.md                         # This file — project overview
├── WORKPACKAGES.md                   # Task tracking (single source of truth)
└── pyproject.toml                    # Python packaging config (planned)
```

## Task Tracking

All work is tracked in [WORKPACKAGES.md](WORKPACKAGES.md). Do not track tasks in this file.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI)

## Development Setup

> Setup instructions will be added once INS-001 (Project Scaffolding) and INS-002 (Python Packaging Config) are complete.

Prerequisites:
- Python 3.10+
- VS Code with GitHub Copilot

## Recommended VS Code Extensions

| Extension | ID | Purpose |
| --------- | -- | ------- |
| Markdown Table Prettifier | `darkriszty.markdown-table-prettify` | Auto-aligns MD table columns on save/format for readable workpackage tables |

## Security Policy

This project enforces a **safety-first** development policy:

- The Python security gate (`security_gate.py`) replaces the previous PowerShell/Bash hook scripts, closing all known bypass vectors identified in the security audit.
- All security-critical code requires both a protection test and a bypass-attempt test.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- See [copilot-instructions.md](.github/instructions/copilot-instructions.md) for the complete rule set enforced on all contributors and AI agents.
