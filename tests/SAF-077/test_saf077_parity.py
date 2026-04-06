"""Tests for SAF-077: Install vs Update Parity Testing.

Verifies that:
- verify_parity.py loads MANIFEST.json and identifies security-critical files.
- SHA-256 helpers produce correct and consistent digests.
- compare_workspaces() correctly reports matches and mismatches.
- The full parity check passes when the template is self-consistent.
- Mismatch detection cannot be bypassed (security tests).
- CLI exits 0 on parity and 1 on mismatch.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
MANIFEST_PATH = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "MANIFEST.json"

# Ensure scripts/ is importable
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify_parity as vp  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_file(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------

def test_manifest_loads_without_error():
    """load_manifest() must not raise on the real MANIFEST.json."""
    manifest = vp.load_manifest()
    assert isinstance(manifest, dict)


def test_manifest_has_files_section():
    """Loaded manifest must have a 'files' key."""
    manifest = vp.load_manifest()
    assert "files" in manifest, "MANIFEST.json missing 'files' section"


def test_load_manifest_raises_on_missing_file(tmp_path):
    """load_manifest() must raise FileNotFoundError when manifest is absent."""
    with pytest.raises(FileNotFoundError):
        vp.load_manifest(tmp_path / "nonexistent.json")


def test_load_manifest_raises_on_invalid_json(tmp_path):
    """load_manifest() must raise ValueError when manifest is not valid JSON."""
    bad_manifest = tmp_path / "MANIFEST.json"
    bad_manifest.write_text("{not: valid json}", encoding="utf-8")
    with pytest.raises(ValueError, match="Failed to parse"):
        vp.load_manifest(bad_manifest)


# ---------------------------------------------------------------------------
# get_security_critical_files
# ---------------------------------------------------------------------------

def test_get_security_critical_files_returns_list():
    """get_security_critical_files() must return a list."""
    result = vp.get_security_critical_files(vp.load_manifest())
    assert isinstance(result, list)


def test_get_security_critical_files_not_empty():
    """There must be at least one security-critical file in the real manifest."""
    result = vp.get_security_critical_files(vp.load_manifest())
    assert len(result) > 0, "Expected at least one security-critical file in MANIFEST"


def test_get_security_critical_files_only_marked_true():
    """Every returned path must have security_critical=True in the manifest."""
    manifest = vp.load_manifest()
    result = vp.get_security_critical_files(manifest)
    for rel_path in result:
        entry = manifest["files"][rel_path]
        assert entry.get("security_critical") is True, (
            f"{rel_path} was returned but security_critical is not True"
        )


def test_get_security_critical_files_excludes_non_critical():
    """Files with security_critical=False must NOT appear in the result."""
    manifest = {
        "files": {
            "secure.py": {"sha256": "aaa", "security_critical": True},
            "readme.md": {"sha256": "bbb", "security_critical": False},
        }
    }
    result = vp.get_security_critical_files(manifest)
    assert "secure.py" in result
    assert "readme.md" not in result


def test_get_security_critical_files_empty_manifest():
    """An empty files section returns an empty list."""
    assert vp.get_security_critical_files({"files": {}}) == []


# ---------------------------------------------------------------------------
# _sha256
# ---------------------------------------------------------------------------

def test_sha256_consistent(tmp_path):
    """Same file content produces the same digest on each call."""
    f = _write_file(tmp_path / "a.txt", b"hello world")
    assert vp._sha256(f) == vp._sha256(f)


def test_sha256_known_value(tmp_path):
    """Empty file must produce the known SHA-256 of empty string."""
    f = _write_file(tmp_path / "empty.txt", b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert vp._sha256(f) == expected


def test_sha256_different_for_different_content(tmp_path):
    """Different file contents must produce different digests."""
    f1 = _write_file(tmp_path / "a.bin", b"aaa")
    f2 = _write_file(tmp_path / "b.bin", b"bbb")
    assert vp._sha256(f1) != vp._sha256(f2)


def test_sha256_single_byte_difference(tmp_path):
    """A 1-byte change must produce a different digest."""
    f1 = _write_file(tmp_path / "v1.bin", b"security_gate_v1")
    f2 = _write_file(tmp_path / "v2.bin", b"security_gate_v2")
    assert vp._sha256(f1) != vp._sha256(f2)


# ---------------------------------------------------------------------------
# compare_workspaces
# ---------------------------------------------------------------------------

def test_compare_workspaces_all_match(tmp_path):
    """compare_workspaces() returns empty list when files are byte-identical."""
    content = b"security content"
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    _write_file(fresh / ".github" / "hooks" / "scripts" / "security_gate.py", content)
    _write_file(upgraded / ".github" / "hooks" / "scripts" / "security_gate.py", content)

    security_files = [".github/hooks/scripts/security_gate.py"]
    mismatches = vp.compare_workspaces(fresh, upgraded, security_files)
    assert mismatches == [], f"Expected no mismatches, got: {mismatches}"


def test_compare_workspaces_detects_mismatch(tmp_path):
    """compare_workspaces() must detect when files have different content."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    _write_file(fresh / ".github" / "hooks" / "scripts" / "security_gate.py", b"version_a")
    _write_file(upgraded / ".github" / "hooks" / "scripts" / "security_gate.py", b"version_b")

    security_files = [".github/hooks/scripts/security_gate.py"]
    mismatches = vp.compare_workspaces(fresh, upgraded, security_files)
    assert len(mismatches) == 1
    assert "HASH MISMATCH" in mismatches[0]


