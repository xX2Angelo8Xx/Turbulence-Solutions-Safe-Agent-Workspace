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
│   ├── agents/                       # Custom agent definitions
│   │   ├── orchestrator.agent.md     # Multi-WP delegation agent
│   │   ├── developer.agent.md        # Single-WP implementation agent
│   │   ├── tester.agent.md           # Review and testing agent
│   │   ├── maintenance.agent.md      # Project health audit agent
│   │   └── story-writer.agent.md     # User story creation agent
│   └── instructions/
│       └── copilot-instructions.md   # Landing page — auto-loaded for all agents
├── Default-Project/                  # "Coding" template (shipped to users)
│   ├── .github/                      # Hook scripts, Copilot config
│   ├── .vscode/                      # VS Code security settings
│   ├── NoAgentZone/                  # Blocked from all AI access
│   └── Project/                      # Agent working directory
├── src/                              # Launcher source
│   ├── launcher/
│   │   ├── main.py                   # Entry point
│   │   ├── gui/                      # UI components
│   │   ├── core/                     # Business logic
│   │   └── config.py                 # Constants
│   └── installer/                    # Per-platform installer scripts
├── templates/                        # Bundled project templates
├── tests/                            # Permanent test scripts (per workpackage)
│   ├── conftest.py                   # pytest configuration — src/ path setup
│   ├── __init__.py
│   ├── INS-001/                      # Tests for INS-001 (Project Scaffolding)
│   ├── INS-002/                      # Tests for INS-002 (Python Packaging)
│   ├── INS-003/                      # Tests for INS-003 (PyInstaller Config)
│   ├── INS-004/                      # Tests for INS-004 (Template Bundling)
│   ├── INS-005/                      # Tests for INS-005 (Windows Installer)
│   ├── INS-006/                      # Tests for INS-006 (macOS Installer)
│   ├── INS-007/                      # Tests for INS-007 (Linux Installer)
│   ├── INS-009/                      # Tests for INS-009 (GitHub Releases Version Check)
│   ├── INS-010/                      # Tests for INS-010 (Update Download)
│   ├── INS-012/                      # Tests for INS-012 (.gitignore Configuration)
│   ├── SAF-001/                      # Tests for SAF-001 (Security Gate Core)
│   ├── SAF-002/                      # Tests for SAF-002 (Zone Enforcement Logic)
│   ├── SAF-003/                      # Tests for SAF-003 (Tool Parameter Validation)
│   ├── SAF-004/                      # Tests for SAF-004 (Terminal Sanitization — Design)
│   ├── SAF-005/                      # Tests for SAF-005 (Terminal Command Sanitization)
│   ├── SAF-006/                      # Tests for SAF-006 (Recursive Enumeration Protection)
│   ├── SAF-007/                      # Tests for SAF-007 (Write Restriction Outside Project)
│   ├── SAF-008/                      # Tests for SAF-008 (Hook File Integrity)
│   ├── SAF-009/                      # Tests for SAF-009 (Cross-Platform Test Suite)
│   ├── SAF-010/                      # Tests for SAF-010 (Hook Integration Config)
│   ├── GUI-001/                      # Tests for GUI-001 (Main Window Layout)
│   ├── GUI-002/                      # Tests for GUI-002 (Project Type Selection)
│   ├── GUI-003/                      # Tests for GUI-003 (Folder Name Input)
│   ├── GUI-004/                      # Tests for GUI-004 (Location Browser)
│   ├── GUI-005/                      # Tests for GUI-005 (Project Creation Logic)
│   ├── GUI-006/                      # Tests for GUI-006 (VS Code Auto-Open)
│   ├── GUI-007/                      # Tests for GUI-007 (Input Validation & Error UX)
│   ├── GUI-008/                      # Tests for GUI-008 (Version Display)
│   ├── GUI-009/                      # Tests for GUI-009 (Update Notification Banner)
│   ├── GUI-010/                      # Tests for GUI-010 (Check for Updates Button)
│   ├── GUI-011/                      # Tests for GUI-011 (Apply Company Color Theme)
│   └── GUI-012/                      # Tests for GUI-012 (UI Spacing and Visual Hierarchy)
├── docs/
│   ├── architecture.md               # Project overview and structure (this file)
│   ├── project-scope.md              # Project scope and vision
│   ├── work-rules/                   # All project rules and workflows
│   │   ├── index.md                  # Central hub — "if you need to…" lookup
│   │   ├── workpackage-rules.md      # WP lifecycle, CSV format, status rules
│   │   ├── user-story-rules.md       # US lifecycle, acceptance criteria
│   │   ├── commit-branch-rules.md    # Branch naming, commit format
│   │   ├── coding-standards.md       # Scope discipline, code quality
│   │   ├── security-rules.md         # Security non-negotiables
│   │   ├── bug-tracking-rules.md     # Bug logging, severity, CSV format
│   │   ├── testing-protocol.md       # Test standards, categories, workflow
│   │   ├── maintenance-protocol.md   # Maintenance checklist, log format
│   │   └── agent-workflow.md         # Agent onboarding, WP execution protocol
│   ├── workpackages/
│   │   ├── workpackages.csv          # Task tracking (single source of truth)
│   │   └── <WP-ID>/                  # Per-WP folders (created during development)
│   │       ├── dev-log.md            #   Developer's implementation log
│   │       └── test-report.md        #   Tester's findings and results
│   ├── user-stories/
│   │   └── user-stories.csv          # User stories (parent of workpackages)
│   ├── bugs/
│   │   └── bugs.csv                  # Bug tracking
│   ├── test-results/
│   │   └── test-results.csv          # Test execution records
│   └── maintenance/                  # Maintenance audit logs (timestamped)
├── .gitignore                        # Excludes .venv/, __pycache__/, build artifacts, etc.
├── .venv/                            # Workspace-local virtual environment (gitignored)
└── pyproject.toml                    # Python packaging configuration
```

## Task Tracking

All work is tracked in [workpackages/workpackages.csv](workpackages/workpackages.csv) (CSV format — open with a table-view extension in VS Code). Do not track tasks in this file.

Each workpackage in active development gets a dedicated folder under `docs/workpackages/<WP-ID>/` containing the developer's log (`dev-log.md`) and the tester's report (`test-report.md`). See [work-rules/workpackage-rules.md](work-rules/workpackage-rules.md) for details.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI) · **DOC** (Documentation)

All rules and workflows are documented in [work-rules/index.md](work-rules/index.md) — the central hub.

## Development Setup

Prerequisites:
- Python 3.11+
- VS Code with GitHub Copilot
- GitHub CLI (`gh`) authenticated as `xX2Angelo8Xx`

### First-time setup

```powershell
# 1. Clone the repository
git clone https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git "Github Repository"
cd "Github Repository"

# 2. Create the workspace virtual environment (never use global pip)
python -m venv .venv

# 3. Install the project in editable mode with all dev dependencies
.venv\Scripts\pip install -e ".[dev]"

# 4. Run the full test suite to verify setup
.venv\Scripts\python -m pytest tests/ -v
```

> All Python commands in this project must use `.venv\Scripts\python` (Windows) or `.venv/bin/python` (macOS/Linux). Never install packages globally.

### Git configuration (one-time per machine)

```powershell
# Authenticate GitHub CLI with the project account
gh auth login --hostname github.com

# Set repository-local git identity
git config user.name "xX2Angelo8Xx"
git config user.email "angelomichaelamon2001@gmail.com"
```

## Security Policy

This project enforces a **safety-first** development policy:

- The Python security gate (`security_gate.py`) replaces the previous PowerShell/Bash hook scripts, closing all known bypass vectors identified in the security audit.
- All security-critical code requires both a protection test and a bypass-attempt test.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- See [copilot-instructions.md](../.github/instructions/copilot-instructions.md) for the landing page and [work-rules/index.md](work-rules/index.md) for the complete rule set enforced on all contributors and AI agents.
