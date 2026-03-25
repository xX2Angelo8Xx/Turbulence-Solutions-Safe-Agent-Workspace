# Plan: v3.2.1 Agent Feedback Report — User Stories, Workpackages & Bugs

> **Source:** `docs/bugs/User-Bug-Reports/AGENT_FEEDBACK_REPORT_v3.2.1.md`  
> **Date:** 2026-03-25  
> **Status:** Draft — awaiting approval before CSV entries are created

---

## Context

The agent feedback report (TS-SAE v3.2.1, 2026-03-25) documents findings from two test
sessions covering:

- **Security gate discrepancies** (Report Sections 2.1–2.5) — enforcement doesn't match AGENT-RULES.md
- **grep_search information leak** (Report Section 3) — workspace root content accessible via grep but not read_file
- **GUI/Launcher bugs** (Report Section 10.1–10.3) — wrong title, wrong project type, broken reset button
- **Denial counter scoping** (Report Section 10.3 + Section 11) — counter is workspace-wide instead of per-conversation
- **Coordinator agent naming** (Report Section 11.4) — case-sensitive agent names don't match documentation

### ID Allocation

| Entity | Next Available ID |
|--------|------------------|
| User Stories | US-052 |
| SAF workpackages | SAF-046 |
| FIX workpackages | FIX-074 |
| DOC workpackages | DOC-030 |
| Bugs | BUG-111 |

### Decisions

| Decision | Resolution |
|----------|-----------|
| Scope | All issues from the report |
| WP prefixes | SAF- for gate/security, FIX- for GUI bugs, DOC- for documentation |
| Gate vs docs mismatch | **Fix the gate** — AGENT-RULES.md is the source of truth; the security gate must be updated to match it |
| Block counter (BUG-118 + BUG-119) | Two separate bugs — one for session ID fallback logic, one for missing/broken reset button |

---

## 1. User Stories

### US-052 — Security Gate Must Match AGENT-RULES.md Permissions

**As a** security-conscious developer  
**I want** the security gate to enforce exactly the permissions documented in AGENT-RULES.md  
**So that** agents have the workspace root access, terminal access, memory access, and search capabilities the rulebook promises, and the environment supports a full development workflow.

**Acceptance Criteria:**

1. `read_file` and `list_dir` on the workspace root succeed for top-level config files (e.g., `pyproject.toml`, `.venv/`) as AGENT-RULES §1 specifies.
2. `run_in_terminal` is zone-checked (not blanket-denied): commands scoped to the workspace and project folder are allowed per AGENT-RULES §4; destructive and out-of-scope commands are denied per the §4 blocked-commands list.
3. Git operations listed in AGENT-RULES §5 (status, log, diff, add, commit, push, etc.) succeed when run via terminal; blocked git operations (push --force, reset --hard, etc.) are denied.
4. The `memory` tool allows reading `/memories/` and `/memories/session/` and allows writing to `/memories/session/` as AGENT-RULES §3 specifies.
5. AGENT-RULES §3 search tool entries accurately describe the actual behavior — amend the "no zone restriction" label to clarify that pattern-directed searches targeting denied zones (e.g., `includePattern: "NoAgentZone/**"`) and `includeIgnoredFiles: true` are blocked.
6. `grep_search` does not surface content from files that `read_file` denies — workspace root files either become accessible to both tools or excluded from both.
7. All acceptance criteria are validated by automated tests in `tests/SAF-046/` through `tests/SAF-050/`.

**Status:** Open  
**Linked WPs:** SAF-046, SAF-047, SAF-048, SAF-049, SAF-050

---

### US-053 — Fix Launcher GUI Branding and Project Type

**As a** developer  
**I want** the launcher to display the correct application title and project type options  
**So that** the branding is consistent and I'm not offered project types that don't exist.

**Acceptance Criteria:**

1. The application window title reads **"TS - Safe Agent Environment"** (not "Turbulence Solutions Launcher").
2. The "Coding" project type option is removed from the Project Type dropdown.
3. A **"Certification Pipeline — Coming Soon..."** entry appears in the dropdown, styled as disabled/greyed-out and non-selectable.
4. Only "Agent Workbench" is selectable for project creation.
5. Attempting to select the disabled entry does not trigger project creation and does not change the active selection.

**Status:** Open  
**Linked WPs:** FIX-074, FIX-075

---

### US-054 — Reliable Per-Conversation Denial Counter with Reset Fallback