def test_compare_workspaces_missing_in_fresh(tmp_path):
    """Missing file in fresh workspace must be reported as a mismatch."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    # Only create the file in the upgraded workspace
    _write_file(upgraded / ".github" / "hooks" / "scripts" / "security_gate.py", b"data")

    security_files = [".github/hooks/scripts/security_gate.py"]
    mismatches = vp.compare_workspaces(fresh, upgraded, security_files)
    assert any("MISSING in fresh" in m for m in mismatches), mismatches


def test_compare_workspaces_missing_in_upgraded(tmp_path):
    """Missing file in upgraded workspace must be reported as a mismatch."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    _write_file(fresh / ".github" / "hooks" / "scripts" / "security_gate.py", b"data")

    security_files = [".github/hooks/scripts/security_gate.py"]
    mismatches = vp.compare_workspaces(fresh, upgraded, security_files)
    assert any("MISSING in upgraded" in m for m in mismatches), mismatches


def test_compare_workspaces_both_absent_no_mismatch(tmp_path):
    """A file absent from BOTH workspaces is not a parity mismatch."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"
    fresh.mkdir()
    upgraded.mkdir()

    security_files = [".github/hooks/scripts/security_gate.py"]
    mismatches = vp.compare_workspaces(fresh, upgraded, security_files)
    assert mismatches == [], "Both-absent should not count as mismatch"


def test_compare_workspaces_multiple_files(tmp_path):
    """compare_workspaces() checks all listed files and aggregates results."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    # file_a matches, file_b mismatches
    _write_file(fresh / "file_a.py", b"same")
    _write_file(upgraded / "file_a.py", b"same")
    _write_file(fresh / "file_b.py", b"old")
    _write_file(upgraded / "file_b.py", b"new")

    mismatches = vp.compare_workspaces(fresh, upgraded, ["file_a.py", "file_b.py"])
    assert len(mismatches) == 1
    assert "file_b.py" in mismatches[0]


# ---------------------------------------------------------------------------
# verify_parity — integration test (real workspaces from template)
# ---------------------------------------------------------------------------

def test_verify_parity_passes():
    """Integration: full parity check against the real template must return True.

    This test creates two real workspaces in a temporary directory and verifies
    that every security-critical file is byte-identical after a fresh install
    vs. an upgrade from a corrupted (simulated-old) workspace.
    """
    # Allow real filesystem operations; the conftest subprocess guards
    # will still block any VS Code spawning attempts.
    result = vp.verify_parity(verbose=False)
    assert result is True, (
        "Parity check failed — fresh and upgraded workspaces have different "
        "security-critical files. Run scripts/verify_parity.py --verbose for details."
    )


