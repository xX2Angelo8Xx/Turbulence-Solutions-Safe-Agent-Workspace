# SAE Security Policy — Compact Reference

**April 2026 | Turbulence Solutions**

```
BLOCK = Hard deny. Gate returns non-zero. No agent override.
ASK   = Gate blocks. Agent MUST call vscode_askQuestions, get explicit approval, then retry.
ALLOW = Auto-approved. Gate passes silently.
```

Zone definitions:
- **Inside** = any path under the workspace root not covered by a more specific named zone below
- **CI/CD zone** = `.github/workflows/` and all other unspecified `.github/` sub-paths (e.g. `CODEOWNERS`, root-level `.github/` files)
- **Agents zone** = `.github/agents/`, `.github/skills/`, `.github/prompts/`, `.github/instructions/`
- **Gate zone** = `.github/hooks/` (security gate code — fully protected)
- **Config zone** = `.vscode/`
- **Restricted zone** = `NoAgentZone/`, `.git/`, `.hg/`, `.svn/`
- **Outside** = any path outside the workspace root

**Zone precedence:** When a path matches multiple zones, the most restrictive zone wins. A BLOCK in any matching zone overrides ALLOW in any other.

---

## 1. File System Tool Calls

| Tool                                   | Inside                                                                      | CI/CD zone | Agents zone | Gate zone | Config zone | Restricted zone | Outside workspace |
|----------------------------------------|-----------------------------------------------------------------------------|------------|-------------|-----------|-------------|-----------------|-------------------|
| `read_file` / `Read`                   | ALLOW                                                                       | ALLOW      | ALLOW       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `list_dir`                             | ALLOW                                                                       | ALLOW      | ALLOW       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `create_file` / `write_file` / `Write` | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `edit_file` / `Edit`                   | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `replace_string_in_file`               | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `multi_replace_string_in_file`         | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `insert_edit_into_file`                | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `create_directory`                     | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `view_image`                           | ALLOW                                                                       | ALLOW      | ALLOW       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `edit_notebook_file`                   | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `create_new_jupyter_notebook`          | ALLOW                                                                       | ASK        | BLOCK       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `read_notebook_cell_output`            | ALLOW                                                                       | ALLOW      | ALLOW       | BLOCK     | BLOCK       | BLOCK           | BLOCK             |
| `memory`                               | ALLOW (writes to `/memories/` only — outside workspace, managed separately) | —          | —           | —         | —           | —               | —                 |

> **Note:** No direct `delete_file` tool call exists in this policy. File deletion by agents is handled exclusively via terminal Category M commands (`rm`, `remove-item`, etc.), which are zone-checked.

---

## 2. Search & Read-Only Tool Calls

