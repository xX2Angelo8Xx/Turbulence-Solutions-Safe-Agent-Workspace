#!/usr/bin/env bash
# install-macos.sh — macOS source install for Agent Environment Launcher
# INS-026
#
# Usage:
#   bash scripts/install-macos.sh
#
# What this script does:
#   1. Checks Python 3.11+ is available
#   2. Checks git is available
#   3. Creates a virtualenv at ~/.local/share/TurbulenceSolutions/venv/
#   4. Installs the package via pip install .
#   5. Deploys the ts-python shim pointing to the venv Python
#   6. Writes python-path.txt with the venv Python path
#   7. Creates an agent-launcher wrapper in the bin directory
#   8. Offers to add the bin directory to PATH via shell profile
#
# Idempotent: safe to run multiple times. Existing venv is reused.
# Supports Apple Silicon (arm64) and Intel (x86_64).

set -euo pipefail

# ── Constants ─────────────────────────────────────────────────────────────────
INSTALL_BASE="$HOME/.local/share/TurbulenceSolutions"
VENV_DIR="$INSTALL_BASE/venv"
BIN_DIR="$INSTALL_BASE/bin"
PYTHON_PATH_FILE="$INSTALL_BASE/python-path.txt"
TS_PYTHON_SHIM="$BIN_DIR/ts-python"
AGENT_LAUNCHER_WRAPPER="$BIN_DIR/agent-launcher"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
success() { printf '\033[0;32m[OK]\033[0m    %s\n' "$*"; }
error()   { printf '\033[0;31m[ERROR]\033[0m %s\n' "$*" >&2; }
warn()    { printf '\033[0;33m[WARN]\033[0m  %s\n' "$*"; }

# ── Step 1: Locate Python 3.11+ ───────────────────────────────────────────────
find_python() {
    local candidates=(python3.13 python3.12 python3.11 python3 python)
    local py

    for candidate in "${candidates[@]}"; do
        if command -v "$candidate" >/dev/null 2>&1; then
            py="$(command -v "$candidate")"
            local version
            version="$("$py" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
            local major minor
            major="${version%%.*}"
            minor="${version#*.}"
            if [ "${major:-0}" -ge "$MIN_PYTHON_MAJOR" ] && \
               [ "${minor:-0}" -ge "$MIN_PYTHON_MINOR" ]; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

info "Checking Python $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR+..."
if ! PYTHON_BIN="$(find_python)"; then
    error "Python $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR or newer not found."
    error "Install it via https://www.python.org/downloads/ or Homebrew:"
    error "  brew install python@3.11"
    exit 1
fi
success "Found Python: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

# ── Step 2: Check git ─────────────────────────────────────────────────────────
info "Checking git..."
if ! command -v git >/dev/null 2>&1; then
    error "git is not installed."
    error "Install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi
success "Found git: $(git --version)"

# ── Step 3: Determine repo root ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$REPO_ROOT/pyproject.toml" ]; then
    error "pyproject.toml not found at $REPO_ROOT"
    error "Run this script from inside the cloned repository."
    exit 1
fi
info "Repository root: $REPO_ROOT"

# ── Step 4: Create venv (idempotent) ──────────────────────────────────────────
info "Setting up virtualenv at $VENV_DIR..."
mkdir -p "$INSTALL_BASE"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    success "Virtualenv created."
else
    warn "Virtualenv already exists — reusing."
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── Step 5: Install the package ───────────────────────────────────────────────
info "Installing package from $REPO_ROOT..."
"$VENV_PIP" install --upgrade pip --quiet
"$VENV_PIP" install "$REPO_ROOT" --quiet
success "Package installed."

# ── Step 6: Create bin directory and deploy shims ─────────────────────────────
mkdir -p "$BIN_DIR"

# Write python-path.txt
printf '%s\n' "$VENV_PYTHON" > "$PYTHON_PATH_FILE"
success "Wrote python-path.txt: $PYTHON_PATH_FILE"

# ts-python shim — delegates to the venv Python
cat > "$TS_PYTHON_SHIM" <<EOF
#!/usr/bin/env bash
# ts-python — points to the TurbulenceSolutions virtualenv Python
# Deployed by install-macos.sh (INS-026)
exec "$VENV_PYTHON" "\$@"
EOF
chmod +x "$TS_PYTHON_SHIM"
success "ts-python shim deployed: $TS_PYTHON_SHIM"

# agent-launcher wrapper
VENV_LAUNCHER="$VENV_DIR/bin/agent-launcher"
if [ -f "$VENV_LAUNCHER" ]; then
    # Prefer a symlink if the entry point exists
    ln -sf "$VENV_LAUNCHER" "$AGENT_LAUNCHER_WRAPPER"
    success "agent-launcher symlink: $AGENT_LAUNCHER_WRAPPER -> $VENV_LAUNCHER"
else
    # Fallback wrapper using python -m launcher
    cat > "$AGENT_LAUNCHER_WRAPPER" <<EOF
#!/usr/bin/env bash
# agent-launcher — falls back to python -m launcher when entry point is absent
exec "$VENV_PYTHON" -m launcher "\$@"
EOF
    chmod +x "$AGENT_LAUNCHER_WRAPPER"
    warn "entry point not found in venv; wrote fallback wrapper: $AGENT_LAUNCHER_WRAPPER"
fi

# ── Step 7: Offer to add bin dir to PATH ─────────────────────────────────────
PATH_LINE="export PATH=\"$BIN_DIR:\$PATH\""

add_to_profile() {
    local profile="$1"
    if [ -f "$profile" ] && grep -qF "$BIN_DIR" "$profile" 2>/dev/null; then
        warn "$BIN_DIR already in $profile — skipping."
        return
    fi
    printf '\n# Added by TurbulenceSolutions install-macos.sh\n%s\n' "$PATH_LINE" >> "$profile"
    success "Added PATH entry to $profile"
}

# Detect default shell profile
if [ -n "${BASH_VERSION:-}" ]; then
    DEFAULT_PROFILE="$HOME/.bashrc"
elif [ -n "${ZSH_VERSION:-}" ]; then
    DEFAULT_PROFILE="$HOME/.zshrc"
else
    # Fallback: prefer zsh (default on macOS 10.15+), then bash
    if [ -f "$HOME/.zshrc" ]; then
        DEFAULT_PROFILE="$HOME/.zshrc"
    else
        DEFAULT_PROFILE="$HOME/.bashrc"
    fi
fi

# Only prompt when running interactively
if [ -t 0 ]; then
    printf '\nAdd %s to PATH in %s? [Y/n] ' "$BIN_DIR" "$DEFAULT_PROFILE"
    read -r answer
    case "${answer:-Y}" in
        [Yy]*|"") add_to_profile "$DEFAULT_PROFILE" ;;
        *)         info "Skipped PATH setup. Add manually: $PATH_LINE" ;;
    esac
else
    # Non-interactive (CI, piped): add automatically
    add_to_profile "$DEFAULT_PROFILE"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
printf '\n'
success "Installation complete!"
printf '\n'
info "Next steps:"
info "  1. Reload your shell:  source %s" "$DEFAULT_PROFILE"
info "  2. Launch the app:     agent-launcher"
info "  3. Or run directly:    %s" "$VENV_LAUNCHER"
printf '\n'
