# Plan: v3.2.4 Update — Bugs, Workpackages & User Stories

> **Source:** `docs/bugs/User-Bug-Reports/AGENT_FEEDBACK_REPORT_v3.2.3.md`  
> **Date:** 2026-03-30  
> **Status:** Draft — awaiting approval before CSV entries are created

---

## Context

The v3.2.3 agent feedback report surfaces 2 CRITICAL security bugs (`.git` breaks zone
classification, `get_changed_files` bypasses all zones), 1 HIGH persistent issue (memory
still blocked despite SAF-048 "Done"), 4 terminal filtering inconsistencies, and structural
issues (copilot-instructions/skills in denied zone, NoAgentZone hidden from explorer).

Additionally, a macOS error report (`SAE_macOS_Error_Report_v323.md`) documents a
CRITICAL launch failure on Apple Silicon — the app crashes with SIGKILL before any GUI
appears. Investigation shows the crash is NOT purely a code signing issue (it occurs even
from the mounted DMG). The root cause is likely a PyInstaller bundling/dylib problem.
Since the launcher already has full fallback logic for non-bundled mode (`config.py`
checks `sys._MEIPASS`), macOS users can build from source, bypassing PyInstaller,
Gatekeeper, and code signing entirely. This also opens the door for git-based auto-updates.

This plan creates 15 bugs, 6 user stories, and 13 workpackages to address everything
systematically for the v3.2.4 release.

### ID Allocation

| Entity | Next Available ID |
|--------|-------------------|
| User Stories | US-060 |
| SAF workpackages | SAF-055 |
| FIX workpackages | FIX-079 |
| Bugs | BUG-135 |

### Decisions

| Decision | Resolution |
|----------|-----------|
| Memory (SAF-048 "Done" but broken) | Investigate — likely deployment or hash mismatch issue |
| Copilot instructions in `.github/` | Keep auto-loaded file minimal; AGENT-RULES.md is the comprehensive reference already accessible in the project folder. Consider further merging later |
| `.github/` agent resource access | **Whitelist** `.github/agents/`, `.github/skills/`, `.github/prompts/`, `.github/instructions/` for **read-only** access. Keep `.github/hooks/` (security gate code) fully denied. `.github/` remains hidden in `files.exclude` |
| `get_changed_files` bypass | Conditional allow — only when `.git/` is inside the project folder; deny if at workspace root |
| Terminal filtering bugs | Fix all 4 (Remove-Item, dir -Name, parenthesized subexpressions, Test-Path) |
| Parallel denial batching | Fix in this release |
| NoAgentZone visibility | Remove from `files.exclude` (visible in explorer); keep in `search.exclude` (hidden from agent search) |
| `.github` visibility | Keep hidden in `files.exclude` — agents should not see it |
| macOS distribution | Accept DMG/code signing as a limitation for now; provide **source distribution** as primary macOS path — users clone repo, `pip install`, run directly. Enables git-based updates. |

---

## 1. User Stories

### US-060 — Whitelist Agent-Facing `.github/` Subdirectories Read-Only  

**As a** developer using an AI agent in the Safe Agent Environment  
**I want** the agent to access its own configuration files (agents, skills, prompts, instructions) without wasting denial blocks  
**So that** agent capabilities work as designed and no blocks are consumed on system-directed reads.

**Acceptance Criteria:**

1. `read_file` on `.github/agents/`, `.github/skills/`, `.github/prompts/`, `.github/instructions/` succeeds (read-only).
2. `list_dir` on those directories succeeds.
3. `create_file` / `edit_file` / `replace_string_in_file` targeting any `.github/` path is still denied.
4. `.github/hooks/` (security gate code) remains fully denied for read and write.
5. `.github/` remains hidden in `files.exclude` — agents discover these paths only via system prompts, not via browsing.
6. Block 1 is no longer consumed reading `copilot-instructions.md`.

**Status:** Open  
**Linked WPs:** SAF-055, SAF-056

