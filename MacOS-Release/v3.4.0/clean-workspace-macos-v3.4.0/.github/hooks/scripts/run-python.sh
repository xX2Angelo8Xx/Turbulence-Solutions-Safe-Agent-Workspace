#!/usr/bin/env bash
# =============================================================================
#  run-python.sh — macOS Python runner for the Turbulence Solutions security gate
#
#  Reads the Python executable path from python-path.txt (same directory as
#  this script) and delegates all arguments to that Python interpreter.
#
#  SETUP: Edit python-path.txt to point to your Python 3.11+ installation:
#    - Default:           python3   (works if python3 is already in your PATH)
#    - Homebrew:          /opt/homebrew/bin/python3.11
#    - System Python:     /usr/bin/python3
#    - pyenv:             /Users/yourname/.pyenv/shims/python3
#
#  The security gate will deny all agent actions if Python cannot be found.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH_FILE="$SCRIPT_DIR/python-path.txt"

# ---------------------------------------------------------------------------
#  Resolve Python path from python-path.txt
# ---------------------------------------------------------------------------
PYTHON=""

if [ -f "$PYTHON_PATH_FILE" ]; then
    # Read the first non-empty, non-comment line; strip whitespace
    PYTHON=$(grep -v '^\s*#' "$PYTHON_PATH_FILE" | grep -v '^\s*$' | head -n 1 | tr -d '[:space:]')
fi

# Fall back to python3 in PATH if file is missing or empty
if [ -z "$PYTHON" ]; then
    PYTHON="python3"
fi

# ---------------------------------------------------------------------------
#  Verify the Python executable is usable
# ---------------------------------------------------------------------------
if ! command -v "$PYTHON" >/dev/null 2>&1 && [ ! -x "$PYTHON" ]; then
    # Python not found — emit a deny response so the security gate fails closed
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Security gate cannot run: Python not found. Edit .github/hooks/scripts/python-path.txt with your Python 3.11+ path (e.g. /opt/homebrew/bin/python3.11) and restart VS Code."}}\n'
    exit 0
fi

# ---------------------------------------------------------------------------
#  Delegate to Python — pass all arguments through unchanged
# ---------------------------------------------------------------------------
exec "$PYTHON" "$@"