| Tool                                                | Decision | Constraint                                |
|-----------------------------------------------------|----------|-------------------------------------------|
| `grep_search`                                       | ALLOW    | Path args zone-checked                    |
| `file_search`                                       | ALLOW    | Path args zone-checked                    |
| `semantic_search`                                   | ALLOW    | Content-based; no path enforcement needed |
| `get_errors`                                        | ALLOW    | Path args zone-checked                    |
| `fetch_webpage`                                     | ALLOW    | Public URLs only; no auth bypass          |
| `vscode_listCodeUsages`                             | ALLOW    | Path zone-checked                         |
| `container-tools_get-config`                        | ALLOW    | Read-only                                 |
| `get_changed_files`                                 | ALLOW    | Read-only                                 |
| `get_project_setup_info`                            | ALLOW    | Read-only                                 |
| `resolve_memory_file_uri`                           | ALLOW    | Read-only                                 |
| `mcp_gitkraken_repository_get_file_content`         | ALLOW    | Read-only                                 |
| `mcp_gitkraken_git_log_or_diff`                     | ALLOW    | Read-only                                 |
| `mcp_gitkraken_git_blame`                           | ALLOW    | Read-only                                 |
| `mcp_gitkraken_git_status`                          | ALLOW    | Read-only                                 |
| `mcp_gitkraken_issues_get_detail`                   | ALLOW    | Read-only                                 |
| `mcp_gitkraken_issues_assigned_to_me`               | ALLOW    | Read-only                                 |
| `mcp_gitkraken_pull_request_get_detail`             | ALLOW    | Read-only                                 |
| `mcp_gitkraken_pull_request_get_comments`           | ALLOW    | Read-only                                 |
| `mcp_gitkraken_pull_request_assigned_to_me`         | ALLOW    | Read-only                                 |
| `mcp_gitkraken_gitkraken_workspace_list`            | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceDocString`                | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceDocuments`                | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceFileSyntaxErrors`         | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceSyntaxErrors`             | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceImports`                  | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceInstalledTopLevelModules` | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylancePythonEnvironments`       | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceSettings`                 | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceWorkspaceRoots`           | ALLOW    | Read-only                                 |
| `mcp_pylance_mcp_s_pylanceWorkspaceUserFiles`       | ALLOW    | Read-only                                 |

---

## 3. Agent & Meta Tool Calls (Always Allow)

These tools are unconditionally allowed. The gate does not inspect them.

| Tool                                                         | Notes                                  |
|--------------------------------------------------------------|----------------------------------------|
| `vscode_askQuestions` / `ask_questions`                      | Asking user is always permitted        |
| `manage_todo_list` / `TodoWrite` / `TodoRead` / `todo_write` | Internal agent planning                |
| `runSubagent` / `Agent` / `agent`                            | Subagent delegation                    |
| `tool_search_tool_regex` / `tool_search`                     | Tool discovery; no side effects        |
| `get_terminal_output`                                        | Read-only terminal inspection          |
| `terminal_last_command`                                      | Read-only terminal inspection          |
| `terminal_selection`                                         | Read-only terminal inspection          |
| `test_failure`                                               | VS Code internal                       |
| `get_vscode_api`                                             | VS Code internal                       |
| `switch_agent`                                               | VS Code internal                       |
| `copilot_getNotebookSummary`                                 | Read-only notebook inspection          |
| `get_search_view_results`                                    | Read-only search result access         |
| `install_extension`                                          | VS Code extension management           |
| `create_and_run_task`                                        | Task runner — VS Code manages task IDs |
| `get_task_output`                                            | Task output retrieval                  |
| `run_task`                                                   | VS Code task runner                    |
| `runTests`                                                   | Test runner                            |
| `await_terminal`                                             | Terminal wait — no side effects        |

---

## 4. Development & Environment Tool Calls

| Tool                                                                                 | Decision | Constraint                                     |
|--------------------------------------------------------------------------------------|----------|------------------------------------------------|
| `install_python_packages`                                                            | ALLOW    | Packages install into `.venv` within workspace |
| `configure_python_environment`                                                       | ALLOW    | Workspace-scoped                               |
| `configure_notebook` / `configure_python_notebook` / `configure_non_python_notebook` | ALLOW    | Workspace-scoped                               |
| `notebook_install_packages`                                                          | ALLOW    | Workspace-scoped                               |
| `notebook_list_packages`                                                             | ALLOW    | Read-only                                      |
| `run_notebook_cell`                                                                  | ALLOW    | Workspace-scoped execution                     |
| `restart_notebook_kernel`                                                            | ALLOW    | Workspace-scoped                               |
| `vscode_renameSymbol`                                                                | ALLOW    | Modifies source files; Inside zone only, path zone-checked       |
| `mcp_pylance_mcp_s_pylanceInvokeRefactoring`                                         | ALLOW    | Workspace-scoped code change                   |
| `mcp_pylance_mcp_s_pylanceUpdatePythonEnvironment`                                   | ALLOW    | Workspace-scoped                               |
| `mcp_pylance_mcp_s_pylanceRunCodeSnippet`                                            | ALLOW    | Executes within VS Code's Pylance language server context; cannot write to the file system directly |
| `renderMermaidDiagram`                                                               | ALLOW    | No side effects                                |
| `get_python_environment_details`                                                     | ALLOW    | Read-only                                      |
| `get_python_executable_details`                                                      | ALLOW    | Read-only                                      |

---

## 5. Elevated / Destructive Tool Calls

| Tool                                       | Decision            | Trigger condition                                                |
|--------------------------------------------|---------------------|------------------------------------------------------------------|
| `run_vscode_command`                       | ASK                 | Can invoke arbitrary VS Code commands including destructive ones |
| `open_browser_page`                        | ASK                 | Navigates external browser; potential data exposure              |
| `create_new_workspace`                     | BLOCK               | New workspace must be created via Safe Agent Environment Launcher|
| `kill_terminal`                            | ASK                 | Terminates a terminal session; may interrupt running processes   |
| `mcp_gitkraken_issues_add_comment`         | ASK                 | Writes to GitHub — irreversible                                  |
| `mcp_gitkraken_pull_request_create`        | ASK                 | Creates a PR — irreversible; see GitHub rules §7                 |
| `mcp_gitkraken_pull_request_create_review` | ASK                 | Creates a PR review — irreversible                               |
| `mcp_gitkraken_gitlens_commit_composer`    | ALLOW               | Local repo operation; subject to §7 push rules (aligns with `git commit` and `mcp_gitkraken_git_add_or_commit`) |
| `mcp_gitkraken_gitlens_start_work`         | ALLOW               | Read-only planning operation                                     |
| `mcp_gitkraken_gitlens_start_review`       | ALLOW               | Read-only planning operation                                     |
| `mcp_gitkraken_gitlens_launchpad`          | ALLOW               | Dashboard view — read-only                                       |
| `mcp_gitkraken_git_push`                   | See §7 GitHub Rules | Push to org-owned repo: whitelist check required                 |
| `mcp_gitkraken_git_branch`                 | ALLOW               | Local repo operation                                             |
| `mcp_gitkraken_git_checkout`               | ALLOW               | Local repo operation                                             |
| `mcp_gitkraken_git_stash`                  | ALLOW               | Local repo operation                                             |
| `mcp_gitkraken_git_add_or_commit`          | ALLOW               | Local repo operation                                             |
| `mcp_gitkraken_git_worktree`               | ALLOW               | Local repo operation                                             |

---

## 6. Terminal Commands (`run_in_terminal`)

### 6.A Always-Blocked Terminal Patterns

Applied before any allowlist check. Any match → BLOCK regardless of context.

| Pattern                                            | Example                     | Reason                  |
|----------------------------------------------------|-----------------------------|-------------------------|
| `perl -e`                                          | `perl -e 'print "x"'`       | Inline interpreter      |
| `ruby -e`                                          | `ruby -e 'puts "x"'`        | Inline interpreter      |
| `node -e` / `--eval`                               | `node -e "console.log(1)"`  | Inline interpreter      |
| `php -r`                                           | `php -r "echo 1;"`          | Inline interpreter      |
| `bash -c` / `sh -c` / `zsh -c`                     | `bash -c "rm -rf /"`        | Shell injection         |
| `cmd.exe /c` / `cmd /k`                            | `cmd /c del *`              | Shell injection         |
| `ipython -c`                                       | `ipython -c "import os"`    | Inline interpreter      |
| `python -m code`                                   | `python -m code`            | Interactive REPL        |
| PowerShell `-EncodedCommand` with payload          | `pwsh -enc AABB...`         | Base64 obfuscation      |
| `iex` / `Invoke-Expression`                        | `iex (curl ...)`            | Dynamic execution       |
| `Start-Process`                                    | `Start-Process malware.exe` | Process spawning        |
| `& $var`                                           | `& $cmd`                    | Variable-driven call    |
| `[Convert]::FromBase64String` / `FromBase64String` | any                         | Base64 decoding         |
| `\| bash` / `\| python` / `\| pwsh` / etc.         | `curl x \| bash`            | Pipe-to-interpreter     |
| `\| iex`                                           | `... \| iex`                | Pipe-to-PowerShell-exec |
| `` ` `` backtick subshell | `` `ls` `` | Subshell |
| `$(...)` subshell | `$(cat /etc/passwd)` | Subshell |
| `eval` | `eval "$cmd"` | Dynamic eval |
| `exec` | `exec bash` | Process replacement |
| `source <file>` (non-venv) | `source evil.sh` | External script sourcing |
| `. <file>` POSIX dot-source (non-venv) | `. evil.sh` | External script sourcing |
| `-ExecutionPolicy Bypass` | `powershell -ExecutionPolicy Bypass` | Policy bypass |
| `Invoke-Item` | `Invoke-Item malware.exe` | File opener |
| `Set-Alias` / `New-Alias` | `Set-Alias rm rm-safe` | Alias hijacking |
| `<(...)` / `>(...)` process substitution | `diff <(cmd1) <(cmd2)` | Subshell |
| `format` / `fdisk` / `diskpart` | any | Disk destructive |
| `dd if=` / `dd of=` | `dd if=/dev/zero of=/dev/sda` | Disk destructive |
| `shutdown` / `Restart-Computer` | any | System power |
| `reg add` / `reg delete` | any | Registry write |
| `Set-ItemProperty HKLM:` / `HKCU:` / `HKCR:` | any | Registry write |
| `sudo` / `runas` | any | Privilege escalation |
| `update_hashes` (substring) | any command containing this | Protects gate hash update — operator-only |
| `python -c` | `python -c "import os; ..."` | Inline interpreter; full stdlib access bypasses all command-level blocks — consistent with all other language `-c`/`-e`/`-r` blocks |
| `wsl` / `wsl.exe` | `wsl bash -c "rm -rf /"` | Runs Linux subsystem; bypasses all Windows-specific terminal restrictions |
| `certutil` | `certutil -decode` / `certutil -urlcache -f <url>` | Windows built-in that can Base64-decode and download from internet — contradicts §6.A Base64 block |
| `schtasks` / `at` / `Register-ScheduledTask` | any | Persistence mechanism; no legitimate agent use |
| `curl` / `wget` / `Invoke-WebRequest` / `iwr` | any | Primary data exfiltration vector; all legitimate download needs are covered by `pip` / `fetch_webpage` |

