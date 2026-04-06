# FIX-117 — Dev Log: Allowlist get_changed_files in security hook

**Status:** In Progress  
**Branch:** `FIX-117/allowlist-get-changed-files`  
**Fixes:** BUG-197  
**User Story:** US-081  

---

## Prior Art Check

- Checked `docs/decisions/index.jsonl` — no ADR directly governing `get_changed_files` allowlisting.
- SAF-058 introduced the conditional `validate_get_changed_files()` logic. This WP supersedes that approach by unconditionally allowlisting the tool.
- ADR-011 (settings.json hash removal) is not directly related.

---

## Problem Analysis

`get_changed_files` is a VS Code deferred tool that returns git diff metadata (changed file names, status). It is read-only — it cannot write files, execute code, or read file content.

The SAF-058 implementation handled `get_changed_files` via `validate_get_changed_files()`, which:
1. Denied the tool when `.git/` exists at workspace root.
2. Allowed the tool when `.git/` exists only inside the project folder.

In the Agent Workbench, the workspace IS the git repository root, so `.git/` is always present at workspace root → the tool is always denied. This consumes 2 denial blocks per use (BUG-197).

The tool only returns file-path metadata, equivalent to `git status` which is already allowed via the terminal allowlist. The zone risk is minimal: knowing changed filenames in `.github/` or `.vscode/` does not grant read access to their content.

---

## Implementation

### Changes Made

1. **`templates/agent-workbench/.github/hooks/scripts/security_gate.py`**
   - Added `get_changed_files` to `_ALWAYS_ALLOW_TOOLS`.
   - Removed the SAF-058 comment noting it was removed.
   - Removed the `validate_get_changed_files()` function (dead code).
   - Removed the `if tool_name == "get_changed_files":` dispatch block in `decide()`.

2. **`templates/agent-workbench/Project/AGENT-RULES.md`** — Added `get_changed_files` row to Tool Permission Matrix (Section 3).

3. **`templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md`** — Same update (mirror file).

4. **`templates/agent-workbench/.github/hooks/scripts/security_gate.py`** — Hash re-embedded via `update_hashes.py`.

5. **`MANIFEST.json`** — Regenerated via `scripts/generate_manifest.py`.

---

## Tests Written

- `tests/FIX-117/test_fix117_get_changed_files_allow.py`
  - `test_get_changed_files_is_always_allowed` — verifies `decide()` returns "allow" regardless of `.git/` at workspace root.
  - `test_get_changed_files_no_git_dir_allowed` — verifies allow when no `.git/` exists.
  - `test_get_changed_files_in_always_allow_set` — verifies the tool name is in `_ALWAYS_ALLOW_TOOLS`.
  - `test_validate_get_changed_files_removed` — verifies `validate_get_changed_files` function no longer exists.
  - `test_agent_rules_has_get_changed_files_entry` — verifies AGENT-RULES.md documents the tool.

---

## Regression Baseline

BUG-197 was not present in `tests/regression-baseline.json` — no entry to remove.

---

## Files Changed

| File | Change |
|------|--------|
| `templates/agent-workbench/.github/hooks/scripts/security_gate.py` | Added `get_changed_files` to `_ALWAYS_ALLOW_TOOLS`; removed `validate_get_changed_files()` and its dispatch |
| `templates/agent-workbench/Project/AGENT-RULES.md` | Added `get_changed_files` to Tool Permission Matrix |
| `templates/agent-workbench/Project/AgentDocs/AGENT-RULES.md` | Same update (mirror file) |
| `docs/workpackages/workpackages.jsonl` | Status → In Progress / Review |
| `docs/bugs/bugs.jsonl` | BUG-197 `Fixed In WP` → FIX-117 |
| `docs/workpackages/FIX-117/dev-log.md` | This file |
| `tests/FIX-117/test_fix117_get_changed_files_allow.py` | New test file |
| `MANIFEST.json` | Regenerated |
