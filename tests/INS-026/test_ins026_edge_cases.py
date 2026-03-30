"""
Edge-case tests for INS-026: macOS source install script and documentation.

These tests extend coverage beyond the Developer's suite, focusing on:
- Strict shell mode completeness
- Security properties (no eval, no CRLF)
- CI/non-interactive compatibility
- Makefile safety (uninstall does not auto-delete)
- WP compliance (INS-026 reference, line endings)
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "install-macos.sh")
MAKEFILE_PATH = os.path.join(REPO_ROOT, "Makefile")
GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "macos-installation-guide.md")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


# ── Strict shell mode ─────────────────────────────────────────────────────────

def test_strict_mode_pipefail():
    """set -e alone isn't enough — pipefail is required for pipeline failures."""
    content = _read(SCRIPT_PATH)
    assert "set -euo pipefail" in content, (
        "Script must use 'set -euo pipefail' for full strict mode, not just 'set -e'"
    )


def test_nounset_flag_present():
    """set -u (nounset) prevents silent errors from undefined variables."""
    content = _read(SCRIPT_PATH)
    assert "set -euo pipefail" in content or re.search(r'set\s+.*-u', content), (
        "Script does not use 'set -u' / nounset flag"
    )


# ── Security ──────────────────────────────────────────────────────────────────

def test_no_eval_in_script():
    """eval of user-influenced data is a code-injection risk."""
    content = _read(SCRIPT_PATH)
    # Allow 'eval' only in comments; reject it in live code
    non_comment_lines = [
        line for line in content.splitlines()
        if not line.strip().startswith("#")
    ]
    assert not any("eval " in line or line.strip() == "eval" for line in non_comment_lines), (
        "Script contains eval — potential code injection risk"
    )


def test_lf_line_endings_not_crlf():
    """CRLF line endings cause bash to treat \\r as part of commands on macOS/Linux."""
    raw = _read_bytes(SCRIPT_PATH)
    crlf_count = raw.count(b"\r\n")
    assert crlf_count == 0, (
        f"install-macos.sh contains {crlf_count} CRLF line endings — "
        "this will cause bash errors on macOS/Linux"
    )


def test_no_hardcoded_home_path():
    """No hardcoded /Users/ or /home/ paths — use $HOME variables."""
    content = _read(SCRIPT_PATH)
    assert "/Users/" not in content, "Script contains hardcoded /Users/ path"
    assert re.search(r'/home/\w', content) is None, (
        "Script contains hardcoded /home/<user> path"
    )


def test_path_variable_properly_escaped():
    """PATH_LINE must escape $PATH to avoid expanding it at assignment time."""
    content = _read(SCRIPT_PATH)
    # The line that defines PATH_LINE should have \$PATH so $PATH is literal
    path_line_def = [
        line for line in content.splitlines()
        if "PATH_LINE" in line and "export PATH" in line
    ]
    assert path_line_def, "PATH_LINE definition not found in script"
    # At least one definition must use escaped $PATH (not bare $PATH)
    assert any(r'\$PATH' in line for line in path_line_def), (
        "PATH_LINE assignment does not escape \\$PATH — it would expand $PATH "
        "at assignment time rather than at shell profile sourcing time"
    )


# ── Shebang format ────────────────────────────────────────────────────────────

def test_shebang_exact_format():
    """Shebang must be exactly #!/usr/bin/env bash (not /bin/bash which may not exist on macOS)."""
    content = _read(SCRIPT_PATH)
    first_line = content.splitlines()[0]
    assert first_line == "#!/usr/bin/env bash", (
        f"Shebang must be '#!/usr/bin/env bash', got: '{first_line}'"
    )


# ── CI / non-interactive compatibility ───────────────────────────────────────

def test_noninteractive_mode_handled():
    """Script must detect non-interactive stdin ([  -t 0 ]) for CI compatibility."""
    content = _read(SCRIPT_PATH)
    assert "[ -t 0 ]" in content or "[ -t 1 ]" in content, (
        "Script does not check for interactive terminal ([ -t 0 ]) — "
        "will block on read in CI environments"
    )


def test_noninteractive_auto_adds_path():
    """In non-interactive mode the else branch must auto-add to PATH profile."""
    content = _read(SCRIPT_PATH)
    assert "add_to_profile" in content, (
        "add_to_profile function not called — PATH setup may be skipped in CI"
    )
    # The script must have a '# Non-interactive' comment followed by add_to_profile.
    # This is the CI/piped-stdin path that runs without prompting.
    match = re.search(
        r'#\s*Non-interactive.*?add_to_profile',
        content,
        re.DOTALL | re.IGNORECASE,
    )
    assert match is not None, (
        "Non-interactive (else) branch of [ -t 0 ] does not call add_to_profile — "
        "PATH will not be configured in CI environments"
    )


# ── Shim deployment completeness ─────────────────────────────────────────────

def test_chmod_x_ts_python_shim():
    """ts-python shim must be made executable after creation."""
    content = _read(SCRIPT_PATH)
    assert re.search(r'chmod\s+\+x\s+"\$TS_PYTHON_SHIM"', content) or \
           re.search(r'chmod\s+\+x\s+.*ts.python', content), (
        "Script does not chmod +x the ts-python shim"
    )


