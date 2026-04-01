# =============================================================================
#  PreToolUse Hook – Turbulence Solutions Default Project Safety Framework
#  PowerShell version – for Windows (ARM and x64)
#  Ref: https://code.visualstudio.com/docs/copilot/customization/hooks
#
#  Compatible with: Windows PowerShell 5.1, PowerShell 7+
# =============================================================================

# Ensure stdin/stdout use UTF-8 so JSON round-trips correctly
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$INPUT_JSON = [Console]::In.ReadToEnd()

# ---------------------------------------------------------------------------
#  Response templates
#  NOTE: All paths must exit 0. Non-zero exit = VS Code treats hook as
#  crashed and falls back to default behavior (silently allows reads).
# ---------------------------------------------------------------------------
$ALLOW = '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
$ASK   = '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Turbulence Solutions Safety: Approval required for this action."}}'
$DENY  = '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"BLOCKED: .github, .vscode, and NoAgentZone are permanently restricted. This denial is enforced by a PreToolUse hook and cannot be bypassed. Do NOT retry this action or attempt alternative paths to access these folders."}}'

# ---------------------------------------------------------------------------
#  Normalize: convert any path to a comparable lowercase forward-slash form
#  Handles: JSON-escaped \\, backslashes, WSL /mnt/X/, Git Bash /X/, X:\
# ---------------------------------------------------------------------------
function Normalize-HookPath {
    param([string]$p)
    $p = $p -replace '\\\\', '/'    # JSON-escaped double backslashes → /
    $p = $p -replace '\\',   '/'    # Remaining single backslashes → /
    $p = $p.ToLowerInvariant()
    # WSL mount prefix: /mnt/c/Users/… → c:/Users/…
    if ($p -match '^/mnt/([a-z])/(.+)') {
        $p = "$($Matches[1]):/$($Matches[2])"
    # Git Bash / MSYS2 prefix: /c/Users/… → c:/Users/…
    } elseif ($p -match '^/([a-z])/(.+)') {
        $p = "$($Matches[1]):/$($Matches[2])"
    }
    return $p.TrimEnd('/')
}

# ---------------------------------------------------------------------------
#  Resolve workspace root dynamically
#  VS Code runs hook commands with cwd = workspace root
# ---------------------------------------------------------------------------
$WS_ROOT = Normalize-HookPath -p (Get-Location).Path

# ---------------------------------------------------------------------------
#  Strip workspace root prefix to get a relative path
# ---------------------------------------------------------------------------
function Get-RelativePath {
    param([string]$full, [string]$root)
    if ($full.StartsWith("$root/")) { return $full.Substring($root.Length + 1) }
    return $full
}

# ---------------------------------------------------------------------------
#  Zone check: returns "deny", "allow", or "ask"
#  Uses BOTH prefix-based and pattern-based matching for robustness
# ---------------------------------------------------------------------------
function Get-Zone {
    param([string]$path)
    $rel = Get-RelativePath -full $path -root $WS_ROOT

    # --- METHOD 1: Prefix-based (strip workspace root) ---
    if ($rel -match '^(\.github|\.vscode|noagentzone)(/|$)') { return 'deny'  }
    if ($rel -match '^project(/|$)')                          { return 'allow' }

    # --- METHOD 2: Pattern-based fallback ---
    # Catches cases where pwd normalization doesn't match tool input format
    if ($path -match '/(\.github|\.vscode|noagentzone)(/|$)') { return 'deny'  }
    if ($path -match '/project(/|$)')                          { return 'allow' }

    return 'ask'
}

# ---------------------------------------------------------------------------
#  Extract tool name
# ---------------------------------------------------------------------------
$TOOL = ''
if ($INPUT_JSON -match '"tool_name"\s*:\s*"([^"]*)"') { $TOOL = $Matches[1] }

# ---------------------------------------------------------------------------
#  Always-allow tools (no path check needed)
#  - ask_questions: user interaction, always safe
#  - todo tools: task tracking, no file system access
#  - runSubagent/search_subagent/Agent: security enforced inside subagent
# ---------------------------------------------------------------------------
if ($TOOL -match '^(vscode_askQuestions|vscode_ask_questions|ask_questions|TodoWrite|TodoRead|todo_write|manage_todo_list|runSubagent|search_subagent|Agent|agent|get_terminal_output|terminal_last_command|terminal_selection|test_failure|tool_search|get_vscode_api|switch_agent|copilot_getNotebookSummary|get_search_view_results|install_extension|create_and_run_task|get_task_output|runTests)$') {
    Write-Output $ALLOW
    exit 0
}

# ---------------------------------------------------------------------------
#  Terminal commands: scan entire input for blocked path references
#  Blocked reference found → DENY; no blocked reference → ASK
# ---------------------------------------------------------------------------
if ($TOOL -match '^(run_in_terminal|terminal|run_command)$') {
    $norm = ($INPUT_JSON -replace '\\\\', '/' -replace '\\', '/').ToLowerInvariant()
    if ($norm -match '\.github|\.vscode|noagentzone') {
        Write-Output $DENY
    } else {
        Write-Output $ASK
    }
    exit 0
}

# ---------------------------------------------------------------------------
#  Exempt tools: auto-allowed inside Project/, ask elsewhere
#  Non-exempt tools: always ask
# ---------------------------------------------------------------------------
$EXEMPT = '^(read_file|Read|edit_file|replace_string_in_file|multi_replace_string_in_file|create_file|write_file|Edit|Write|list_dir|search|grep_search|semantic_search|file_search|Glob|agent|Agent|runSubagent|search_subagent)$'
if ($TOOL -notmatch $EXEMPT) {
    Write-Output $ASK
    exit 0
}

# ---------------------------------------------------------------------------
#  Extract file path from tool input
#  Checks common parameter names in order of priority
# ---------------------------------------------------------------------------
$PATH_RAW = ''
if ($INPUT_JSON -match '"(?:filePath|file_path|path|directory|pattern|target|query)"\s*:\s*"([^"]*)"') {
    $PATH_RAW = $Matches[1]
}

# No recognizable path → ask (safe default)
if ([string]::IsNullOrEmpty($PATH_RAW)) {
    Write-Output $ASK
    exit 0
}

# Normalize the extracted path
$PATH_NORM = Normalize-HookPath -p $PATH_RAW

# If path is relative (no drive letter, no leading /), resolve against workspace
if ($PATH_NORM -notmatch '^[a-z]:' -and -not $PATH_NORM.StartsWith('/')) {
    $PATH_NORM = "$WS_ROOT/$PATH_NORM"
}

# ---------------------------------------------------------------------------
#  Determine zone and respond
# ---------------------------------------------------------------------------
switch (Get-Zone -path $PATH_NORM) {
    'deny'  { Write-Output $DENY;  exit 0 }
    'allow' { Write-Output $ALLOW; exit 0 }
    default { Write-Output $ASK;   exit 0 }
}
