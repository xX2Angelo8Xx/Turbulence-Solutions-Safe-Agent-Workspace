"""
FIX-102: Tests for CI fix — regenerate MANIFEST.json and fix pycache leak.

Verifies:
1. .gitignore excludes __pycache__/ under templates/agent-workbench/
2. MANIFEST.json exists, is valid, and contains no __pycache__ entries
3. Regression baseline JSON is internally consistent (_count matches actual keys)
4. Git treats __pycache__ as ignored in templates/agent-workbench/
"""
import json
import subprocess
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "templates" / "agent-workbench"
TEMPLATES_HOOKS_SCRIPTS = TEMPLATES_ROOT / ".github" / "hooks" / "scripts"
MANIFEST_PATH = TEMPLATES_ROOT / "MANIFEST.json"
GITIGNORE_PATH = TEMPLATES_ROOT / ".gitignore"
BASELINE_PATH = REPO_ROOT / "tests" / "regression-baseline.json"


def test_gitignore_excludes_pycache():
    """templates/agent-workbench/.gitignore must contain a __pycache__/ exclusion rule."""
    assert GITIGNORE_PATH.exists(), f".gitignore not found at {GITIGNORE_PATH}"
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    assert "__pycache__/" in content, (
        "templates/agent-workbench/.gitignore must contain '__pycache__/' "
        "to exclude Python bytecode cache directories."
    )


def test_gitignore_excludes_pyc_files():
    """templates/agent-workbench/.gitignore must contain *.pyc exclusion rule."""
    assert GITIGNORE_PATH.exists(), f".gitignore not found at {GITIGNORE_PATH}"
    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    assert "*.pyc" in content, (
        "templates/agent-workbench/.gitignore must contain '*.pyc' "
        "to exclude Python bytecode files."
    )


def test_pycache_is_git_ignored():
    """Git must treat __pycache__ under templates/agent-workbench/ as ignored."""
    pycache_path = TEMPLATES_HOOKS_SCRIPTS / "__pycache__"
    # Create a dummy __pycache__ if it doesn't exist so git check-ignore can test it
    created = False
    if not pycache_path.exists():
        pycache_path.mkdir(parents=True)
        created = True
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(pycache_path)],
            cwd=str(REPO_ROOT),
            capture_output=True,
        )
        assert result.returncode == 0, (
            f"Git does NOT ignore {pycache_path}. "
            "Ensure '__pycache__/' is in templates/agent-workbench/.gitignore"
        )
    finally:
        if created and pycache_path.exists():
            import shutil
            shutil.rmtree(pycache_path)


def test_manifest_json_exists():
    """MANIFEST.json must exist in templates/agent-workbench/."""
    assert MANIFEST_PATH.exists(), f"MANIFEST.json not found at {MANIFEST_PATH}"


def test_manifest_json_is_valid():
    """MANIFEST.json must be valid JSON with at least one tracked file."""
    content = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert "files" in content, "MANIFEST.json must have a 'files' key"
    assert len(content["files"]) > 0, "MANIFEST.json must track at least one file"


def test_manifest_json_tracks_security_gate():
    """MANIFEST.json must track security_gate.py as a security-critical file."""
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    assert "security_gate.py" in manifest_text, (
        "MANIFEST.json must include security_gate.py in its tracked files"
    )


def test_manifest_json_has_no_pycache_entries():
    """MANIFEST.json must NOT contain any __pycache__ or .pyc entries."""
    content = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files_section = content.get("files", {})
    pycache_entries = [k for k in files_section if "__pycache__" in k or k.endswith(".pyc")]
    assert not pycache_entries, (
        f"MANIFEST.json must not contain __pycache__ or .pyc entries. "
        f"Found: {pycache_entries}"
    )


def test_manifest_json_excludes_runtime_files():
    """MANIFEST.json must NOT contain gitignored runtime files (audit.jsonl, .hook_state.json, copilot-otel.jsonl)."""
    content = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files_section = content.get("files", {})
    runtime_files = ["audit.jsonl", ".hook_state.json", "copilot-otel.jsonl"]
    found = [k for k in files_section if any(rf in k for rf in runtime_files)]
    assert not found, (
        f"MANIFEST.json must not track gitignored runtime files. "
        f"Found: {found}"
    )


def test_regression_baseline_count_matches_actual():
    """Regression baseline _count field must match actual number of known_failures keys."""
    assert BASELINE_PATH.exists(), f"regression-baseline.json not found at {BASELINE_PATH}"
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    declared_count = data.get("_count", -1)
    actual_count = len(data.get("known_failures", {}))
    assert declared_count == actual_count, (
        f"regression-baseline.json _count ({declared_count}) "
        f"does not match actual known_failures entries ({actual_count})"
    )