### 6.B Allowlisted Terminal Commands

All path arguments for commands marked `zone-checked` must resolve inside the project folder. Commands outside path are BLOCK.

**Category A — Python Runtime**

| Command                     | Allowed flags/subcommands                                   | Denied flags          | Notes                                                                    |
|-----------------------------|-------------------------------------------------------------|-----------------------|--------------------------------------------------------------------------|
| `python` / `python3` / `py` | Any args; `-m` restricted to approved modules               | `-i`, `--interactive` | Zone-check path args. `python -c` is BLOCK — see §6.A (inline interpreter). |
| Approved `-m` modules       | `pytest`, `build`, `pip`, `setuptools`, `hatchling`, `venv` | All others            | `python -m evil_module` → BLOCK                                          |

**Category B — Package Management**

| Command | Allowed subcommands | Notes |
|---|---|---|
| `pip` / `pip3` | `install`, `uninstall`, `list`, `show`, `freeze`, `check`, `download`, `config` | Zone-check path args |

**Category C — Testing**

| Command | Notes |
|---|---|
| `pytest` | All standard flags; path args zone-checked |

**Category D — Build Tools**

| Command       | Allowed subcommands                                | Notes                        |
|---------------|----------------------------------------------------|------------------------------|
| `pyinstaller` | All                                                | Path args zone-checked       |
| `hatch`       | `build`, `run`, `env`, `dep`, `version`, `publish` | —                            |
| `build`       | All                                                | `python -m build` invocation |
| `twine`       | `check`, `upload`                                  | —                            |

