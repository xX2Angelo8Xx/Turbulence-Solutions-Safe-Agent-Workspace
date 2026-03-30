# macOS Installation Guide — Agent Environment Launcher

## Overview

Agent Environment Launcher can be installed on macOS directly from the source
repository using Python and `pip`. This is the **primary and recommended method**
because it avoids Gatekeeper, code-signing, and notarization requirements
entirely — no `xattr` workarounds, no quarantine dialogs, no SIGKILL crashes.

A pre-built DMG is available as an **alternative** (see [DMG Install](#dmg-install-alternative))
but is blocked by macOS Gatekeeper until the project obtains an Apple
Developer ID certificate. Until then, use the source install below.

---

## Prerequisites

Before you begin, ensure the following are installed:

| Requirement | Minimum Version | How to Install |
|-------------|----------------|----------------|
| **Python** | 3.11 or newer | [python.org](https://www.python.org/downloads/) or `brew install python@3.11` |
| **git** | any recent | Xcode CLT: `xcode-select --install` |
| **Xcode Command Line Tools** | latest | `xcode-select --install` |

### Install Xcode Command Line Tools

```bash
xcode-select --install
```

A dialog will appear; click **Install**. This also installs `git`.

### Verify Python 3.11+

```bash
python3 --version
```

If the version shown is below 3.11, install a newer Python:

```bash
# Via Homebrew (recommended)
brew install python@3.11

# Or download the macOS installer from:
# https://www.python.org/downloads/
```

---

## Quick Start (Source Install)

```bash
# 1. Clone the repository
git clone https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
cd Turbulence-Solutions-Safe-Agent-Workspace

# 2. Run the installer
make install-macos
# or equivalently:
# bash scripts/install-macos.sh

# 3. Reload your shell (the installer will tell you which file)
source ~/.zshrc   # or ~/.bashrc

# 4. Launch
agent-launcher
```

The entire process takes about 1–2 minutes on a typical internet connection.

---

## What the Install Script Does

`scripts/install-macos.sh` performs these steps automatically:

1. **Checks Python 3.11+** is available on the system.
2. **Checks git** is installed.
3. **Creates a virtualenv** at `~/.local/share/TurbulenceSolutions/venv/`.
4. **Installs the package** via `pip install .` from the repository root.
5. **Deploys the `ts-python` shim** at
   `~/.local/share/TurbulenceSolutions/bin/ts-python` — a wrapper that points
   to the virtualenv Python (not a bundled Python.framework).
6. **Writes `python-path.txt`** with the absolute path to the venv Python.
7. **Creates an `agent-launcher` command** in
   `~/.local/share/TurbulenceSolutions/bin/` pointing to the venv entry point.
8. **Adds the bin directory to PATH** in your shell profile (`~/.zshrc` or
   `~/.bashrc`), guarded against duplicate entries.

The script is **idempotent** — running it a second time is safe.

---

## Step-by-Step Instructions

### Step 1 — Clone the repository

```bash
git clone https://github.com/xX2Angelo8Xx/Turbulence-Solutions-Safe-Agent-Workspace.git
cd Turbulence-Solutions-Safe-Agent-Workspace
```

### Step 2 — Run the installer

```bash
make install-macos
```

You will see progress output. If prompted about adding to PATH, press **Enter**
to accept (recommended).

### Step 3 — Reload your shell

```bash
source ~/.zshrc    # if using zsh (default on macOS 10.15+)
# or
source ~/.bashrc   # if using bash
```

### Step 4 — Verify the installation

```bash
agent-launcher --version
ts-python --version
```

Both commands should print the version number without errors.

### Step 5 — Launch

```bash
agent-launcher
```

The GUI will open. No quarantine dialogs, no code-signing prompts.

---

## Updating

Pull the latest changes and reinstall:

```bash
cd Turbulence-Solutions-Safe-Agent-Workspace
make update-macos
```

---

## Uninstalling

Run:

```bash
make uninstall-macos
```

This prints the exact commands to remove the installation. It does **not**
delete anything automatically — copy and run the printed commands yourself
to avoid accidental data loss.

---

## Troubleshooting

### `command not found: agent-launcher`

The bin directory is not yet in your PATH. Either:

1. Reload your shell: `source ~/.zshrc`
2. Or run the launcher directly:
   ```bash
   ~/.local/share/TurbulenceSolutions/venv/bin/agent-launcher
   ```
3. Or re-run the installer; it will add the PATH entry if missing.

### `python3: command not found` / Python version too old

Install Python 3.11 or newer:

```bash
# Homebrew
brew install python@3.11

# Or download from https://www.python.org/downloads/
```

Then re-run `make install-macos`.

### `xcode-select: error: command line tools are not installed`

Install Xcode Command Line Tools:

```bash
xcode-select --install
```

### `git: command not found`

git is bundled with Xcode CLT. Run `xcode-select --install`.

### `pip install` fails with permission error

The install goes into `~/.local/` (your home directory) — no `sudo` is needed.
If you see permission errors, check that `~/.local/` is writable:

```bash
ls -la ~/.local/
```

### App closes immediately / crashes on launch

Run from Terminal to see the error output:

```bash
~/.local/share/TurbulenceSolutions/venv/bin/agent-launcher
```

Capture the output and report it to the development team.

### Checking the installation

```bash
# Show installed venv Python path
cat ~/.local/share/TurbulenceSolutions/python-path.txt

# Confirm package is installed
~/.local/share/TurbulenceSolutions/venv/bin/pip show agent-environment-launcher

# Confirm entry point
ls -la ~/.local/share/TurbulenceSolutions/bin/
```

---

## Architecture Notes

**Why source install instead of DMG?**

The pre-built DMG uses PyInstaller to bundle Python.framework into the app.
This causes three known issues on macOS:

- **BUG-147** — SIGKILL crash: macOS kills the app due to memory pressure from
  the embedded framework.
- **BUG-148** — Code signature corruption: PyInstaller's ad-hoc signing breaks
  when moved to `~/Applications/` or network drives.
- **BUG-149** — Gatekeeper blocks the app without an Apple Developer ID cert.

The source install uses the system/Homebrew Python directly inside a
standard virtualenv — no embedded framework, no signature issues, no
Gatekeeper friction.

---

## DMG Install (Alternative)

> **Status:** Pending resolution of BUG-148 (code signature corruption) and
> BUG-149 (Gatekeeper). The DMG is available but not recommended until the
> project obtains an Apple Developer ID certificate.

If you still want to use the DMG:

### Step 1: Download the DMG

Download the latest `AgentEnvironmentLauncher-x.x.x-arm64.dmg` from the
GitHub Releases page.

### Step 2: Mount and copy

Double-click the `.dmg` file. Drag `AgentEnvironmentLauncher.app` to your
**Applications** folder.

### Step 3: Remove the quarantine flag

```bash
xattr -cr /Applications/AgentEnvironmentLauncher.app
```

### Step 4: Launch

Double-click `AgentEnvironmentLauncher.app`.

> **Note:** Even after removing quarantine, you may encounter SIGKILL crashes
> (BUG-147) or code signing errors (BUG-148). Use the source install to avoid
> these issues entirely.