**As a** developer using the Safe Agent Environment  
**I want** the denial counter to reset automatically when I start a new conversation, and have a working manual reset button as a fallback  
**So that** my workspace doesn't become unusable over time due to accumulated blocks from past sessions.

**Acceptance Criteria:**

1. The denial counter reliably identifies distinct conversations and scopes blocks per-conversation (not per-workspace).
2. Starting a new chat resets the counter to zero, as AGENT-RULES §6 documents.
3. The Settings dialog's "Reset Agent Blocks" section has a visible, functional **Reset** button.
4. After clicking "Reset Agent Blocks" with a valid workspace selected, all session counters are cleared and a confirmation message is shown.
5. If the OTel session ID is unavailable and the system falls back to a generated UUID, a new conversation must still produce a new fallback ID (not reuse the persisted one).

**Status:** Open  
**Linked WPs:** SAF-051, FIX-076

---

### US-055 — Fix Coordinator Agent Name Resolution

**As a** developer using the Coordinator agent mode  
**I want** the Coordinator's delegation instructions to use the correct agent names  
**So that** the Coordinator can successfully delegate to all 10 specialist agents without name resolution failures.

**Acceptance Criteria:**

1. All agent name references in `coordinator.agent.md` use PascalCase (`Programmer`, `Tester`, `Writer`, `Brainstormer`, `Researcher`, `Scientist`, `Criticist`, `Planner`, `Fixer`, `Prototyper`) matching actual VS Code agent name resolution.
2. The delegation table and all inline `@`-references use the corrected names.
3. The `agents:` frontmatter list uses PascalCase names.
4. The Coordinator's delegation succeeds for all 10 agents on the first attempt without "agent not found" errors.

**Status:** Open  
**Linked WPs:** DOC-030

---

## 2. Bugs

### BUG-111 — Workspace root access blocked despite AGENT-RULES allowing it

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | Agent (Feedback Report v3.2.1, §2.1) |
| **Description** | AGENT-RULES §1 and §3 state that workspace root reads are allowed for config files. The security gate denies both `read_file` and `list_dir` on the workspace root. |
| **Steps to Reproduce** | 1. Start a conversation in an Agent Workbench workspace. 2. Use `read_file` on the workspace root `README.md`. 3. Use `list_dir` on the workspace root. 4. Both are denied. |
| **Expected** | `read_file` succeeds for workspace root config files; `list_dir` succeeds for workspace root. |
| **Actual** | Both operations are denied by the security gate. |
| **Fixed In WP** | SAF-046 |

### BUG-112 — Terminal access completely blocked despite AGENT-RULES allowing scoped commands

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | Agent (Feedback Report v3.2.1, §2.2) |
| **Description** | AGENT-RULES §4 and §5 detail permitted and blocked terminal commands, implying scoped terminal access. The security gate blanket-denies ALL `run_in_terminal` calls, including harmless read-only commands like `Get-Location`. |
| **Steps to Reproduce** | 1. Start a conversation. 2. Run `run_in_terminal` with command `Get-Location`. 3. Denied. 4. Try `git status` — also denied. 5. Try `.venv\Scripts\python -c "print('hello')"` — also denied. |
| **Expected** | Read-only and scoped terminal commands per §4 are allowed; destructive commands per §4 blocked list are denied. |
| **Actual** | Every terminal command is denied regardless of content. |
| **Fixed In WP** | SAF-047 |

### BUG-113 — Memory tool blanket-blocked despite AGENT-RULES allowing session memory

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | Agent (Feedback Report v3.2.1, §2.3) |
| **Description** | AGENT-RULES §3 says `/memories/` and `/memories/session/` are always readable, and session memory writes are allowed. The security gate denies all `memory` tool operations including view. |
| **Steps to Reproduce** | 1. Start a conversation. 2. Use `memory` tool with `view` command on `/memories/`. 3. Denied. 4. Try `/memories/session/`. 5. Also denied. |
| **Expected** | Memory read operations succeed for `/memories/` and `/memories/session/`; session writes succeed. |
| **Actual** | All memory operations denied. |
| **Fixed In WP** | SAF-048 |