**Category E — Version Control**

| Command | Allowed subcommands | Denied flags/combos |
|---|---|---|
| `git` | `status`, `log`, `diff`, `branch`, `add`, `commit` (including `--amend` for unpushed commits only — amending already-pushed history is not permitted), `fetch`, `pull`, `push`, `checkout`, `switch`, `stash`, `tag`, `show`, `remote`, `blame`, `config`, `init`, `clone`, `merge`, `rebase`, `describe`, `shortlog`, `rev-parse`, `ls-files` | `--force`, `-f` globally; `push --force`, `push -f`, `push --force-with-lease`, `reset --hard`, `clean -f`, `clean -fd`, `filter-branch`, `gc --force` |
| `git push` to `turbulencesolutions` org | See §7 — GitHub-specific rules apply | — |

**Category F — Node / NPM Ecosystem**

| Command | Allowed subcommands | Denied flags |
|---|---|---|
| `npm` | `install`, `ci`, `run`, `test`, `build`, `start`, `pack`, `publish`, `list`, `ls`, `outdated`, `update`, `audit` | — |
| `yarn` | `install`, `add`, `remove`, `run`, `test`, `build`, `upgrade`, `list`, `audit` | — |
| `pnpm` | `install`, `ci`, `run`, `test`, `build`, `start`, `pack`, `publish`, `list`, `ls`, `outdated`, `update`, `audit` | — |
| `node` | File args only | `-e`, `--eval`, `--interactive`, `-i` |
| `npx` | All (unknown packages — always forwarded to user judgment) | — |

**Category G — Read-only File Inspection**

All commands zone-check path args. Outside-project paths → BLOCK.

`cat`, `type`, `head`, `tail`, `less`, `more`, `diff`, `fc`, `comp`, `sort`, `uniq`, `awk`, `sed`, `ls`, `dir`, `get-childitem`, `gci`, `get-content`, `gc`, `select-string`, `findstr`, `grep`, `wc`, `file`, `stat`, `test-path`

**Category H — Navigation & Environment**