---

### US-061 — Close Zone Classification Bypass via `.git` Directory

**As a** security-conscious developer  
**I want** `.git` directories to never be selected as the project folder  
**So that** `git init` at the workspace root cannot break zone classification and lock the agent out of the real project folder.

**Acceptance Criteria:**

1. `.git` is in `_DENY_DIRS` in `zone_classifier.py`.
2. Other common VCS dirs (`.hg`, `.svn`) are also excluded defensively.
3. `detect_project_folder()` skips all dot-prefixed directories.
4. After `git init` at workspace root, the actual project folder remains accessible.
5. Paths inside `.git/` are classified as "deny".

**Status:** Open  
**Linked WPs:** SAF-057

---

### US-062 — Close `get_changed_files` Zone Enforcement Bypass

**As a** security-conscious developer  
**I want** `get_changed_files` to not expose files from denied zones  
**So that** zone enforcement cannot be bypassed by a single tool call when a git repo exists.

**Acceptance Criteria:**

1. `get_changed_files` is moved from `_ALWAYS_ALLOW_TOOLS` to a conditional check.
2. When `.git/` is at workspace root (outside project folder), the tool is denied.
3. When `.git/` is inside the project folder, the tool is allowed.
4. No file paths or contents from denied zones are exposed via the tool output.

**Status:** Open  
**Linked WPs:** SAF-058

---

### US-063 — Fix Terminal Command Filtering Inconsistencies

**As a** developer using terminal commands in the Safe Agent Environment  
**I want** the terminal filter to correctly handle PowerShell cmdlets, parameters, and property-access patterns  
**So that** standard PowerShell workflows don't waste denial blocks on false positives.

**Acceptance Criteria:**

1. `Remove-Item <project-path>` is allowed (same as `del`).
2. `dir -Name` is allowed (valid PS parameter, not a security risk).
3. `(Get-Content file).Count` and similar property-access patterns are allowed.
4. `Test-Path` is added to the command allowlist (read-only diagnostic).
5. `cmd /c` remains blocked (legitimate security concern).
6. Existing tests for all terminal categories still pass.

**Status:** Open  
**Linked WPs:** SAF-059, SAF-061

---

### US-064 — Make NoAgentZone Visible in VS Code Explorer

**As a** developer  
**I want** to see the NoAgentZone folder in the VS Code file explorer  
**So that** I can easily manage its contents without needing the terminal.

**Acceptance Criteria:**

1. `NoAgentZone` is removed from `files.exclude` in `.vscode/settings.json`.
2. `NoAgentZone` remains in `search.exclude` (agent searches don't index it).
3. Security gate zone enforcement still denies all agent access to NoAgentZone.

**Status:** Open  
**Linked WPs:** FIX-079

---

### US-065 — macOS Source Distribution with Git-Based Updates

**As a** macOS user  
**I want** to install the launcher from source via `pip install` and receive updates via git  
**So that** I can use the launcher on macOS without PyInstaller bundling, code signing, or Gatekeeper issues.

**Acceptance Criteria:**

1. A documented `make install-macos` (or equivalent shell script) installs the launcher from the cloned repo into a virtualenv.
2. Running `agent-launcher` from the virtualenv launches the GUI without PyInstaller.
3. The `ts-python` shim is deployed correctly for source-mode installs (points to the virtualenv Python, not a bundled Python.framework).
4. An `update` command or script (`make update-macos` or `agent-launcher --update`) pulls latest changes via git and re-installs.
5. The updater in `core/updater.py` detects source-mode and offers git-based updates instead of downloading DMG assets.
6. The macOS installation guide is updated with the source installation as the **primary** method, with DMG as an alternative for when code signing is resolved.
7. Works on both Apple Silicon (arm64) and Intel (x86_64) Macs with Python 3.11+.

**Status:** Open  
**Linked WPs:** INS-020, INS-021, INS-022

---

## 2. Bugs

### BUG-135 — `.git` directory selected as project folder by zone classifier (CRITICAL)

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.9) |
| **Description** | `detect_project_folder()` in `zone_classifier.py` sorts subdirectories alphabetically and picks the first not in `_DENY_DIRS`. `.git` is absent from `_DENY_DIRS`, sorts before `.github`, and gets selected — making the real project folder inaccessible. |
| **Steps to Reproduce** | 1. `git init` at workspace root. 2. Any `read_file`/`edit_file` on project folder files is denied. |
| **Expected** | `.git` is skipped; real project folder is selected. |
| **Actual** | `.git` selected as project folder; all project files denied. |
| **Fixed In WP** | SAF-057 |

