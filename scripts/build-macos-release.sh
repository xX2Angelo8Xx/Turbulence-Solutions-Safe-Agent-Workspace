#!/usr/bin/env bash
# =============================================================================
#  build-macos-release.sh — Build macOS-specific workspace templates
#
#  Produces macOS variants of clean-workspace and agent-workbench inside
#  MacOS-Release/v3.4.0/. Each variant is identical to the standard template
#  except that the security gate hook is wired to a local python-path.txt file
#  instead of the ts-python shim (which requires the full AEL installer).
#
#  Usage:
#    bash scripts/build-macos-release.sh
#
#  Output:
#    MacOS-Release/v3.4.0/clean-workspace-macos-v3.4.0/
#    MacOS-Release/v3.4.0/agent-workbench-macos-v3.4.0/
#
#  Run from the repository root.
# =============================================================================

set -euo pipefail

VERSION="v3.4.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/templates"
DEST_DIR="$REPO_ROOT/MacOS-Release/$VERSION"

info()    { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
success() { printf '\033[0;32m[OK]\033[0m    %s\n' "$*"; }

# ---------------------------------------------------------------------------
#  Validate repo root
# ---------------------------------------------------------------------------
if [ ! -f "$REPO_ROOT/pyproject.toml" ]; then
    printf '\033[0;31m[ERROR]\033[0m Run this script from the repository root.\n' >&2
    exit 1
fi

mkdir -p "$DEST_DIR"

# ---------------------------------------------------------------------------
#  build_variant <template_name> <output_name>
#  Copies the template, injects macOS-specific files, patches the hook config.
# ---------------------------------------------------------------------------
build_variant() {
    local TEMPLATE_NAME="$1"
    local OUTPUT_NAME="$2"
    local SRC="$TEMPLATES_DIR/$TEMPLATE_NAME"
    local DEST="$DEST_DIR/$OUTPUT_NAME"

    info "Building $OUTPUT_NAME ..."

    # Fresh copy
    rm -rf "$DEST"
    cp -r "$SRC" "$DEST"

    # Remove Python bytecode cache (not useful in a release package)
    find "$DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    local SCRIPTS_DIR="$DEST/.github/hooks/scripts"
    local HOOKS_DIR="$DEST/.github/hooks"

    # ----  python-path.txt  -------------------------------------------------
    cat > "$SCRIPTS_DIR/python-path.txt" << 'EOF'
python3
EOF

    # ----  run-python.sh  ---------------------------------------------------
    cat > "$SCRIPTS_DIR/run-python.sh" << 'RUNNER'
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

# Resolve Python path from python-path.txt
PYTHON=""

if [ -f "$PYTHON_PATH_FILE" ]; then
    PYTHON=$(grep -v '^\s*#' "$PYTHON_PATH_FILE" | grep -v '^\s*$' | head -n 1 | tr -d '[:space:]')
fi

# Fall back to python3 in PATH if file is missing or empty
if [ -z "$PYTHON" ]; then
    PYTHON="python3"
fi

# Verify the Python executable is usable
if ! command -v "$PYTHON" >/dev/null 2>&1 && [ ! -x "$PYTHON" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Security gate cannot run: Python not found. Edit .github/hooks/scripts/python-path.txt with your Python 3.11+ path (e.g. /opt/homebrew/bin/python3.11) and restart VS Code."}}\n'
    exit 0
fi

exec "$PYTHON" "$@"
RUNNER

    chmod +x "$SCRIPTS_DIR/run-python.sh"

    # ----  require-approval.json  (add "macos" key)  ------------------------
    cat > "$HOOKS_DIR/require-approval.json" << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "ts-python .github/hooks/scripts/security_gate.py",
        "windows": "ts-python .github/hooks/scripts/security_gate.py",
        "macos": "bash .github/hooks/scripts/run-python.sh .github/hooks/scripts/security_gate.py",
        "timeout": 15
      }
    ]
  }
}
EOF

    success "Built: $DEST"
}

# ---------------------------------------------------------------------------
#  Build both variants
# ---------------------------------------------------------------------------
build_variant "clean-workspace"  "clean-workspace-macos-$VERSION"
build_variant "agent-workbench"  "agent-workbench-macos-$VERSION"

# ---------------------------------------------------------------------------
#  Summary
# ---------------------------------------------------------------------------
printf '\n'
success "macOS release packages built in MacOS-Release/$VERSION/"
printf '\n'
printf '  Packages:\n'
printf '    clean-workspace-macos-%s/\n' "$VERSION"
printf '    agent-workbench-macos-%s/\n' "$VERSION"
printf '\n'
printf '  User setup (first time, one minute):\n'
printf '    1. Open the workspace folder in VS Code.\n'
printf '    2. Find your Python 3.11+ path:\n'
printf '           which python3\n'
printf '           python3 --version\n'
printf '    3. Edit  .github/hooks/scripts/python-path.txt\n'
printf '       Replace the default "python3" with the full path if needed,\n'
printf '       e.g.  /opt/homebrew/bin/python3.11\n'
printf '    4. Restart VS Code (or reload the window: Cmd+Shift+P → Reload Window).\n'
printf '    5. The security gate is now active.\n'
printf '\n'