| Command                                        | Notes                                 |
|------------------------------------------------|---------------------------------------|
| `cd` / `set-location` / `sl` / `push-location` | Path zone-checked                     |
| `pwd` / `get-location` / `gl`                  | No args; always safe                  |
| `which` / `where` / `get-command` / `gcm`      | Command lookup; no zone risk          |
| `env` / `printenv`                             | Read env vars; safe                   |
| `echo` / `write-host` / `write-output`         | Free-form output; no path enforcement |

**Category I — VS Code CLI**

| Command | Allowed subcommands                                                              |
|---------|----------------------------------------------------------------------------------|
| `code`  | `--version`, `--list-extensions`, `--install-extension`, `--uninstall-extension` |

**Category J — File Creation/Copy/Move**

All zone-check both source and destination. Outside-project path on either side → BLOCK.

`mkdir`, `new-item`, `ni`, `cp`, `copy`, `copy-item`, `mv`, `move`, `move-item`, `touch`, `chmod`, `ln`

**Category K — Recursive Listing**

`tree`, `find` — path args zone-checked including ancestor-of-deny-zone check.

**Category L — Write Commands**

`set-content`, `add-content`, `ac`, `out-file`, `rename-item`, `ren`, `tee-object`, `tee` — path args zone-checked. (`sc` removed — alias conflicts with Windows Service Control Manager `sc.exe`; use full `set-content` instead.)

**Category M — Delete Commands**

`rm`, `del`, `erase`, `rmdir`, `remove-item`, `ri` — ALL path args must be inside project folder. Any arg outside → BLOCK. No ASK: deletion outside project is a hard BLOCK.

**Category N — Other**

| Command | Decision | Notes |
|---|---|---|
| `venv activation` (`.venv/Scripts/Activate.ps1`, `source .venv/bin/activate`, etc.) | ALLOW | Explicitly whitelisted before obfuscation patterns |
| Any unrecognized command | BLOCK | Unknown verbs are denied by default |

---

## 7. GitHub Repository Access Control

### 7.1 Definitions

| Term          | Value                                                                                                            |
|---------------|------------------------------------------------------------------------------------------------------------------|
| Protected org | `github.com/turbulencesolutions` (case-insensitive)                                                              |
| Whitelist     | `.github/hooks/scripts/repository_whitelist.json` — list of explicitly permitted `turbulencesolutions` repo URLs |
| Personal repo | Any GitHub repository NOT under `github.com/turbulencesolutions/`                                                |

### 7.2 Read Operations (always allowed)

| Operation                                        | Target                                  | Decision |
|--------------------------------------------------|-----------------------------------------|----------|
| `git clone` / `git fetch` / `git pull`           | Any URL (including turbulencesolutions) | ALLOW    |
| `git log`, `git diff`, `git status`, `git blame` | Any local clone                         | ALLOW    |
| GitHub API read (issues, PRs, file content)      | Any org including turbulencesolutions   | ALLOW    |

### 7.3 Write / Push Operations

| Operation                      | Target                                                 | Decision                           |
|--------------------------------|--------------------------------------------------------|------------------------------------|
| `git push`                     | Personal repo (no `turbulencesolutions` in remote URL) | ALLOW                              |
| `git push`                     | `turbulencesolutions` repo — URL in whitelist          | ALLOW                              |
| `git push`                     | `turbulencesolutions` repo — URL NOT in whitelist      | BLOCK                              |
| `mcp_gitkraken_git_push`       | Personal repo                                          | ALLOW                              |
| `mcp_gitkraken_git_push`       | `turbulencesolutions` repo — URL in whitelist          | ALLOW                              |
| `mcp_gitkraken_git_push`       | `turbulencesolutions` repo — URL NOT in whitelist      | BLOCK                              |
| `git push --force` / `push -f` | Any target                                             | BLOCK (force-push globally denied) |
| `git push --force-with-lease`   | Any target                                             | BLOCK (history rewrite; equivalent risk to `--force`)  |

### 7.4 Repository Creation

| Operation                                                 | Target                  | Decision |
|-----------------------------------------------------------|-------------------------|----------|
| `gh repo create <name>` (personal, no org)                | User's personal account | ALLOW    |
| `gh repo create turbulencesolutions/<name>`               | Organization            | BLOCK    |
| `gh repo create --org turbulencesolutions`                | Organization            | BLOCK    |
| Creating repo via any API under `turbulencesolutions` org | Organization            | BLOCK    |

### 7.5 GitHub Social / Review Operations