### BUG-136 — `get_changed_files` bypasses all zone enforcement (CRITICAL)

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.10) |
| **Description** | `get_changed_files` is in `_ALWAYS_ALLOW_TOOLS`, bypassing all zone checks. When a git repo exists, it returns full diff content of all untracked files including `.github/hooks/scripts/security_gate.py`, `zone_classifier.py`, and other denied-zone files. |
| **Steps to Reproduce** | 1. `git init` at workspace root. 2. `git add .` 3. Call `get_changed_files`. 4. Full content of all files (including denied zones) returned. |
| **Expected** | Denied-zone files excluded from output. |
| **Actual** | Complete zone enforcement bypass. |
| **Fixed In WP** | SAF-058 |

### BUG-137 — Memory tool still blocked despite SAF-048 marked Done (HIGH)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.1) |
| **Description** | SAF-048 added `validate_memory()` to `security_gate.py` with correct logic for `/memories/` paths. v3.2.3 testing shows all memory operations still denied (Blocks 10-12). Possible causes: (a) test workspace deployed with pre-SAF-048 code, (b) integrity hash mismatch after code update, (c) `validate_memory()` not reached in `decide()` flow. |
| **Steps to Reproduce** | 1. `memory view /memories/`. 2. Denied. 3. `memory view /memories/session/`. 4. Denied. 5. `memory create /memories/session/test.md`. 6. Denied. |
| **Expected** | All three operations succeed per SAF-048. |
| **Actual** | All three denied. |
| **Fixed In WP** | SAF-060 |

### BUG-138 — Copilot instructions in `.github/` wastes Block 1 every conversation

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.2) |
| **Description** | System `prompt:customizationsIndex` directs agent to read `.github/instructions/copilot-instructions.md`. This is in a permanently denied zone. Block 1 is consumed automatically every conversation. |
| **Steps to Reproduce** | 1. Start a new conversation. 2. Agent attempts to read `.github/instructions/copilot-instructions.md` per system prompt. 3. Denied — Block 1 consumed. |
| **Expected** | Agent can read its own configuration without penalty. |
| **Actual** | Block 1 wasted every conversation. |
| **Fixed In WP** | SAF-055 |

### BUG-139 — Skill files in `.github/skills/` inaccessible to agents

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.3) |
| **Description** | Skills index directs agent to read `.github/skills/*/SKILL.md`. File is in denied zone. Any skill-matching request wastes a block. |
| **Steps to Reproduce** | 1. User request matches a skill. 2. Agent attempts to read SKILL.md. 3. Denied. |
| **Expected** | Agent can load skill files. |
| **Actual** | Skill files inaccessible. |
| **Fixed In WP** | SAF-055 |

### BUG-140 — `Remove-Item` blocked but `del` alias allowed (terminal inconsistency)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.4) |
| **Description** | Both `Remove-Item` and `del` are in `_COMMAND_ALLOWLIST` with identical `CommandRule`. Yet `Remove-Item` is blocked while `del` works. Root cause needs investigation — possibly a Stage 3 obfuscation pattern false positive on the cmdlet name. |
| **Steps to Reproduce** | 1. `del Test-v3.2.3/debug-probe.txt` — allowed. 2. `Remove-Item Test-v3.2.3/debug-probe.txt` — denied. |
| **Expected** | Both succeed (identical rules). |
| **Actual** | `Remove-Item` denied, `del` allowed. |
| **Fixed In WP** | SAF-059 |

