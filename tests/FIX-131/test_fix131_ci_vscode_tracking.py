"""Regression tests for FIX-131: CI clean-workspace .vscode tracking.

Verifies:
1. templates/clean-workspace/.vscode/settings.json is tracked in git so CI checkout
   includes the file and DOC-063/DOC-064/FIX-122 tests pass.
2. pytest.internal is present in the regression baseline so it does not
   block CI as an unrecognised failure.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = "templates/clean-workspace/.vscode/settings.json"
BASELINE_PATH = REPO_ROOT / "tests" / "regression-baseline.json"


def test_clean_workspace_vscode_settings_is_git_tracked():
    """settings.json must be tracked by git (not just present on disk)."""
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", SETTINGS_PATH],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"templates/clean-workspace/.vscode/settings.json is NOT tracked in git. "
        f"CI checkout will not include the file, causing DOC-063/DOC-064/FIX-122 "
        f"test failures. Run: git add -f {SETTINGS_PATH}"
    )


def test_clean_workspace_vscode_settings_file_exists():
    """settings.json must exist on disk."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    assert settings_file.exists(), (
        f"templates/clean-workspace/.vscode/settings.json does not exist at {settings_file}"
    )


def test_clean_workspace_vscode_settings_is_valid_json():
    """settings.json must be valid JSON."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    content = settings_file.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict), "settings.json must be a JSON object"


def test_clean_workspace_vscode_settings_excludes_vscode():
    """settings.json must exclude .vscode in files.exclude."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    files_exclude = data.get("files.exclude", {})
    assert ".vscode" in files_exclude, (
        "settings.json files.exclude must contain .vscode entry"
    )


def test_clean_workspace_vscode_settings_excludes_github():
    """settings.json must exclude .github in files.exclude."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    files_exclude = data.get("files.exclude", {})
    assert ".github" in files_exclude, (
        "settings.json files.exclude must contain .github entry"
    )


def test_pytest_internal_in_regression_baseline():
    """pytest.internal must be in the regression baseline to prevent CI blocking."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    known_failures = baseline.get("known_failures", {})
    assert "pytest.internal" in known_failures, (
        "pytest.internal is not in regression-baseline.json. "
        "This CI-only collection artifact must be listed as a known failure "
        "so it does not block CI as a new regression."
    )


def test_regression_baseline_count_matches_entries():
    """_count in regression baseline must match actual number of known_failures entries."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    declared_count = baseline.get("_count", 0)
    actual_count = len(baseline.get("known_failures", {}))
    assert declared_count == actual_count, (
        f"regression-baseline.json _count={declared_count} does not match "
        f"actual number of known_failures entries ({actual_count}). "
        f"Update _count to fix."
    )


# ---------------------------------------------------------------------------
# Tester edge-case tests (added by Tester Agent)
# ---------------------------------------------------------------------------

MANIFEST_PATH = REPO_ROOT / "templates" / "clean-workspace" / ".github" / "hooks" / "scripts" / "MANIFEST.json"


def test_gitignore_still_excludes_vscode():
    """Root .gitignore must still exclude .vscode/ (force-add approach, not gitignore removal)."""
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore must exist at repo root"
    content = gitignore.read_text(encoding="utf-8")
    assert ".vscode" in content, (
        "Root .gitignore no longer excludes .vscode — the fix should use "
        "'git add -f' (force-track), never modify .gitignore"
    )


def test_clean_workspace_settings_security_critical_in_manifest():
    """settings.json must be marked security_critical=True in MANIFEST.json."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = manifest.get("files", {}).get(".vscode/settings.json")
    assert entry is not None, ".vscode/settings.json is missing from MANIFEST.json"
    assert entry.get("security_critical") is True, (
        ".vscode/settings.json must be marked security_critical=True in MANIFEST.json"
    )


def test_clean_workspace_settings_sha256_matches_disk():
    """SHA256 in MANIFEST.json must match the actual settings.json on disk."""
    import hashlib
    settings_file = REPO_ROOT / SETTINGS_PATH
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_hash = manifest.get("files", {}).get(".vscode/settings.json", {}).get("sha256", "")
    actual_hash = hashlib.sha256(settings_file.read_bytes()).hexdigest()
    assert manifest_hash == actual_hash, (
        f"MANIFEST.json SHA256 ({manifest_hash!r}) does not match "
        f"actual settings.json hash ({actual_hash!r}). Run: python scripts/generate_manifest.py --template clean-workspace"
    )


def test_clean_workspace_settings_terminal_sandbox_enabled():
    """settings.json must have terminal sandbox enabled (security requirement)."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    data = json.loads(settings_file.read_text(encoding="utf-8"))
    sandbox = data.get("chat.tools.terminal.sandbox.enabled")
    assert sandbox is True, (
        "settings.json must set chat.tools.terminal.sandbox.enabled=true"
    )


def test_clean_workspace_settings_no_plain_text_secrets():
    """settings.json must not contain obvious secret patterns (keys, tokens, passwords)."""
    settings_file = REPO_ROOT / SETTINGS_PATH
    content = settings_file.read_text(encoding="utf-8").lower()
    forbidden_patterns = ["password", "api_key", "apikey", "secret", "token", "Bearer "]
    for pattern in forbidden_patterns:
        assert pattern.lower() not in content, (
            f"settings.json appears to contain a secret/credential pattern: '{pattern}'"
        )