| Operation               | Target   | Decision |
|-------------------------|----------|----------|
| Create issue comment    | Any repo | ASK      |
| Create pull request     | Any repo | ASK      |
| Create PR review        | Any repo | ASK      |
| Close / reopen issue    | Any repo | ASK      |
| Merge pull request      | Any repo | ASK      |
| Delete branch on remote | Any repo | ASK      |

### 7.6 Whitelist Configuration

```json
// .github/hooks/scripts/repository_whitelist.json
{
  "allowed_turbulencesolutions_repositories": [
    "https://github.com/turbulencesolutions/example-repo"
  ]
}
```

- **Scope: workspace-local only.** The whitelist file lives inside `.github/hooks/scripts/` of a specific workspace. It is never shared, inherited, or copied to other workspaces. Adding an entry to workspace A has zero effect on workspace B.
- **Default state: empty list** → all `turbulencesolutions` push operations blocked in every new workspace until an entry is explicitly added by the operator.
- Entries can be added or removed at any time after workspace creation. Changes take effect immediately on the next tool call; no restart required.
- Creating a workspace from a template does not carry over whitelist entries — the template ships with an empty list and each workspace starts clean.
- Personal repositories (non-`turbulencesolutions` origin URL) are auto-allowed and do not require whitelist entries in any workspace.
- The gate resolves `git remote get-url origin` to determine the push target URL before evaluating the whitelist.
- Whitelist entries are matched case-insensitively against the full remote URL.

---

## 8. Unconditional Hard Blocks (No ASK Possible)

These are non-negotiable regardless of user intent, whitelist, or instruction file overrides.

| Action                                                                | Reason                                            |
|-----------------------------------------------------------------------|---------------------------------------------------|
| Write to `.github/hooks/` (any file)                                  | Protects the security gate from self-modification |
| Read from `.github/hooks/` (any file)                                 | Gate code is not agent-readable                   |
| Write to `.vscode/`                                                   | Prevents settings tampering                       |
| Write to `NoAgentZone/`                                               | Explicit exclusion zone                           |
| Write to any path outside workspace root                              | Cross-workspace contamination                     |
| `git push --force` / `-f` to any remote                               | Irreversible history rewrite                      |
| `git push --force-with-lease` to any remote                           | History rewrite; equivalent risk to `--force`     |
| `git reset --hard`                                                    | Irreversible local state destruction              |
| `git clean -f` / `-fd`                                                | Irreversible untracked file deletion              |
| `git filter-branch`                                                   | History rewrite                                   |
| Disk utilities: `format`, `fdisk`, `diskpart`, `dd if=/dd of=`        | Disk destruction                                  |
| `shutdown` / `Restart-Computer`                                       | OS state                                          |
| Registry writes (`reg add/delete`, `Set-ItemProperty HKLM/HKCU/HKCR`) | System config                                     |
| `sudo` / `runas`                                                      | Privilege escalation                              |
| All obfuscation patterns (§6.A)                                       | Attack vectors with no legitimate use             |
| Any unrecognized terminal verb                                        | Deny-by-default                                   |
| `update_hashes` in any terminal command                               | Operator-only gate maintenance                    |
| `turbulencesolutions` repo push without whitelist entry               | Org repo protection                               |
| `gh repo create` under `turbulencesolutions` org                      | Org namespace protection                          |

---

## 9. What the Gate Cannot Prevent (Honest Residual Risk)

| Risk                                                      | Why it cannot be prevented                                                          |
|-----------------------------------------------------------|-------------------------------------------------------------------------------------|
| Agent writes a script inside the workspace, then runs it  | Script content is not inspected; execution of in-project scripts is ALLOW by design |
| Script reads files outside workspace                      | OS permissions govern; no sandbox on Windows                                        |
| Script exfiltrates data via network                       | Network access is unrestricted on Windows                                           |
| Agent uses `git push` via a script (not direct tool call) | Script bypass; URL resolved only for direct terminal `git push` calls               |
| Prompt injection via file content read by agent           | Not a gate concern; LLM-level problem                                               |
| `run_task` / `create_and_run_task` task bypass            | Operator-defined tasks execute without gate inspection; trusted as operator-authored and not modifiable by agents |
| `install_python_packages` supply-chain risk               | Packages execute arbitrary code at install time (setup.py / build hooks); mitigated by `.venv` scoping but not fully contained |
| PowerShell pipeline chaining                              | Individually-allowed commands (Category G + L) can be combined to produce blocked effects; gate inspects verbs only, not pipeline semantics |

These risks are accepted. The gate is designed to prevent accidental damage and raise the cost of low-effort attacks, not to provide OS-level containment.
