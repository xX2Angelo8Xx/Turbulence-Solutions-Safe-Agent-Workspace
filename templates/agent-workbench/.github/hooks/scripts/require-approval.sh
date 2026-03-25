#!/bin/bash
# =============================================================================
#  PreToolUse Hook – Turbulence Solutions Default Project Safety Framework
#  Pure bash – no external dependencies (no jq, no python)
#  Ref: https://code.visualstudio.com/docs/copilot/customization/hooks
#
#  Works with: Git Bash, WSL, macOS bash/zsh, Linux bash
# =============================================================================

INPUT=$(cat)

# ---------------------------------------------------------------------------
#  Response templates
#  NOTE: All responses MUST exit 0. Non-zero exit = VS Code treats hook as
#  crashed and falls back to default behavior (silently allows reads).
# ---------------------------------------------------------------------------
ALLOW='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
ASK='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Turbulence Solutions Safety: Approval required for this action."}}'
DENY='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"BLOCKED: .github, .vscode, and NoAgentZone are permanently restricted. This denial is enforced by a PreToolUse hook and cannot be bypassed. Do NOT retry this action or attempt alternative paths to access these folders."}}'

# ---------------------------------------------------------------------------
#  Blocked folder names (lowercase, used for pattern matching)
# ---------------------------------------------------------------------------
BLOCKED_PATTERN='\.github|\.vscode|noagentzone'

# ---------------------------------------------------------------------------
#  Normalize: convert any path to a comparable lowercase forward-slash form
#  Handles: JSON-escaped \\, backslashes, WSL /mnt/X/, Git Bash /X/, drive X:\
# ---------------------------------------------------------------------------
normalize() {
  local p="$1"
  # JSON-escaped double backslashes → forward slash
  p="${p//\\\\/\/}"
  # Remaining single backslashes → forward slash
  p="${p//\\//}"
  # Lowercase
  p=$(echo "$p" | tr '[:upper:]' '[:lower:]')
  # WSL mount prefix: /mnt/c/Users/... → c:/Users/...
  if [[ "$p" =~ ^/mnt/([a-z])/(.*) ]]; then
    p="${BASH_REMATCH[1]}:/${BASH_REMATCH[2]}"
  # Git Bash / MSYS2 prefix: /c/Users/... → c:/Users/...
  elif [[ "$p" =~ ^/([a-z])/(.*) ]]; then
    p="${BASH_REMATCH[1]}:/${BASH_REMATCH[2]}"
  fi
  # Strip trailing slash
  p="${p%/}"
  echo "$p"
}

# ---------------------------------------------------------------------------
#  Resolve workspace root dynamically
#  VS Code runs hook commands with cwd = workspace root
# ---------------------------------------------------------------------------
WS_NORM=$(normalize "$(pwd)")

# ---------------------------------------------------------------------------
#  get_relative: strip workspace root prefix from an absolute path
# ---------------------------------------------------------------------------
get_relative() {
  local full="$1"
  local root="$2"
  if [[ "$full" == "$root/"* ]]; then
    echo "${full#"$root"/}"
    return
  fi
  echo "$full"
}