### BUG-141 — `dir -Name` blocked (terminal false positive)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.4) |
| **Description** | `dir` with no flags works but `dir -Name` is denied. `-Name` is a valid PowerShell parameter for controlling output format, not a security risk. Likely triggers Stage 5 argument validation treating `-Name` as a path-like token. |
| **Steps to Reproduce** | 1. `dir Test-v3.2.3/` — allowed. 2. `dir -Name` — denied. |
| **Expected** | `dir -Name` allowed. |
| **Actual** | Denied. |
| **Fixed In WP** | SAF-059 |

### BUG-142 — Parenthesized subexpressions blocked in terminal

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.4) |
| **Description** | `(Get-Content file).Count` and `(echo "hello").Length` are denied. Stage 3 pattern P-19 `\$\(` targets `$(...)` subshells but may also match, or a different pattern catches `(...)`. Blocks all PowerShell property-access patterns. |
| **Steps to Reproduce** | 1. `(Get-Content Test-v3.2.3/file.txt).Count` — denied. 2. `(echo "hello").Length` — denied. |
| **Expected** | Property-access on grouped commands is allowed. |
| **Actual** | Denied. |
| **Fixed In WP** | SAF-059 |

### BUG-143 — `Test-Path` not in terminal command allowlist

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | Agent (Feedback Report v3.2.3, §3.6.3) |
| **Description** | `Test-Path` is a read-only PowerShell diagnostic cmdlet (checks if path exists). Not in `_COMMAND_ALLOWLIST`. Should be added to Category G (read-only inspection) with `path_args_restricted=True`. |
| **Steps to Reproduce** | 1. `Test-Path .git` — denied. |
| **Expected** | Allowed (read-only diagnostic). |
| **Actual** | Denied — not in allowlist. |
| **Fixed In WP** | SAF-059 |

### BUG-144 — Parallel denial batching non-deterministic

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.5) |
| **Description** | In v3.2.2, parallel denied operations consistently shared block numbers. In v3.2.3, behavior is inconsistent — some parallel batches share blocks, others don't. Two `memory` calls in the same batch got separate blocks (10+11) while two `list_dir` calls shared one block. |
| **Steps to Reproduce** | 1. Issue two parallel tool calls that both target denied zones. 2. Observe block counter — sometimes +1, sometimes +2. |
| **Expected** | Consistent behavior — parallel batch shares one block. |
| **Actual** | Non-deterministic. |
| **Fixed In WP** | SAF-061 |

### BUG-145 — No `.venv` Python environment despite AGENT-RULES reference

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | Agent (Feedback Report v3.2.3, §8.7) |
| **Description** | AGENT-RULES §4 prescribes `.venv\Scripts\python` but no `.venv` exists in the workspace. Agents following rules faithfully will attempt `.venv` first, fail, then fall back to system Python. |
| **Steps to Reproduce** | 1. Read AGENT-RULES §4. 2. Attempt `.venv\Scripts\python --version`. 3. Fails — no `.venv`. |
| **Expected** | Rules match reality. |
| **Actual** | Rules reference non-existent `.venv`. |
| **Fixed In WP** | SAF-056 |

### BUG-146 — NoAgentZone hidden from VS Code file explorer

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | User (v3.2.3 feedback session) |
| **Description** | `**/NoAgentZone` is in `files.exclude`, making the folder invisible in the VS Code explorer. Users cannot manage its contents without the terminal. Should be visible (security gate handles access control). |
| **Steps to Reproduce** | 1. Open workspace in VS Code. 2. NoAgentZone not visible in explorer. |
| **Expected** | Folder visible. |
| **Actual** | Hidden by `files.exclude`. |
| **Fixed In WP** | FIX-079 |

