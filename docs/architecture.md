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
  └── creative-marketing/   ← Marketing/creative template
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
│   ├── instructions/
│   │   └── copilot-instructions.md   # Landing page — auto-loaded for all agents
│   └── workflows/
│       └── release.yml               # CI/CD: build + release on version tag push
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
│   │   │   ├── github_auth.py        # GitHub token provider (env vars / gh CLI)
│   │   │   ├── updater.py            # Version check via GitHub Releases API
│   │   │   └── downloader.py         # Asset download from GitHub Releases
│   │   └── config.py                 # Constants
│   └── installer/                    # Per-platform installer scripts
├── templates/                        # Bundled project templates
├── tests/                            # Permanent test scripts (per workpackage)
│   ├── conftest.py                   # pytest configuration — src/ path setup
│   ├── __init__.py
│   ├── DOC-001/                      # Tests for DOC-001 (Placeholder System)
│   ├── DOC-002/                      # Tests for DOC-002 (README Placeholders)
│   ├── DOC-003/                      # Tests for DOC-003 (copilot-instructions Placeholders)
│   ├── DOC-004/                      # Tests for DOC-004 (Project Folder README Placeholders)
│   ├── FIX-006/                      # Tests for FIX-006 (Test Safety Infrastructure)
│   ├── FIX-007/                      # Tests for FIX-007 (Standardize GUI Test Mock Pattern)
│   ├── FIX-008/                      # Tests for FIX-008 (Conftest Multi-Layer VS Code Guard)
│   ├── FIX-009/                      # Tests for FIX-009 (TST-ID Deduplication)
│   ├── FIX-010/                      # Tests for FIX-010 (Fix CI/CD Release Pipeline)
│   ├── FIX-011/                      # Tests for FIX-011 (Fix CI Spec File and Drop Intel Mac)
│   ├── FIX-012/                      # Tests for FIX-012 (Fix macOS/Windows CI directives)
│   ├── FIX-013/                      # Tests for FIX-013 (Fix PyInstaller Template Path)
│   ├── FIX-014/                      # Tests for FIX-014 (Bump Version to 1.0.1)
│   ├── FIX-015/                      # Tests for FIX-015 (Fix TS Logo Aspect Ratio)
│   ├── FIX-016/                      # Tests for FIX-016 (Fix App Icon for Windows)
│   ├── FIX-017/                      # Tests for FIX-017 (Bump Version to 1.0.2)
│   ├── FIX-018/                      # Tests for FIX-018 (GitHub Auth for Private Repo)
│   ├── FIX-019/                      # Tests for FIX-019 (Bump Version to 1.0.3)
│   ├── FIX-020/                      # Tests for FIX-020 (Bump Version to 2.0.0)
│   ├── FIX-021/                      # Tests for FIX-021 (Search Tools Blocking Fix)
│   ├── FIX-022/                      # Tests for FIX-022 (Python/pip/venv Terminal Fixes)
│   ├── FIX-023/                      # Tests for FIX-023 (.venv Directory in Project Folder)
│   ├── FIX-026/                      # Tests for FIX-026 (get_errors Project Folder Fallback)
│   ├── FIX-028/                      # Tests for FIX-028 (macOS Ad-Hoc Code Signing)
│   ├── FIX-029/                      # Tests for FIX-029 (CI Code Signing Verification)
│   ├── FIX-030/                      # Tests for FIX-030 (Bump Version to 2.0.1)
│   ├── FIX-036/                      # Tests for FIX-036 (Bump Version to 2.1.0)
│   ├── FIX-037/                      # Tests for FIX-037 (Remove .dist-info from macOS bundle)
│   ├── FIX-038/                      # Tests for FIX-038 (Component-level macOS codesign)
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
│   ├── GUI-012/                      # Tests for GUI-012 (UI Spacing and Visual Hierarchy)
│   ├── GUI-013/                      # Tests for GUI-013 (Add TS-Logo to App GUI and Icon)
│   ├── GUI-014/                      # Tests for GUI-014 (Grey Out Unfinished Templates)
│   ├── GUI-015/                      # Tests for GUI-015 (Rename Root Folder to TS-SAE)
│   ├── GUI-016/                      # Tests for GUI-016 (Rename Internal Project Folder)
│   ├── GUI-017/                      # Tests for GUI-017 (UI Labels for New Naming)
│   ├── INS-001/                      # Tests for INS-001 (Project Scaffolding)
│   ├── INS-002/                      # Tests for INS-002 (Python Packaging)
│   ├── INS-003/                      # Tests for INS-003 (PyInstaller Config)
│   ├── INS-004/                      # Tests for INS-004 (Template Bundling)
│   ├── INS-005/                      # Tests for INS-005 (Windows Installer)
│   ├── INS-006/                      # Tests for INS-006 (macOS Installer)
│   ├── INS-007/                      # Tests for INS-007 (Linux Installer)
│   ├── INS-009/                      # Tests for INS-009 (GitHub Releases Version Check)
│   ├── INS-010/                      # Tests for INS-010 (Update Download)
│   ├── INS-011/                      # Tests for INS-011 (Update Apply and Restart)
│   ├── INS-012/                      # Tests for INS-012 (.gitignore Configuration)
│   ├── INS-013/                      # Tests for INS-013 (CI Workflow Skeleton)
│   ├── INS-014/                      # Tests for INS-014 (CI Windows Build Job)
│   ├── INS-015/                      # Tests for INS-015 (CI macOS Build Jobs)
│   ├── INS-016/                      # Tests for INS-016 (CI Linux Build Job)
│   ├── INS-017/                      # Tests for INS-017 (CI Release Upload Job)
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
│   ├── SAF-011/                      # Tests for SAF-011 (Hash Update Script)
│   ├── SAF-012/                      # Tests for SAF-012 (Deny-by-Default Zone Classifier)
│   ├── SAF-013/                      # Tests for SAF-013 (Security Gate 2-Tier Model)
│   ├── SAF-014/                      # Tests for SAF-014 (Terminal Allowlist — Read Commands)
│   ├── SAF-015/                      # Tests for SAF-015 (Terminal Allowlist — Write Commands)
│   ├── SAF-016/                      # Tests for SAF-016 (Terminal Allowlist — Delete Commands)
│   ├── SAF-017/                      # Tests for SAF-017 (Python and pip Commands)
│   ├── SAF-018/                      # Tests for SAF-018 (multi_replace_string_in_file)
│   ├── SAF-019/                      # Tests for SAF-019 (VS Code Auto-Approve Settings)
│   ├── SAF-020/                      # Tests for SAF-020 (Terminal Wildcard Detection)
│   ├── SAF-021/                      # Tests for SAF-021 (Wildcard Bypass Regression Tests)
│   ├── SAF-022/                      # Tests for SAF-022 (NoAgentZone VS Code Exclude)
│   ├── SAF-023/                      # Tests for SAF-023 (get_errors Restricted Zone Block)
│   ├── SAF-024/                      # Tests for SAF-024 (Generic Deny Messages)
│   └── SAF-025/                      # Tests for SAF-025 (Integrity Hashes Update)
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
├── TS-Logo.png                       # Company logo (used in GUI header and non-Windows icon)
├── TS-Logo.ico                       # Company logo in ICO format (Windows app icon)
├── .gitignore                        # Excludes .venv/, __pycache__/, build artifacts, etc.
├── .venv/                            # Workspace-local virtual environment (gitignored)
└── pyproject.toml                    # Python packaging configuration
```

## Task Tracking

All work is tracked in [workpackages/workpackages.csv](workpackages/workpackages.csv) (CSV format — open with a table-view extension in VS Code). Do not track tasks in this file.

Each workpackage in active development gets a dedicated folder under `docs/workpackages/<WP-ID>/` containing the developer's log (`dev-log.md`) and the tester's report (`test-report.md`). See [work-rules/workpackage-rules.md](work-rules/workpackage-rules.md) for details.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI) · **FIX** (Fix / Bug Fix) · **DOC** (Documentation)

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