### BUG-114 — Search tool docs say "no zone restriction" but denied-zone targeting is blocked

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Reported By** | Agent (Feedback Report v3.2.1, §2.4) |
| **Description** | AGENT-RULES §3 labels `grep_search` and `file_search` as "no zone restriction." In practice, searches with `includePattern` targeting denied zones (e.g., `NoAgentZone/**`) and `includeIgnoredFiles: true` are blocked. The intent is correct but the documentation is misleading. |
| **Steps to Reproduce** | 1. Run `grep_search` with `includePattern: "NoAgentZone/**"`. 2. Denied. 3. Run `file_search` with query `NoAgentZone/**`. 4. Denied. 5. Run `grep_search` with `includeIgnoredFiles: true`. 6. Denied. |
| **Expected** | Documentation accurately describes actual behavior. |
| **Actual** | "No zone restriction" label contradicts enforcement. |
| **Fixed In WP** | SAF-049 |

### BUG-115 — grep_search surfaces workspace root content that read_file denies

| Field | Value |
|-------|-------|
| **Severity** | Low-Medium |
| **Reported By** | Agent (Feedback Report v3.2.1, §3) |
| **Description** | An unfiltered `grep_search` returns matches from workspace root files (e.g., `README.md`) that `read_file` blocks. An agent could reconstruct file contents via many targeted grep queries. The `.github/`, `.vscode/`, and `NoAgentZone/` paths are correctly excluded via `search.exclude`. |
| **Steps to Reproduce** | 1. Confirm `read_file` on workspace root `README.md` is denied. 2. Run `grep_search` for a term known to be in `README.md` (e.g., "NoAgentZone"). 3. Grep returns matching lines from the denied file. |
| **Expected** | Files inaccessible via `read_file` are also excluded from `grep_search` results. |
| **Actual** | Content from workspace root `README.md` is returned by grep despite read_file denial. |
| **Fixed In WP** | SAF-050 |

### BUG-116 — "Coding" project type should be replaced by disabled "Certification Pipeline"

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | User (Feedback Report v3.2.1, §10.1) |
| **Description** | The Project Type dropdown shows "Coding" as a fully selectable option. This project type should not exist. It should be replaced by "Certification Pipeline — Coming Soon..." which is greyed out and non-selectable. |
| **Steps to Reproduce** | 1. Open the launcher. 2. Click the Project Type dropdown. 3. "Coding" appears and is selectable. |
| **Expected** | "Coding" does not appear. "Certification Pipeline — Coming Soon..." appears as a disabled entry. Only "Agent Workbench" is selectable. |
| **Actual** | "Coding" option is present and selectable. |
| **Fixed In WP** | FIX-074 |

### BUG-117 — Launcher window title incorrect

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Reported By** | User (Feedback Report v3.2.1, §10.2) |
| **Description** | The application window title shows "Turbulence Solutions Launcher" instead of "TS - Safe Agent Environment". |
| **Steps to Reproduce** | 1. Open the launcher. 2. Observe the window title bar. |
| **Expected** | Title reads "TS - Safe Agent Environment". |
| **Actual** | Title reads "Turbulence Solutions Launcher". |
| **Fixed In WP** | FIX-075 |

### BUG-118 — Denial counter falls back to workspace-wide UUID instead of per-conversation

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | Agent (Feedback Report v3.2.1, §10.3 + §11.1) |
| **Description** | `_get_session_id()` in `security_gate.py` attempts to read the OTel `session.id` from `copilot-otel.jsonl`. When that fails, it falls back to a UUID4 persisted in `.hook_state.json` under `_fallback_session_id`. This UUID never changes between conversations, so the deny counter becomes workspace-wide rather than per-conversation. The report confirms blocks were not reset between Session 1 and Session 2 (counter started at 13/20). |
| **Steps to Reproduce** | 1. Start conversation A. Trigger 5 denials. Counter shows 5/20. 2. Close the conversation. 3. Start conversation B. Counter shows 5/20 (not reset to 0). |
| **Expected** | Counter resets to 0 when a new conversation starts (per AGENT-RULES §6). |
| **Actual** | Counter persists across conversations due to reused fallback UUID. |
| **Fixed In WP** | SAF-051 |