### BUG-147 — macOS launcher crashes immediately with SIGKILL (CRITICAL)

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **Reported By** | User (SAE_macOS_Error_Report_v323.md) |
| **Description** | The v3.2.3 arm64 DMG launcher crashes immediately upon execution with signal 143 (SIGKILL). Memory usage is 48 bytes — the process is killed before any code runs. This happens even when launched directly from the mounted DMG, ruling out signature corruption from copying. No stdout/stderr output is captured. Root cause is likely PyInstaller's embedded Python.framework or dylib loading failure on the target macOS version. |
| **Steps to Reproduce** | 1. Download `AgentEnvironmentLauncher-3.2.3-arm64.dmg`. 2. Mount DMG. 3. Run `./launcher` from terminal or double-click .app. 4. Process exits immediately with SIGKILL. |
| **Expected** | Launcher GUI appears. |
| **Actual** | Immediate crash, no output, 48 bytes memory. |
| **Fixed In WP** | INS-020 (workaround via source install) |

### BUG-148 — macOS code signature corrupted when copying .app from DMG

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | User (SAE_macOS_Error_Report_v323.md) |
| **Description** | Copying the .app bundle from the DMG to ~/Applications/ breaks the code signature. `spctl -a -v` reports "a sealed resource is missing or invalid". PyInstaller bundles have complex nested signatures (dylibs, frameworks, executables) that are damaged by standard Finder copy operations. |
| **Steps to Reproduce** | 1. Mount DMG. 2. Drag .app to Applications. 3. `spctl -a -v ~/Applications/AgentEnvironmentLauncher.app` → signature invalid. |
| **Expected** | Signature intact after copy. |
| **Actual** | Signature broken. |
| **Fixed In WP** | INS-020 (workaround via source install) |

### BUG-149 — macOS Gatekeeper blocks unsigned/unnotarized app

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | User (SAE_macOS_Error_Report_v323.md) |
| **Description** | The launcher uses ad-hoc code signing (`codesign_identity='-'` in `launcher.spec`). macOS Gatekeeper blocks execution with "Apple cannot check it for malicious software". Proper fix requires Apple Developer Certificate ($99/year) + notarization. Accepted as a known limitation — source distribution bypasses this entirely. |
| **Steps to Reproduce** | 1. Download DMG from GitHub Releases. 2. Copy to Applications. 3. Double-click → Gatekeeper warning. |
| **Expected** | App launches normally. |
| **Actual** | Gatekeeper blocks execution. |
| **Fixed In WP** | INS-020 (workaround via source install) |

---

## 3. Workpackages

### Phase A — Critical Security (must be first)

#### SAF-055 — Whitelist `.github/` agent-facing subdirectories read-only

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-060 |
| **Depends On** | — |
| **Description** | Update `security_gate.py` to allow **read-only** access to `.github/agents/`, `.github/skills/`, `.github/prompts/`, and `.github/instructions/`. Write operations to any `.github/` path remain denied. `.github/hooks/` (security gate scripts) remains fully denied for both read and write. Implementation: add a `_GITHUB_READ_ALLOWED` set of subdirectory prefixes. In the exempt-tool path, if a read operation targets one of these prefixes, return "allow". All other `.github/` access remains "deny". |
| **Goal** | Agents can read their own config files; security gate code remains protected; Block 1 is no longer wasted. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py`, `templates/agent-workbench/.github/hooks/scripts/zone_classifier.py` |
| **Bug References** | BUG-138, BUG-139 |

#### SAF-056 — Update AGENT-RULES for `.venv` and copilot-instructions reality

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-060 |
| **Depends On** | SAF-055 |
| **Description** | Update AGENT-RULES.md §4 to note that system Python is acceptable when no `.venv` exists. Verify auto-loaded `copilot-instructions.md` is minimal (just a pointer to AGENT-RULES.md which is the comprehensive reference already in the project folder). No file moves needed since SAF-055 whitelists the instructions path. |
| **Goal** | AGENT-RULES accurately reflects reality for Python and instructions access. |
| **Key Files** | `templates/agent-workbench/Project/AGENT-RULES.md`, `templates/agent-workbench/.github/instructions/copilot-instructions.md` |
| **Bug Reference** | BUG-145 |

#### SAF-057 — Add `.git` and VCS directories to zone classifier deny set

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-061 |
| **Depends On** | — |
| **Description** | Add `.git`, `.hg`, `.svn` to `_DENY_DIRS` in `zone_classifier.py`. Additionally, make `detect_project_folder()` skip **all dot-prefixed directories** as a defensive measure — no hidden directory should ever be the project folder. Update the regex deny pattern to include `.git`. Run `update_hashes.py` after changes. |
| **Goal** | `git init` at workspace root no longer breaks zone classification. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/zone_classifier.py` |
| **Bug Reference** | BUG-135 |

