# Turbulence Solutions — Agent Environment Launcher

## Safety-First Mandate

This project has the highest security classification. Every decision — code, config, architecture — must prioritize safety over convenience. When in doubt, choose the more restrictive option.

## File Conventions

- `README.md` (root): Project overview, architecture summary, dev setup. Do NOT put task tracking here.
- `WORKPACKAGES.md` (root): Single source of truth for all tasks. Every code change MUST reference a workpackage ID.
- `Default-Project/`: Template shipped to end users. NEVER modify it for testing or experimentation — copy it first.

## Workpackage Discipline

- IDs use category prefixes: `INS-xxx` (Installer), `SAF-xxx` (Safety), `GUI-xxx` (GUI).
- Statuses: `Open` → `In Progress` → `Review` → `Done`. No skipping states.
- Before starting work: set the workpackage to `In Progress` and assign yourself.
- After finishing: set to `Review`. Only a reviewer may set `Done`.
- Do NOT create, rename, or re-scope workpackages without approval. Propose changes in Comments.

## Commit & Branch Rules

- Branch naming: `<WP-ID>/<short-description>` (e.g., `SAF-003/fix-grep-bypass`).
- Every commit message MUST start with the workpackage ID: `SAF-003: block includeIgnoredFiles parameter`.
- One workpackage per branch. Do not bundle unrelated changes.

## Scope Discipline

- Only implement what the assigned workpackage specifies. No bonus features, no drive-by refactors.
- Do not add comments, docstrings, or type annotations to code you did not change.
- Do not refactor or "improve" adjacent code unless it is broken and blocking your workpackage.

## Security Rules

- No secrets, credentials, or API keys in source code — ever.
- Validate all external inputs at system boundaries (user input, file paths, JSON from VS Code hooks).
- Never disable, bypass, or weaken safety controls, even temporarily.
- Never use absolute paths in code or documentation. Use relative paths only.
- Never reference documents outside this repository that may be altered independently.

## Code Standards

- All security-critical code requires a test that validates the protection and a test that attempts the bypass.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- Prefer failing closed (deny) over failing open (allow) in all security decisions.

## For AI Agents

- Read `WORKPACKAGES.md` at the start of every session to understand current project state.
- Do not explore, read, or modify files in `.github/`, `.vscode/`, or `NoAgentZone/` within `Default-Project/` unless explicitly required by your assigned workpackage.
- When uncertain about scope, stop and ask — do not guess.