### BUG-119 — Reset Agent Blocks button missing or non-functional in deployed v3.2.1

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | User (Feedback Report v3.2.1, §10.3) |
| **Description** | User reports the Reset Agent Blocks UI has a workspace selector but no "accept" or "execute" button to perform the reset. Code at HEAD (GUI-021) shows the button exists at `app.py` line ~682–693. This may be a deployment/packaging issue where a stale build was shipped. |
| **Steps to Reproduce** | 1. Open the launcher (v3.2.1 deployed build). 2. Open Settings. 3. Navigate to Reset Agent Blocks section. 4. Select a workspace. 5. No execute/reset button is visible. |
| **Expected** | A "Reset Agent Blocks" button is visible and functional below the workspace selector. |
| **Actual** | No execute button present. Workspace can be selected but no action can be triggered. |
| **Fixed In WP** | FIX-076 |

### BUG-120 — Coordinator agent names use wrong casing (lowercase vs required PascalCase)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Reported By** | Agent (Feedback Report v3.2.1, §11.4) |
| **Description** | `coordinator.agent.md` references all 10 specialist agents in lowercase (`@programmer`, `@tester`, etc.) and lists them in lowercase in the `agents:` frontmatter. VS Code agent name resolution is case-sensitive and requires PascalCase (`Programmer`, `Tester`, etc.). All 10 lowercase invocations fail with "agent not found", while all 10 PascalCase invocations succeed. |
| **Steps to Reproduce** | 1. Activate Coordinator mode. 2. Ask it to delegate a coding task. 3. Coordinator calls `runSubagent` with `agentName: "programmer"`. 4. Fails: "Requested agent 'programmer' not found." 5. Manual test with `agentName: "Programmer"` succeeds. |
| **Expected** | Coordinator uses correct names and all delegations succeed. |
| **Actual** | All 10 delegations fail on first attempt due to lowercase names. |
| **Fixed In WP** | DOC-030 |

---

## 3. Workpackages