# ---------------------------------------------------------------------------
# verify_parity — unit tests with mocks
# ---------------------------------------------------------------------------

def test_verify_parity_returns_false_on_mismatch(tmp_path):
    """verify_parity() must return False when compare_workspaces finds a mismatch."""
    fake_manifest = {
        "files": {
            "file.py": {"sha256": "abc", "security_critical": True}
        }
    }
    with (
        patch.object(vp, "load_manifest", return_value=fake_manifest),
        patch.object(vp, "create_fresh_workspace", return_value=tmp_path / "fresh"),
        patch.object(vp, "create_upgraded_workspace", return_value=tmp_path / "upgraded"),
        patch.object(vp, "compare_workspaces", return_value=["HASH MISMATCH: file.py"]),
    ):
        result = vp.verify_parity()
    assert result is False


def test_verify_parity_returns_true_on_empty_mismatches(tmp_path):
    """verify_parity() must return True when compare_workspaces returns empty list."""
    fake_manifest = {
        "files": {
            "file.py": {"sha256": "abc", "security_critical": True}
        }
    }
    with (
        patch.object(vp, "load_manifest", return_value=fake_manifest),
        patch.object(vp, "create_fresh_workspace", return_value=tmp_path / "fresh"),
        patch.object(vp, "create_upgraded_workspace", return_value=tmp_path / "upgraded"),
        patch.object(vp, "compare_workspaces", return_value=[]),
    ):
        result = vp.verify_parity()
    assert result is True


def test_verify_parity_no_security_files_returns_true():
    """verify_parity() must return True when manifest has no security-critical files."""
    fake_manifest = {"files": {"readme.md": {"sha256": "abc", "security_critical": False}}}
    with patch.object(vp, "load_manifest", return_value=fake_manifest):
        result = vp.verify_parity()
    assert result is True


# ---------------------------------------------------------------------------
# CLI exit-code tests
# ---------------------------------------------------------------------------

