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
│   │   └── maintenance.agent.md      # Project health audit agent
│   └── instructions/
│       └── copilot-instructions.md   # Landing page — auto-loaded for all agents
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
├── WORKPACKAGES.md                   # Legacy — superseded by docs/workpackages/workpackages.csv
└── pyproject.toml                    # Python packaging config (planned)
```

## Task Tracking

All work is tracked in [workpackages/workpackages.csv](workpackages/workpackages.csv) (CSV format — open with a table-view extension in VS Code). Do not track tasks in this file.

Each workpackage in active development gets a dedicated folder under `docs/workpackages/<WP-ID>/` containing the developer's log (`dev-log.md`) and the tester's report (`test-report.md`). See [work-rules/workpackage-rules.md](work-rules/workpackage-rules.md) for details.

`WORKPACKAGES.md` at the root is kept for reference only and is no longer the active source of truth.

Categories: **INS** (Installer) · **SAF** (Safety) · **GUI** (GUI) · **DOC** (Documentation)

All rules and workflows are documented in [work-rules/index.md](work-rules/index.md) — the central hub.

## Development Setup

> Setup instructions will be added once INS-001 (Project Scaffolding) and INS-002 (Python Packaging Config) are complete.

Prerequisites:
- Python 3.10+
- VS Code with GitHub Copilot

## Security Policy

This project enforces a **safety-first** development policy:

- The Python security gate (`security_gate.py`) replaces the previous PowerShell/Bash hook scripts, closing all known bypass vectors identified in the security audit.
- All security-critical code requires both a protection test and a bypass-attempt test.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- See [copilot-instructions.md](../.github/instructions/copilot-instructions.md) for the landing page and [work-rules/index.md](work-rules/index.md) for the complete rule set enforced on all contributors and AI agents.