### SAF-046 — Enable workspace root read access in security gate

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-052 |
| **Depends On** | — |
| **Description** | Update `security_gate.py` to allow `read_file` and `list_dir` on the workspace root for top-level config files (e.g., `pyproject.toml`, `.venv/`), as documented in AGENT-RULES §1. The current gate logic incorrectly treats the workspace root as a denied zone. Implement scoped access — only allow reading of files directly in the workspace root, not recursion into denied subdirectories. |
| **Goal** | `read_file` and `list_dir` on the workspace root succeed for config files; denied subdirectories (`.github/`, `.vscode/`, `NoAgentZone/`) remain blocked. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py`, `templates/agent-workbench/Project/AGENT-RULES.md` |
| **Bug Reference** | BUG-111 |

### SAF-047 — Implement scoped terminal access in security gate

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-052 |
| **Depends On** | — |
| **Description** | Update `security_gate.py` to zone-check `run_in_terminal` calls instead of blanket-denying them. Implement the permission model from AGENT-RULES §4: allow commands scoped to the workspace/project folder (Python via `.venv`, git standard operations, file inspection, directory creation); deny commands targeting paths outside the workspace, global pip installs, destructive git operations (§5 blocked list), interactive prompts, and writes outside the allowed zone. Reuse existing terminal analysis stages (SAF-004 design: tokenization, command classification, zone check). |
| **Goal** | Scoped terminal commands per AGENT-RULES §4 are allowed; blocked commands per §4 and §5 are denied; agents can run Python, execute tests, and use git. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-112 |

### SAF-048 — Enable memory tool access in security gate

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-052 |
| **Depends On** | — |
| **Description** | Update `security_gate.py` to allow `memory` tool operations as documented in AGENT-RULES §3: allow reading `/memories/` and `/memories/session/`, allow writing to `/memories/session/`. The current gate logic blanket-denies all memory operations. Memory paths are virtual (not filesystem paths in the workspace) and pose no security risk to denied zones. |
| **Goal** | `memory` view/read operations succeed for `/memories/` and `/memories/session/`; session memory writes succeed; user memory writes follow agent-workflow rules. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-113 |

### SAF-049 — Update AGENT-RULES search tool documentation to match actual behavior

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-052 |
| **Depends On** | — |
| **Description** | Update the Tool Permission Matrix in AGENT-RULES §3 to accurately describe search tool behavior. Replace the "no zone restriction" labels for `grep_search` and `file_search` with a more precise description: "Allowed for general workspace queries; searches with `includePattern` targeting denied zones or `includeIgnoredFiles: true` are blocked." Also note that deferred tool preloading (§2.5 in the report) is not enforced by VS Code — tools execute regardless of whether `tool_search_tool_regex` was called first. |
| **Goal** | AGENT-RULES §3 search tool entries accurately document the actual enforcement; no misleading "no zone restriction" label. |
| **Key Files** | `templates/agent-workbench/Project/AGENT-RULES.md` |
| **Bug Reference** | BUG-114 |

### SAF-050 — Prevent grep_search information leak on workspace root files

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-052 |
| **Depends On** | SAF-046 |
| **Description** | After SAF-046 enables workspace root read access, verify whether the grep_search leak is still relevant. If workspace root reads are now allowed via `read_file`, the grep results are no longer a "leak" (both tools have consistent access). If any workspace root files remain read-blocked after SAF-046, add those paths to `search.exclude` in `.vscode/settings.json` to ensure consistent policy across tools. The principle: no file should be accessible via one tool but denied via another. |
| **Goal** | Consistent access policy — every file is either accessible via both `read_file` and `grep_search`, or excluded from both. |
| **Key Files** | `templates/agent-workbench/.vscode/settings.json` (search.exclude), `templates/agent-workbench/.github/hooks/scripts/security_gate.py` |
| **Bug Reference** | BUG-115 |

### SAF-051 — Fix denial counter session ID resolution for per-conversation scoping

| Field | Value |
|-------|-------|
| **Category** | Safety |
| **User Story** | US-054 |
| **Depends On** | — |
| **Description** | `_get_session_id()` in `security_gate.py` falls back to a persisted UUID4 when the OTel `session.id` is unavailable. This fallback UUID persists across conversations, making the counter workspace-wide. Fix the fallback logic so new conversations produce new session IDs. Approaches to investigate (see also `docs/plans/vscode-session-id-methoden.md`): (a) detect OTel file timestamp changes or new entries as a conversation change signal; (b) use `gen_ai.conversation.id` from the JSONL spans; (c) expire the fallback UUID after an inactivity gap (e.g., 5 minutes). Ensure the fix works even when OTel export is disabled (worst case: fallback must still detect conversation boundaries). |
| **Goal** | Denial counter reliably resets when a new conversation starts; blocks from session 1 do not carry into session 2; AGENT-RULES §6 guarantee is met. |
| **Key Files** | `templates/agent-workbench/.github/hooks/scripts/security_gate.py` (`_get_session_id`, `_read_otel_session_id`, `_increment_deny_counter`) |
| **Bug Reference** | BUG-118 |
| **Related Docs** | `docs/plans/vscode-session-id-methoden.md` |

### FIX-074 — Replace "Coding" project type with disabled "Certification Pipeline — Coming Soon..."

| Field | Value |
|-------|-------|
| **Category** | Fix |
| **User Story** | US-053 |
| **Depends On** | — |
| **Description** | Remove the "Coding" template option from the Project Type dropdown. Add "Certification Pipeline — Coming Soon..." as a visible but disabled/greyed-out entry that cannot be selected for project creation. The `templates/certification-pipeline/` directory already exists with only `README.md`. `is_template_ready()` already returns `False` for such templates — use this to drive the disabled state in the dropdown. Only "Agent Workbench" should remain selectable. Since `CTkOptionMenu` doesn't natively support disabled items, consider switching to a `CTkComboBox` with validation, or implementing a custom dropdown with disabled-item rendering. |
| **Goal** | Dropdown shows "Agent Workbench" (selectable) and "Certification Pipeline — Coming Soon..." (disabled/greyed). No "Coding" option exists. Selecting the disabled entry has no effect. |
| **Key Files** | `src/launcher/gui/app.py` (`_build_ui`, `project_type_dropdown`), `src/launcher/core/project_creator.py` (`list_templates`, `is_template_ready`) |
| **Bug Reference** | BUG-116 |

### FIX-075 — Fix launcher window title to "TS - Safe Agent Environment"

| Field | Value |
|-------|-------|
| **Category** | Fix |
| **User Story** | US-053 |
| **Depends On** | — |
| **Description** | Change `APP_NAME` in `config.py` from `"Turbulence Solutions Launcher"` to `"TS - Safe Agent Environment"`. Verify the title propagates correctly to the window title bar and any other UI locations referencing `APP_NAME`. |
| **Goal** | Application window title reads "TS - Safe Agent Environment". |
| **Key Files** | `src/launcher/config.py` (`APP_NAME`), `src/launcher/gui/app.py` |
| **Bug Reference** | BUG-117 |

### FIX-076 — Fix Reset Agent Blocks button visibility and functionality

| Field | Value |
|-------|-------|
| **Category** | Fix |
| **User Story** | US-054 |
| **Depends On** | — |
| **Description** | User reports the v3.2.1 deployed build has no execute button in the Reset Agent Blocks section. Code at HEAD (GUI-021) shows the button exists at `app.py` lines 682–693 with a `_on_reset_agent_blocks` handler. Possible causes: (a) the deployed build is from a commit before GUI-021 landed; (b) a packaging/build issue excluded the updated `app.py`. Verify the button is in the deployed artifact. If missing, rebuild and redeploy. Regardless, add an end-to-end test: browse workspace → click Reset → counters clear → confirmation dialog shown. |
| **Goal** | "Reset Agent Blocks" button is visible, functional, and provides clear feedback in both the development and deployed builds. |
| **Key Files** | `src/launcher/gui/app.py` (`_on_reset_agent_blocks`, `reset_agent_blocks_button`) |
| **Bug Reference** | BUG-119 |

### DOC-030 — Fix Coordinator agent name casing in instructions

| Field | Value |
|-------|-------|
| **Category** | Documentation |
| **User Story** | US-055 |
| **Depends On** | — |
| **Description** | Update `coordinator.agent.md` to use PascalCase agent names matching VS Code's case-sensitive resolution. Changes required: (1) `agents:` frontmatter list: `[programmer, tester, ...]` → `[Programmer, Tester, Writer, Brainstormer, Researcher, Scientist, Criticist, Planner, Fixer, Prototyper]`; (2) Delegation table: `` `@programmer` `` → `` `@Programmer` `` (all 10 rows); (3) Inline references in persona and "How You Work" sections: `@planner`, `@tester`, `@criticist` → `@Planner`, `@Tester`, `@Criticist`. |
| **Goal** | All agent name references in Coordinator instructions use PascalCase; all 10 delegations succeed on the first attempt. |
| **Key Files** | `templates/agent-workbench/.github/agents/coordinator.agent.md` |
| **Bug Reference** | BUG-120 |

---

## 4. Summary Matrix

### User Stories → Workpackages

| User Story | Title | Linked WPs |
|------------|-------|------------|
| US-052 | Security Gate Must Match AGENT-RULES.md | SAF-046, SAF-047, SAF-048, SAF-049, SAF-050 |
| US-053 | Fix Launcher GUI Branding and Project Type | FIX-074, FIX-075 |
| US-054 | Reliable Per-Conversation Denial Counter with Reset | SAF-051, FIX-076 |
| US-055 | Fix Coordinator Agent Name Resolution | DOC-030 |

### Bugs → Workpackages

| Bug | Title | Severity | WP |
|-----|-------|----------|----|
| BUG-111 | Workspace root access blocked | Medium | SAF-046 |
| BUG-112 | Terminal blanket-denied | High | SAF-047 |
| BUG-113 | Memory tool blanket-denied | Medium | SAF-048 |
| BUG-114 | Search "no zone restriction" label misleading | Low | SAF-049 |
| BUG-115 | grep_search leaks workspace root content | Low-Medium | SAF-050 |
| BUG-116 | "Coding" project type should not exist | High | FIX-074 |
| BUG-117 | Window title incorrect | Medium | FIX-075 |
| BUG-118 | Denial counter workspace-wide instead of per-conversation | High | SAF-051 |
| BUG-119 | Reset Agent Blocks button missing in deployed build | High | FIX-076 |
| BUG-120 | Coordinator agent names wrong casing | High | DOC-030 |

### Dependency Graph

```
SAF-046 ← SAF-050 (grep leak depends on root access policy decision)
All other WPs are independent and can be worked in parallel.
```

---

## 5. Execution Notes

- **SAF-047 is the highest-impact item** — without terminal access, agents cannot run code, execute tests, install packages, or use git. This single fix unlocks the full development workflow.
- **SAF-050 depends on SAF-046** — the grep leak resolution depends on what workspace root access policy SAF-046 implements. If root reads are enabled, the "leak" resolves itself.
- **FIX-076 may be a deployment-only issue** — the code at HEAD already has the button. Verify the deployed build first before writing new code.
- **DOC-030 is the lowest-effort fix** — pure text changes in one markdown file.
- **SAF-051 has prior research** — `docs/plans/vscode-session-id-methoden.md` documents four methods for obtaining VS Code session IDs. The OTel method is already partially implemented.
