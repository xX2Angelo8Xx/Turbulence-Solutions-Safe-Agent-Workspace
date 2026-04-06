"""Tests for FIX-122: Move MANIFEST.json inside .github/hooks/scripts/.

Regression and unit tests that verify:
- MANIFEST.json exists at the new location (.github/hooks/scripts/) in both templates.
- MANIFEST.json does NOT exist at the template root in either template.
- generate_manifest.py writes to the new location.
- generate_manifest.py --check passes for both templates.
- workspace_upgrader.py _MANIFEST_NAME points to the new location.
- verify_parity.py _MANIFEST_PATH points to the new location.
- CI workflow files reference the new manifest path.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_WORKBENCH = REPO_ROOT / "templates" / "agent-workbench"
CLEAN_WORKSPACE = REPO_ROOT / "templates" / "clean-workspace"

_NEW_MANIFEST_SUBPATH = Path(".github") / "hooks" / "scripts" / "MANIFEST.json"


# ---------------------------------------------------------------------------
# Regression: MANIFEST.json at new location
# ---------------------------------------------------------------------------

def test_manifest_exists_at_new_location_agent_workbench():
    """MANIFEST.json must exist at .github/hooks/scripts/ in agent-workbench."""
    manifest = AGENT_WORKBENCH / _NEW_MANIFEST_SUBPATH
    assert manifest.is_file(), (
        f"MANIFEST.json not found at new location: {manifest}"
    )


def test_manifest_exists_at_new_location_clean_workspace():
    """MANIFEST.json must exist at .github/hooks/scripts/ in clean-workspace."""
    manifest = CLEAN_WORKSPACE / _NEW_MANIFEST_SUBPATH
    assert manifest.is_file(), (
        f"MANIFEST.json not found at new location: {manifest}"
    )


# ---------------------------------------------------------------------------
# Regression: MANIFEST.json NOT at template root
# ---------------------------------------------------------------------------

def test_manifest_not_at_root_agent_workbench():
    """MANIFEST.json must NOT exist at the agent-workbench template root (BUG-207)."""
    old_path = AGENT_WORKBENCH / "MANIFEST.json"
    assert not old_path.exists(), (
        f"MANIFEST.json still present at template root (BUG-207): {old_path}"
    )


def test_manifest_not_at_root_clean_workspace():
    """MANIFEST.json must NOT exist at the clean-workspace template root (BUG-207)."""
    old_path = CLEAN_WORKSPACE / "MANIFEST.json"
    assert not old_path.exists(), (
        f"MANIFEST.json still present at template root (BUG-207): {old_path}"
    )


# ---------------------------------------------------------------------------
# generate_manifest.py: writes to new location and --check passes
# ---------------------------------------------------------------------------

def test_generate_manifest_check_agent_workbench():
    """generate_manifest.py --check must exit 0 for agent-workbench."""
    result = subprocess.run(
        [sys.executable, "scripts/generate_manifest.py", "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"generate_manifest.py --check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_generate_manifest_check_clean_workspace():
    """generate_manifest.py --check --template clean-workspace must exit 0."""
    result = subprocess.run(
        [sys.executable, "scripts/generate_manifest.py", "--check", "--template", "clean-workspace"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"generate_manifest.py --check (clean-workspace) failed:\n{result.stdout}\n{result.stderr}"
    )


def test_generate_manifest_new_path_constant():
    """generate_manifest.py must reference the new manifest subpath constant."""
    script = (REPO_ROOT / "scripts" / "generate_manifest.py").read_text(encoding="utf-8")
    assert ".github/hooks/scripts/MANIFEST.json" in script or "_MANIFEST_SUBPATH" in script, (
        "generate_manifest.py must contain the new manifest path"
    )


def test_manifest_not_tracked_in_itself():
    """MANIFEST.json must not track itself in its 'files' section."""
    manifest_path = AGENT_WORKBENCH / _NEW_MANIFEST_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = data.get("files", {})
    assert ".github/hooks/scripts/MANIFEST.json" not in files, (
        "MANIFEST.json must not track itself"
    )


# ---------------------------------------------------------------------------
# workspace_upgrader.py: _MANIFEST_NAME points to new location
# ---------------------------------------------------------------------------

def test_workspace_upgrader_manifest_name():
    """workspace_upgrader.py _MANIFEST_NAME must point to new hooks/scripts location."""
    upgrader = (REPO_ROOT / "src" / "launcher" / "core" / "workspace_upgrader.py").read_text(encoding="utf-8")
    assert ".github/hooks/scripts/MANIFEST.json" in upgrader or (
        '_MANIFEST_NAME = Path(".github") / "hooks" / "scripts" / "MANIFEST.json"' in upgrader
    ), "workspace_upgrader.py must use new MANIFEST.json path"
    assert '_MANIFEST_NAME = "MANIFEST.json"' not in upgrader, (
        "workspace_upgrader.py must not use old root MANIFEST.json path"
    )


# ---------------------------------------------------------------------------
# verify_parity.py: _MANIFEST_PATH points to new location
# ---------------------------------------------------------------------------

def test_verify_parity_manifest_path():
    """verify_parity.py _MANIFEST_PATH must point to .github/hooks/scripts/MANIFEST.json."""
    parity = (REPO_ROOT / "scripts" / "verify_parity.py").read_text(encoding="utf-8")
    # The path is constructed with Path divisions, so look for the parts
    assert '"hooks"' in parity and '"scripts"' in parity and '"MANIFEST.json"' in parity, (
        "verify_parity.py must reference the new MANIFEST.json path components"
    )
    # Must not use the old root path pattern
    assert '"agent-workbench" / "MANIFEST.json"' not in parity, (
        "verify_parity.py must not reference old root MANIFEST.json path"
    )


# ---------------------------------------------------------------------------
# CI workflows: reference new manifest path
# ---------------------------------------------------------------------------

def test_test_yml_manifest_path():
    """.github/workflows/test.yml must reference the new manifest path."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "templates/agent-workbench/.github/hooks/scripts/MANIFEST.json" in workflow, (
        "test.yml must use new MANIFEST.json path"
    )
    assert 'Path("templates/agent-workbench/MANIFEST.json")' not in workflow, (
        "test.yml must not use old root MANIFEST.json path"
    )


def test_staging_test_yml_manifest_path():
    """.github/workflows/staging-test.yml must reference the new manifest path."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "staging-test.yml").read_text(encoding="utf-8")
    assert "templates/agent-workbench/.github/hooks/scripts/MANIFEST.json" in workflow, (
        "staging-test.yml must use new MANIFEST.json path"
    )
    assert 'Path("templates/agent-workbench/MANIFEST.json")' not in workflow, (
        "staging-test.yml must not use old root MANIFEST.json path"
    )
