"""MNT-029 — Manifest integrity tests.

Verifies:
- generate_manifest.py --check exits 0 (manifest matches template files)
- MANIFEST.json has expected top-level keys
- MANIFEST.json files dict is non-empty
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"
GENERATE_SCRIPT = REPO_ROOT / "scripts" / "generate_manifest.py"


def test_manifest_check_exits_clean():
    """generate_manifest.py --check must exit 0 (manifest is up to date)."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"generate_manifest.py --check failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_manifest_has_expected_keys():
    """MANIFEST.json must contain files, _generated, and file_count."""
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("files", "_generated", "file_count"):
        assert key in data, f"MANIFEST.json missing key: {key}"
    assert len(data["files"]) > 0, "MANIFEST.json files dict must be non-empty"