#### SAF-058 — Move `get_changed_files` from always-allow to conditional check

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-062 |
| **Depends On** | SAF-057 |
| **Description** | Remove `get_changed_files` from `_ALWAYS_ALLOW_TOOLS`. Add a dedicated `validate_get_changed_files()` function in `security_gate.py`. Logic: locate `.git/` — if it's at workspace root (outside project folder), deny. If `.git/` is inside the project folder, allow. If no `.git/` exists, allow (tool returns harmless "no repo" message). This prevents zone bypass while preserving git diff functionality for project-scoped repos. |
| **Goal** | `get_changed_files` cannot expose denied-zone files. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-136 |

### Phase B — Functional Fixes (parallel with each other, after Phase A)

#### SAF-059 — Fix 4 terminal command filtering inconsistencies

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-063 |
| **Depends On** | — |
| **Description** | Fix four terminal bugs in `security_gate.py`: **(1)** Investigate why `Remove-Item` is blocked — check if a Stage 3 pattern false-positives on it; if so, adjust pattern OR ensure verb extraction happens before obfuscation scan for allowlisted verbs. **(2)** Fix `dir -Name` — ensure `-Name` is not treated as a path argument in Stage 5 `_validate_args()`. **(3)** Fix parenthesized subexpressions — identify which pattern blocks `(cmd).Property` and add an exclusion for non-`$()` parentheses OR pre-extract the inner command verb. **(4)** Add `Test-Path` to `_COMMAND_ALLOWLIST` Category G with `path_args_restricted=True` and `allow_arbitrary_paths=False`. |
| **Goal** | All four commands work correctly inside the project folder; existing test suite still passes. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug References** | BUG-140, BUG-141, BUG-142, BUG-143 |

#### SAF-060 — Investigate and fix memory tool still blocked

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-060 |
| **Depends On** | — |
| **Description** | SAF-048 is "Done" and `validate_memory()` exists with correct logic. Memory is still denied in v3.2.3 testing. Investigate: **(a)** Was the test workspace built from a commit that includes SAF-048? Check deployed `security_gate.py` hash vs template hash. **(b)** Is `validate_memory()` actually reached in `decide()`? Add debug logging. **(c)** Does the `memory` tool's input schema match what `validate_memory()` expects (check `"path"` vs `"filePath"` key extraction)? **(d)** Is the integrity hash stale (BUG-128), causing the gate to reject all calls? Fix whatever the root cause is. |
| **Goal** | `memory view /memories/` and `memory create /memories/session/` work in deployed workspace. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-137 |

#### SAF-061 — Make parallel denial batching deterministic

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-063 |
| **Depends On** | — |
| **Description** | Investigate why parallel tool calls sometimes share a single block and sometimes get separate blocks. The deny counter logic in `_increment_deny_counter()` likely has a race condition — two parallel calls may read the same counter value, both increment, and write back with different results. Fix: ensure atomic read-increment-write (file lock or atomic compare-and-swap pattern). All tool calls in the same parallel batch should ideally share one block increment, or at minimum, the behavior should be deterministic. |
| **Goal** | Parallel denied operations consistently share a single block. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-144 |