def test_cli_exits_zero_on_parity():
    """CLI must exit with code 0 when parity check passes."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "verify_parity.py"), "--verbose"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 but got {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "PASSED" in result.stdout


def test_cli_exits_one_on_missing_manifest(tmp_path):
    """CLI must exit with code 1 and print ERROR when load_manifest() fails."""
    # Write a helper script that patches load_manifest to raise FileNotFoundError
    # before calling main(). This correctly exercises the error-handling path without
    # relying on module-level constant patching (which cannot affect default args).
    script = tmp_path / "run_error_test.py"
    script.write_text(
        f"import sys\n"
        f"sys.path.insert(0, r'{SCRIPTS_DIR!s}')\n"
        f"import verify_parity as vp\n"
        f"from unittest.mock import patch\n"
        f"with patch.object(vp, 'load_manifest', side_effect=FileNotFoundError('no manifest')):\n"
        f"    vp.main()\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "ERROR" in result.stderr


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------

def test_sentinel_content_is_detected_as_mismatch(tmp_path):
    """PROTECTION: sentinel content in upgraded workspace must NOT pass parity.

    This verifies that the protection mechanism (compare_workspaces) catches
    a file that was left with sentinel content (i.e., the upgrader failed
    to restore it).
    """
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    real_content = b"def security_gate(): pass"
    # Simulate a file that the upgrader forgot to restore
    _write_file(fresh / "security_gate.py", real_content)
    _write_file(upgraded / "security_gate.py", vp._OLD_CONTENT_SENTINEL)

    mismatches = vp.compare_workspaces(fresh, upgraded, ["security_gate.py"])
    assert len(mismatches) == 1, (
        "Sentinel content in upgraded workspace must be flagged as a MISMATCH. "
        "The protection failed — parity check would return True for a corrupted file."
    )


def test_bypass_attempt_all_files_must_be_checked(tmp_path):
    """BYPASS ATTEMPT: compare_workspaces must check EVERY file, not just the first.

    An attacker might rely on the check short-circuiting after finding one good
    match. All files in the list must be independently verified.
    """
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"

    # Two files: first matches, second is tampered
    _write_file(fresh / "gate.py", b"real gate code")
    _write_file(upgraded / "gate.py", b"real gate code")
    _write_file(fresh / "settings.json", b'{"security": true}')
    _write_file(upgraded / "settings.json", b'{"security": false}')  # tampered

    mismatches = vp.compare_workspaces(
        fresh, upgraded, ["gate.py", "settings.json"]
    )
    # Must catch the tampered second file even though the first matched
    assert len(mismatches) == 1
    assert "settings.json" in mismatches[0]


def test_tampered_hash_in_manifest_does_not_help_attacker():
    """SECURITY: MANIFEST.json hashes are not used in compare_workspaces.

    compare_workspaces compares the actual files byte-by-byte, NOT against
    manifest hashes. A tampered manifest cannot make a mismatched file pass.
    """
    # This test verifies the design: compare_workspaces takes two workspace paths
    # and compares their contents directly. It does NOT consult the manifest.
    # create a fake workspace pair with mismatched content
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fresh = tmp / "fresh"
        upgraded = tmp / "upgraded"

        # Place different content in each workspace
        _write_file(fresh / "secret.py", b"real_secret_code")
        _write_file(upgraded / "secret.py", b"malicious_replacement")

        mismatches = vp.compare_workspaces(fresh, upgraded, ["secret.py"])
        assert len(mismatches) == 1, (
            "Mismatch must be detected even if an attacker has tampered with MANIFEST. "
            "compare_workspaces must compare file contents directly, not manifest hashes."
        )


# ---------------------------------------------------------------------------
# Script exists and is importable
# ---------------------------------------------------------------------------

def test_verify_parity_script_exists():
    """scripts/verify_parity.py must exist in the repository."""
    script = SCRIPTS_DIR / "verify_parity.py"
    assert script.exists(), f"scripts/verify_parity.py not found at {script}"


def test_verify_parity_has_main():
    """verify_parity module must expose a main() callable."""
    assert callable(vp.main)


def test_verify_parity_has_verify_parity():
    """verify_parity module must expose a verify_parity() callable."""
    assert callable(vp.verify_parity)


# ---------------------------------------------------------------------------
# Tester edge-case additions (SAF-077)
# ---------------------------------------------------------------------------

def test_ensure_src_on_path_idempotent():
    """_ensure_src_on_path() called twice must not add more entries to sys.path.

    Note: conftest.py and the editable install may already have placed src in
    sys.path before this test runs. The property we verify is that calling
    _ensure_src_on_path() N times produces the same count as calling it once —
    i.e., it is idempotent relative to the starting state, not that the
    absolute count is exactly 1.
    """
    src_dir = str(vp._REPO_ROOT / "src")
    count_before = sys.path.count(src_dir)
    vp._ensure_src_on_path()
    count_after_first = sys.path.count(src_dir)
    vp._ensure_src_on_path()
    count_after_second = sys.path.count(src_dir)
    assert count_after_first == count_after_second, (
        f"Second call to _ensure_src_on_path() added a duplicate entry: "
        f"count went from {count_after_first} to {count_after_second}."
    )
    # Also verify that if src_dir was absent, it was added at least once
    assert count_after_first >= max(1, count_before), (
        "_ensure_src_on_path() must ensure src_dir is in sys.path."
    )


def test_compare_workspaces_verbose_does_not_change_results(tmp_path):
    """compare_workspaces() verbose=True must return the same mismatches as verbose=False."""
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"
    _write_file(fresh / "a.py", b"same")
    _write_file(upgraded / "a.py", b"same")
    _write_file(fresh / "b.py", b"different_fresh")
    _write_file(upgraded / "b.py", b"different_upgraded")

    silent_result = vp.compare_workspaces(fresh, upgraded, ["a.py", "b.py"], verbose=False)
    verbose_result = vp.compare_workspaces(fresh, upgraded, ["a.py", "b.py"], verbose=True)
    assert silent_result == verbose_result, (
        "verbose mode must not change the returned mismatch list."
    )


def test_compare_workspaces_path_traversal_both_absent_not_a_mismatch(tmp_path):
    """SECURITY: A path-traversal entry absent from both sides is NOT flagged as a mismatch.

    This test verifies that even if MANIFEST.json contained a traversal path
    (e.g. '../../etc/passwd'), the script doesn't erroneously open OS-level files
    when they are absent under both workspace roots.
    """
    fresh = tmp_path / "fresh"
    upgraded = tmp_path / "upgraded"
    fresh.mkdir()
    upgraded.mkdir()
    # A traversal path that cannot exist under the workspace subdirectories
    traversal_path = "../../../nonexistent_target_file.sentinel"
    mismatches = vp.compare_workspaces(fresh, upgraded, [traversal_path])
    assert mismatches == [], (
        "A file absent under both workspace roots must not be a mismatch, "
        "including traversal paths."
    )


def test_create_upgraded_workspace_raises_on_copy_error(tmp_path):
    """create_upgraded_workspace() must raise RuntimeError when upgrade_workspace() has copy errors."""
    _ensure_src_on_path_via_import = vp._ensure_src_on_path
    _ensure_src_on_path_via_import()

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    security_files = ["gate.py"]

    mock_report = MagicMock()
    mock_report.errors = ["Failed to copy gate.py from template"]  # copy error, not verification error

    with patch("launcher.core.workspace_upgrader.upgrade_workspace", return_value=mock_report):
        with pytest.raises(RuntimeError, match="failed to copy files"):
            vp.create_upgraded_workspace(template_dir, tmp_path / "dest", security_files)


def test_create_upgraded_workspace_ignores_post_upgrade_verification_errors(tmp_path):
    """create_upgraded_workspace() must NOT raise for 'Post-upgrade verification' errors."""
    vp._ensure_src_on_path()

    template_dir = vp._TEMPLATES_DIR / "agent-workbench"
    security_files = []  # empty → no sentinel writes

    mock_report = MagicMock()
    mock_report.errors = ["Post-upgrade verification failed for audit.jsonl (stale hash)"]

    with patch("launcher.core.workspace_upgrader.upgrade_workspace", return_value=mock_report):
        # Should not raise — post-upgrade verification errors are intentionally filtered
        result = vp.create_upgraded_workspace(template_dir, tmp_path, security_files)
    assert result == tmp_path / "upgraded_workspace"


def test_verify_parity_exits_one_on_runtime_error():
    """CLI must exit with code 1 when create_upgraded_workspace() raises RuntimeError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "run_runtime_error_test.py"
        script.write_text(
            f"import sys\n"
            f"sys.path.insert(0, r'{SCRIPTS_DIR!s}')\n"
            f"import verify_parity as vp\n"
            f"from unittest.mock import patch\n"
            f"with patch.object(vp, 'create_upgraded_workspace', "
            f"side_effect=RuntimeError('simulated copy failure')):\n"
            f"    vp.main()\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert result.returncode == 1
    assert "ERROR" in result.stderr


def test_sha256_reads_file_in_binary_chunks(tmp_path):
    """_sha256 must produce correct digest for a file larger than one 8192-byte chunk."""
    large_content = b"A" * 20_000  # 20 KB — spans multiple 8192-byte read chunks
    f = _write_file(tmp_path / "large.bin", large_content)
    expected = hashlib.sha256(large_content).hexdigest()
    assert vp._sha256(f) == expected, "Multi-chunk SHA-256 must match single-pass hashlib result"


def test_get_security_critical_files_missing_key(tmp_path):
    """Files without 'security_critical' key must not appear in the result."""
    manifest = {
        "files": {
            "with_key.py": {"sha256": "aaa", "security_critical": True},
            "without_key.py": {"sha256": "bbb"},  # key absent entirely
        }
    }
    result = vp.get_security_critical_files(manifest)
    assert "with_key.py" in result
    assert "without_key.py" not in result, (
        "Files where 'security_critical' key is absent must not appear in the result."
    )