# ---------------------------------------------------------------------------
#  Zone check: returns "deny", "allow", or "ask"
#  Uses BOTH prefix-based and pattern-based matching for robustness
# ---------------------------------------------------------------------------
check_zone() {
  local path_norm="$1"
  local rel

  # --- METHOD 1: Prefix-based (strip workspace root) ---
  rel=$(get_relative "$path_norm" "$WS_NORM")

  case "$rel" in
    .github|.github/*|.vscode|.vscode/*|noagentzone|noagentzone/*)
      echo "deny"
      return
      ;;
    project|project/*)
      echo "allow"
      return
      ;;
  esac

  # --- METHOD 2: Pattern-based fallback ---
  # Catches cases where pwd normalization doesn't match tool input format
  if echo "$path_norm" | grep -qiE "/(${BLOCKED_PATTERN})(/|$)"; then
    echo "deny"
    return
  fi
  if echo "$path_norm" | grep -qiE '/project(/|$)'; then
    echo "allow"
    return
  fi

  echo "ask"
}

# ---------------------------------------------------------------------------
#  Extract tool name
# ---------------------------------------------------------------------------
TOOL=$(echo "$INPUT" | grep -oE '"tool_name" *: *"[^"]*"' | head -1 | sed 's/"tool_name" *: *"//;s/"$//')

# ---------------------------------------------------------------------------
#  Always-allow tools (no path check needed)
#  - ask_questions: user interaction, always safe
#  - todo tools: task tracking, no file system access
#  - runSubagent/search_subagent/Agent: launch subagents (security enforced
#    inside the subagent via the same hook; blocking here stalls the parent)
# ---------------------------------------------------------------------------
if echo "$TOOL" | grep -qiE '^(vscode_ask_questions|ask_questions|TodoWrite|TodoRead|todo_write|manage_todo_list|runSubagent|search_subagent|Agent|agent)$'; then
  printf '%s\n' "$ALLOW"
  exit 0
fi

# ---------------------------------------------------------------------------
#  Terminal commands: inspect the ENTIRE input for blocked path references
#  If a blocked path is found → DENY (not just ASK)
#  If no blocked path → ASK (user must still approve)
#  NOTE: We search the raw INPUT instead of extracting the command field
#  because command values often contain escaped quotes that break regex.
# ---------------------------------------------------------------------------
if echo "$TOOL" | grep -qiE '^(run_in_terminal|terminal|run_command)$'; then
  # Normalize entire input for matching (unescape, lowercase)
  INPUT_NORM=$(echo "$INPUT" | sed 's/\\\\/\//g; s/\\/\//g' | tr '[:upper:]' '[:lower:]')
  if echo "$INPUT_NORM" | grep -qiE '\.github|\.vscode|noagentzone'; then
    printf '%s\n' "$DENY"
    exit 0
  fi
  # No blocked reference → still ask (terminal is never auto-allowed)
  printf '%s\n' "$ASK"
  exit 0
fi

# ---------------------------------------------------------------------------
#  Exempt tools: auto-allowed inside Project/, ask elsewhere
#  Non-exempt tools: always ask
# ---------------------------------------------------------------------------
EXEMPT_REGEX="^(read_file|Read|edit_file|replace_string_in_file|multi_replace_string_in_file|create_file|write_file|Edit|Write|list_dir|search|grep_search|semantic_search|file_search|Glob|agent|Agent|runSubagent|search_subagent)$"

if ! echo "$TOOL" | grep -qE "$EXEMPT_REGEX"; then
  printf '%s\n' "$ASK"
  exit 0
fi

# ---------------------------------------------------------------------------
#  Extract file path from tool input
#  Checks common parameter names in order of priority
# ---------------------------------------------------------------------------
PATH_RAW=$(echo "$INPUT" | grep -oE '"(filePath|file_path|path|directory|pattern|target|query)" *: *"[^"]*"' \
  | head -1 | sed 's/"[^"]*" *: *"//;s/"$//')

# No recognizable path → ask (safe default)
if [ -z "$PATH_RAW" ]; then
  printf '%s\n' "$ASK"
  exit 0
fi

# Normalize the extracted path
PATH_NORM=$(normalize "$PATH_RAW")

# If path is relative (no drive letter, no leading /), resolve against workspace
if [[ "$PATH_NORM" != /* ]] && [[ ! "$PATH_NORM" =~ ^[a-z]: ]]; then
  PATH_NORM="$WS_NORM/$PATH_NORM"
fi

# ---------------------------------------------------------------------------
#  Determine zone and respond
# ---------------------------------------------------------------------------
ZONE=$(check_zone "$PATH_NORM")

case "$ZONE" in
  deny)
    printf '%s\n' "$DENY"
    exit 0
    ;;
  allow)
    printf '%s\n' "$ALLOW"
    exit 0
    ;;
  *)
    printf '%s\n' "$ASK"
    exit 0
    ;;
esac