### Phase C — UX Improvements (parallel, independent)

#### FIX-079 — Show NoAgentZone in VS Code file explorer  

| Field | Value |
|-------|-------|
| **Category** | Fix |
| **User Story** | US-064 |
| **Depends On** | — |
| **Description** | Remove `"**/NoAgentZone": true` from `files.exclude` in `.vscode/settings.json`. Keep it in `search.exclude`. Security gate zone enforcement remains the access control — explorer visibility doesn't grant agent access. |
| **Goal** | Users see NoAgentZone in explorer for easy management; agent search doesn't index it. |
| **Key Files** | `templates/agent-workbench/.vscode/settings.json` |
| **Bug Reference** | BUG-146 |

### Phase D — macOS Source Distribution

#### INS-020 — Create macOS source install script and documentation

| Field | Value |
|-------|-------|
| **Category** | Installer |
| **User Story** | US-065 |
| **Depends On** | — |
| **Description** | Create a `Makefile` (or `scripts/install-macos.sh`) that automates the macOS source installation: (1) check Python 3.11+ is available, (2) create a virtualenv in `~/.local/share/TurbulenceSolutions/venv/`, (3) `pip install .` from the repo, (4) deploy the `ts-python` shim pointing to the virtualenv Python (not a bundled Python.framework), (5) add `agent-launcher` to PATH via shell profile or symlink. Update `docs/macos-installation-guide.md` to make source install the **primary** macOS method. Include: prerequisites (Python 3.11+, git, Xcode Command Line Tools), step-by-step instructions, and troubleshooting. DMG remains documented as an alternative pending code signing resolution. |
| **Goal** | macOS users can install and run the launcher from source in under 5 minutes. |
| **Key Files** | `Makefile` or `scripts/install-macos.sh` (new), `docs/macos-installation-guide.md`, `src/launcher/core/shim_config.py` (ensure source-mode shim deployment works) |
| **Bug References** | BUG-147, BUG-148, BUG-149 |

#### INS-021 — Add source-mode detection and git-based update to updater

| Field | Value |
|-------|-------|
| **Category** | Installer |
| **User Story** | US-065 |
| **Depends On** | INS-020 |
| **Description** | Modify `src/launcher/core/updater.py` to detect source-mode installs (absence of `sys._MEIPASS` + presence of `.git/` in the repo root). When in source mode: (1) check for updates by comparing local `git describe --tags` against GitHub Releases API `tag_name`, (2) if update available, show a notification in the GUI with an "Update" button, (3) on click, execute `git pull && pip install .` in the background, (4) prompt restart. Modify `core/applier.py` to handle the source-mode update path (no DMG mounting). The existing DMG/exe/AppImage update path remains for bundled installs. |
| **Goal** | Source-mode macOS users get one-click updates from the launcher GUI. |
| **Key Files** | `src/launcher/core/updater.py`, `src/launcher/core/applier.py`, `src/launcher/core/downloader.py` (skip download in source mode) |
| **Bug Reference** | — |

#### INS-022 — Add macOS source install to CI test matrix

| Field | Value |
|-------|-------|
| **Category** | Installer |
| **User Story** | US-065 |
| **Depends On** | INS-020 |
| **Description** | Add a `macos-source-install` job to `.github/workflows/release.yml` (or a new CI workflow). Steps: (1) checkout repo on `macos-14` runner, (2) run the install script, (3) verify `agent-launcher --version` succeeds, (4) verify `ts-python --version` succeeds, (5) run `python -m pytest tests/` to confirm the test suite passes on macOS. This ensures the source install path doesn't regress. |
| **Goal** | CI validates macOS source install on every release. |
| **Key Files** | `.github/workflows/release.yml` (or new workflow file) |
| **Bug Reference** | — |