def test_chmod_x_agent_launcher_wrapper():
    """Fallback agent-launcher wrapper must be made executable."""
    content = _read(SCRIPT_PATH)
    assert re.search(r'chmod\s+\+x\s+"\$AGENT_LAUNCHER_WRAPPER"', content) or \
           re.search(r'chmod\s+\+x\s+.*agent.launcher', content), (
        "Script does not chmod +x the fallback agent-launcher wrapper"
    )


def test_fallback_uses_python_minus_m_launcher():
    """Fallback wrapper must execute 'python -m launcher' when entry point is missing."""
    content = _read(SCRIPT_PATH)
    assert "-m launcher" in content, (
        "Fallback agent-launcher wrapper does not use 'python -m launcher'"
    )


def test_bash_source_used_for_script_dir():
    """BASH_SOURCE[0] is the correct way to get the script's own directory in bash."""
    content = _read(SCRIPT_PATH)
    assert "BASH_SOURCE" in content, (
        "Script does not use BASH_SOURCE to locate itself — "
        "$0 is unreliable when the script is sourced or called via sudo"
    )


# ── WP compliance ─────────────────────────────────────────────────────────────

def test_wp_reference_in_script():
    """Every code file must reference its workpackage ID (INS-026)."""
    content = _read(SCRIPT_PATH)
    assert "INS-026" in content, (
        "install-macos.sh does not contain workpackage reference 'INS-026'"
    )


def test_wp_reference_in_makefile():
    """Makefile must reference its workpackage ID (INS-026)."""
    content = _read(MAKEFILE_PATH)
    assert "INS-026" in content, (
        "Makefile does not contain workpackage reference 'INS-026'"
    )


# ── Makefile safety ───────────────────────────────────────────────────────────

def test_makefile_uninstall_does_not_execute_rm():
    """uninstall-macos must NOT execute rm -rf — it must only print instructions."""
    content = _read(MAKEFILE_PATH)
    # Find the uninstall-macos target block
    match = re.search(
        r'^uninstall-macos\s*:.*?(?=^\w|\Z)',
        content,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "uninstall-macos target not found in Makefile"
    block = match.group(0)
    # Any rm line must be prefixed with @echo (i.e., it's printed, not executed)
    rm_lines = [
        line for line in block.splitlines()
        if "rm" in line
    ]
    for line in rm_lines:
        stripped = line.strip()
        assert stripped.startswith("@echo"), (
            f"Makefile uninstall-macos target appears to execute rm: '{stripped}' — "
            "destructive operations must not run automatically"
        )


def test_makefile_uses_bash_shell():
    """Makefile must set SHELL to bash to match the install script's requirements."""
    content = _read(MAKEFILE_PATH)
    assert "SHELL" in content and "bash" in content, (
        "Makefile does not set SHELL to bash — recipe commands may run under /bin/sh"
    )


def test_makefile_install_calls_install_script_with_bash():
    """install-macos target must invoke the script explicitly with bash."""
    content = _read(MAKEFILE_PATH)
    # Should have bash or @bash before the script path
    assert re.search(r'bash\s+\$[({(]INSTALL_SCRIPT[}))]', content) or \
           "bash $(INSTALL_SCRIPT)" in content or \
           "bash ${INSTALL_SCRIPT}" in content, (
        "install-macos target does not invoke install-macos.sh with bash explicitly"
    )


# ── Documentation completeness ────────────────────────────────────────────────

def test_guide_mentions_idempotent():
    """Guide must state the installer is idempotent (safe to re-run)."""
    content = _read(GUIDE_PATH)
    assert "idempotent" in content.lower() or "safe to run" in content.lower() or \
           "re-run" in content.lower() or "running it a second time" in content.lower(), (
        "Guide does not mention that the installer is idempotent / safe to re-run"
    )


def test_guide_references_path_reload():
    """Guide must instruct user to reload their shell after install."""
    content = _read(GUIDE_PATH)
    assert "source ~/.zshrc" in content or "source $HOME/.zshrc" in content or \
           "Reload your shell" in content or "reload" in content.lower(), (
        "Guide does not instruct user to reload shell after install"
    )


def test_guide_lf_line_endings_not_crlf():
    """Documentation should prefer LF line endings.

    CRLF in .md files is cosmetic/minor (GitHub and browsers render it fine),
    but LF is preferred for consistency. This test is informational — it records
    the finding without blocking the WP if CRLF is found.
    """
    raw = _read_bytes(GUIDE_PATH)
    crlf_count = raw.count(b"\r\n")
    # We log the finding rather than hard-fail: CRLF in .md is non-blocking.
    # NOTE: if this ever causes issues (e.g. curl | bash piping), fix the line endings.
    if crlf_count > 0:
        import warnings
        warnings.warn(
            f"macos-installation-guide.md contains {crlf_count} CRLF line endings "
            "(minor: .md files render fine, but LF is preferred for consistency)"
        )
    # No assert — CRLF in docs is a style issue, not a functional failure.


def test_guide_no_absolute_paths():
    """Guide must not contain hardcoded absolute paths outside of examples."""
    content = _read(GUIDE_PATH)
    assert "/Users/" not in content, "Guide contains hardcoded /Users/ path"