---

## 4. Summary Matrices

### User Stories → Workpackages

| User Story | Title | Linked WPs |
|------------|-------|------------|
| US-060 | Whitelist agent-facing `.github/` subdirs read-only | SAF-055, SAF-056, SAF-060 |
| US-061 | Close zone classification bypass via `.git` | SAF-057 |
| US-062 | Close `get_changed_files` zone bypass | SAF-058 |
| US-063 | Fix terminal command filtering inconsistencies | SAF-059, SAF-061 |
| US-064 | Make NoAgentZone visible in explorer | FIX-079 |
| US-065 | macOS source distribution with git-based updates | INS-020, INS-021, INS-022 |

### Bugs → Workpackages

| Bug | Title | Severity | WP |
|-----|-------|----------|----|
| BUG-135 | `.git` selected as project folder | Critical | SAF-057 |
| BUG-136 | `get_changed_files` zone bypass | Critical | SAF-058 |
| BUG-137 | Memory still blocked (SAF-048 regression) | High | SAF-060 |
| BUG-138 | copilot-instructions wastes Block 1 | High | SAF-055 |
| BUG-139 | Skill files inaccessible | Medium | SAF-055 |
| BUG-140 | `Remove-Item` blocked, `del` allowed | Medium | SAF-059 |
| BUG-141 | `dir -Name` blocked | Low | SAF-059 |
| BUG-142 | Parenthesized subexpressions blocked | Medium | SAF-059 |
| BUG-143 | `Test-Path` missing from allowlist | Low | SAF-059 |
| BUG-144 | Parallel denial batching non-deterministic | Low | SAF-061 |
| BUG-145 | No `.venv` despite AGENT-RULES reference | Low | SAF-056 |
| BUG-146 | NoAgentZone hidden from explorer | Low | FIX-079 |
| BUG-147 | macOS launcher SIGKILL crash | Critical | INS-020 |
| BUG-148 | macOS code signature corruption on copy | High | INS-020 |
| BUG-149 | macOS Gatekeeper blocks unnotarized app | Medium | INS-020 |

### Dependency Graph

```
Phase A (Critical Security — sequential):
  SAF-055 ← SAF-056 (AGENT-RULES update depends on whitelist being in place)
  SAF-057 ← SAF-058 (get_changed_files check depends on .git deny fix)

Phase B (Functional — parallel, after Phase A):
  SAF-059 (terminal fixes — independent)
  SAF-060 (memory investigation — independent)
  SAF-061 (denial batching — independent)

Phase C (UX — parallel, independent):
  FIX-079 (NoAgentZone visibility — independent)

Phase D (macOS — parallel with B and C):
  INS-020 ← INS-021 (updater depends on install script)
  INS-020 ← INS-022 (CI depends on install script)
```

### Verification

1. Deploy updated `security_gate.py` and `zone_classifier.py` to a test workspace.
2. Run `update_hashes.py` to regenerate integrity hashes.
3. Run existing test suites: `pytest tests/SAF-*/` — all must pass.
4. Write new tests for each SAF WP in `tests/SAF-055/` through `tests/SAF-061/`.
5. Manual agent test: start conversation, verify Block 1 not consumed on instructions read.
6. Manual agent test: `git init` at workspace root, verify project folder still accessible.
7. Manual agent test: `get_changed_files` with workspace-root `.git/` returns deny.
8. Manual agent test: `memory view /memories/` succeeds.
9. Manual agent test: `Remove-Item`, `dir -Name`, `(Get-Content f).Count`, `Test-Path` all succeed in project folder.
10. Manual agent test: verify NoAgentZone visible in explorer but agent access still denied.
11. macOS test: clone repo on Apple Silicon Mac, run install script, verify `agent-launcher` launches GUI.
12. macOS test: verify `ts-python` shim points to virtualenv Python (not bundled framework).
13. macOS test: verify git-based update detection and execution from launcher GUI.
