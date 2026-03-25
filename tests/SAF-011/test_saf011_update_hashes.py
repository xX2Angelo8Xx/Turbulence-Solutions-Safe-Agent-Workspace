"""Tests for SAF-011: Hash Update Script

Verifies that update_hashes.py exists, correctly computes SHA256 hashes,
correctly re-embeds them into security_gate.py, and handles edge cases.

Test IDs:
  TST-624  test_script_exists_default_project
  TST-625  test_script_exists_templates
  TST-626  test_script_is_valid_python
  TST-627  test_no_absolute_paths_in_script
  TST-628  test_sha256_file_valid
  TST-629  test_sha256_file_missing
  TST-630  test_canonical_gate_hash_zeros_gate_constant
  TST-631  test_canonical_hash_independent_of_gate_hash_value
  TST-632  test_patch_hash_settings
  TST-633  test_patch_hash_gate
  TST-634  test_patch_hash_raises_when_pattern_missing
  TST-635  test_full_update_on_real_files_integrity_passes
  TST-636  test_update_is_idempotent
  TST-637  test_update_error_missing_settings
  TST-638  test_update_error_missing_gate
  TST-639  test_embedded_hashes_are_64_lowercase_hex
  TST-640  test_scripts_are_byte_for_byte_identical
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
_TEMPLATE_SCRIPTS_DIR = (
    _REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
_UPDATE_HASHES_PATH = _SCRIPTS_DIR / "update_hashes.py"
_TEMPLATE_UPDATE_HASHES_PATH = _TEMPLATE_SCRIPTS_DIR / "update_hashes.py"
_GATE_PATH = _SCRIPTS_DIR / "security_gate.py"
_SETTINGS_PATH = _REPO_ROOT / "templates" / "agent-workbench" / ".vscode" / "settings.json"

# ---------------------------------------------------------------------------
# Import the module under test from its non-standard location
# ---------------------------------------------------------------------------

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import update_hashes as uh  # noqa: E402


# ===========================================================================
# TST-624: Script exists in templates/coding
# ===========================================================================

def test_script_exists_default_project():
    assert _UPDATE_HASHES_PATH.is_file(), (
        f"update_hashes.py missing from {_UPDATE_HASHES_PATH}"
    )


# ===========================================================================
# TST-625: Script copy exists in templates
# ===========================================================================

def test_script_exists_templates():
    assert _TEMPLATE_UPDATE_HASHES_PATH.is_file(), (
        f"update_hashes.py missing from templates: {_TEMPLATE_UPDATE_HASHES_PATH}"
    )


# ===========================================================================
# TST-626: Script is valid Python (ast.parse passes)
# ===========================================================================

def test_script_is_valid_python():
    source = _UPDATE_HASHES_PATH.read_text(encoding="utf-8")
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"update_hashes.py has a syntax error: {exc}")


# ===========================================================================
# TST-627: No absolute paths hard-coded in script
# ===========================================================================

def test_no_absolute_paths_in_script():
    source = _UPDATE_HASHES_PATH.read_text(encoding="utf-8")
    # Should not contain Windows-style C:\ or Unix-style /home/ absolute paths.
    # Allow __file__ references (relative runtime resolution).
    assert "C:\\" not in source, "Hardcoded Windows absolute path found"
    assert "/home/" not in source, "Hardcoded Unix absolute path found"
    assert "C:/" not in source, "Hardcoded Windows absolute path found"


# ===========================================================================
# TST-628: _sha256_file returns correct hash for a known file
# ===========================================================================

def test_sha256_file_valid(tmp_path):
    content = b"turbulence solutions integrity test"
    f = tmp_path / "data.bin"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert uh._sha256_file(f) == expected


# ===========================================================================
# TST-629: _sha256_file raises OSError when file is missing
# ===========================================================================

def test_sha256_file_missing(tmp_path):
    missing = tmp_path / "nonexistent.bin"
    with pytest.raises(OSError):
        uh._sha256_file(missing)


# ===========================================================================
# TST-630: _compute_canonical_gate_hash zeros _KNOWN_GOOD_GATE_HASH value
# ===========================================================================

def test_canonical_gate_hash_zeros_gate_constant():
    known_hash = "a" * 64
    zeroed = "0" * 64
    content = (
        b'_KNOWN_GOOD_GATE_HASH: str = "' + known_hash.encode() + b'"\n'
    )
    content_zeroed = (
        b'_KNOWN_GOOD_GATE_HASH: str = "' + zeroed.encode() + b'"\n'
    )
    result = uh._compute_canonical_gate_hash(content)
    expected = hashlib.sha256(content_zeroed).hexdigest()
    assert result == expected


# ===========================================================================
# TST-631: Canonical hash is independent of the stored gate hash value
# ===========================================================================

def test_canonical_hash_independent_of_gate_hash_value():
    base_prefix = b'_KNOWN_GOOD_GATE_HASH: str = "'
    suffix = b'"\nsome other content stays constant\n'
    content_a = base_prefix + b"a" * 64 + suffix
    content_b = base_prefix + b"b" * 64 + suffix
    assert uh._compute_canonical_gate_hash(content_a) == uh._compute_canonical_gate_hash(content_b)


# ===========================================================================
# TST-632: _patch_hash replaces settings hash correctly
# ===========================================================================

def test_patch_hash_settings():
    old_hash = "1" * 64
    new_hash = "2" * 64
    content = (
        b'_KNOWN_GOOD_SETTINGS_HASH: str = "' + old_hash.encode() + b'"\n'
    )
    result = uh._patch_hash(content, uh._SETTINGS_HASH_RE, new_hash)
    assert new_hash.encode() in result
    assert old_hash.encode() not in result


# ===========================================================================
# TST-633: _patch_hash replaces gate hash correctly
# ===========================================================================

def test_patch_hash_gate():
    old_hash = "c" * 64
    new_hash = "d" * 64
    content = (
        b'_KNOWN_GOOD_GATE_HASH: str = "' + old_hash.encode() + b'"\n'
    )
    result = uh._patch_hash(content, uh._GATE_HASH_RE, new_hash)
    assert new_hash.encode() in result
    assert old_hash.encode() not in result


# ===========================================================================
# TST-634: _patch_hash raises ValueError when pattern not found
# ===========================================================================

def test_patch_hash_raises_when_pattern_missing():
    content = b"no hash constant here\n"
    with pytest.raises(ValueError, match="Hash constant pattern not found"):
        uh._patch_hash(content, uh._SETTINGS_HASH_RE, "a" * 64)


# ===========================================================================
# TST-635: Full update on real files — verify_file_integrity() returns True
# ===========================================================================

def test_full_update_on_real_files_integrity_passes(tmp_path):
    # Make a temp copy of the scripts dir + settings to avoid mutating real files.
    temp_scripts = tmp_path / "scripts"
    temp_scripts.mkdir()
    # Copy gate and zone_classifier so import works
    shutil.copy(_GATE_PATH, temp_scripts / "security_gate.py")
    zone_src = _SCRIPTS_DIR / "zone_classifier.py"
    shutil.copy(zone_src, temp_scripts / "zone_classifier.py")
    # Copy update_hashes.py
    shutil.copy(_UPDATE_HASHES_PATH, temp_scripts / "update_hashes.py")
    # Construct workspace root structure
    workspace_root = tmp_path / "workspace"
    vscode_dir = workspace_root / ".vscode"
    vscode_dir.mkdir(parents=True)
    github_dir = workspace_root / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)
    shutil.copy(_SETTINGS_PATH, vscode_dir / "settings.json")
    shutil.copy(_GATE_PATH, github_dir / "security_gate.py")
    shutil.copy(zone_src, github_dir / "zone_classifier.py")
    update_script = github_dir / "update_hashes.py"
    shutil.copy(_UPDATE_HASHES_PATH, update_script)

    # Corrupt both hashes so we know the script actually updates them.
    gate_content = (github_dir / "security_gate.py").read_bytes()
    corrupted = re.sub(
        rb'(?<=_KNOWN_GOOD_SETTINGS_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        gate_content,
    )
    corrupted = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        corrupted,
    )
    (github_dir / "security_gate.py").write_bytes(corrupted)

    # Patch _resolve_paths in the module to point to our temp copies.
    def _mock_resolve_paths():
        return (github_dir / "security_gate.py", vscode_dir / "settings.json")

    # Re-import update_hashes from the temp location so __file__ is correct.
    spec = importlib.util.spec_from_file_location("update_hashes_tmp", update_script)
    uh_tmp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uh_tmp)
    uh_tmp._resolve_paths = _mock_resolve_paths
    uh_tmp.update_hashes()

    # Now verify integrity using security_gate from the same temp location.
    module_name = "security_gate_tmp_saf011"
    sys.path.insert(0, str(github_dir))
    try:
        sg_spec = importlib.util.spec_from_file_location(
            module_name, github_dir / "security_gate.py"
        )
        sg_tmp = importlib.util.module_from_spec(sg_spec)
        # Must register before exec so @dataclasses.dataclass can find the module.
        sys.modules[module_name] = sg_tmp
        sg_spec.loader.exec_module(sg_tmp)
        assert sg_tmp.verify_file_integrity(), (
            "verify_file_integrity() returned False after update_hashes() ran"
        )
    finally:
        sys.path.remove(str(github_dir))
        sys.modules.pop(module_name, None)


# ===========================================================================
# TST-636: Running update_hashes twice is idempotent
# ===========================================================================

def test_update_is_idempotent(tmp_path):
    workspace_root = tmp_path / "workspace"
    vscode_dir = workspace_root / ".vscode"
    vscode_dir.mkdir(parents=True)
    github_dir = workspace_root / ".github" / "hooks" / "scripts"
    github_dir.mkdir(parents=True)
    shutil.copy(_SETTINGS_PATH, vscode_dir / "settings.json")
    shutil.copy(_GATE_PATH, github_dir / "security_gate.py")
    zone_src = _SCRIPTS_DIR / "zone_classifier.py"
    shutil.copy(zone_src, github_dir / "zone_classifier.py")
    update_script = github_dir / "update_hashes.py"
    shutil.copy(_UPDATE_HASHES_PATH, update_script)

    spec = importlib.util.spec_from_file_location("update_hashes_idempotent", update_script)
    uh_i = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uh_i)

    def _mock_resolve_paths():
        return (github_dir / "security_gate.py", vscode_dir / "settings.json")

    uh_i._resolve_paths = _mock_resolve_paths

    uh_i.update_hashes()
    content_after_first = (github_dir / "security_gate.py").read_bytes()

    uh_i.update_hashes()
    content_after_second = (github_dir / "security_gate.py").read_bytes()

    assert content_after_first == content_after_second, (
        "update_hashes is not idempotent — second run produced different output"
    )


# ===========================================================================
# TST-637: update_hashes exits with error when settings.json is missing
# ===========================================================================

def test_update_error_missing_settings(tmp_path, capsys):
    gate_path = tmp_path / "security_gate.py"
    gate_path.write_bytes(_GATE_PATH.read_bytes())
    missing_settings = tmp_path / "nonexistent" / "settings.json"

    def _mock_resolve_paths():
        return (gate_path, missing_settings)

    with patch.object(uh, "_resolve_paths", _mock_resolve_paths):
        with pytest.raises(SystemExit) as exc_info:
            uh.update_hashes()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "settings.json" in captured.err
    assert "ERROR" in captured.err


# ===========================================================================
# TST-638: update_hashes exits with error when security_gate.py is missing
# ===========================================================================

def test_update_error_missing_gate(tmp_path, capsys):
    settings_path = tmp_path / "settings.json"
    settings_path.write_bytes(_SETTINGS_PATH.read_bytes())
    missing_gate = tmp_path / "nonexistent" / "security_gate.py"

    def _mock_resolve_paths():
        return (missing_gate, settings_path)

    with patch.object(uh, "_resolve_paths", _mock_resolve_paths):
        with pytest.raises(SystemExit) as exc_info:
            uh.update_hashes()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "security_gate.py" in captured.err
    assert "ERROR" in captured.err


# ===========================================================================
# TST-639: Embedded hashes in real security_gate.py are 64 lowercase hex chars
# ===========================================================================

def test_embedded_hashes_are_64_lowercase_hex():
    content = _GATE_PATH.read_text(encoding="utf-8")
    settings_match = re.search(
        r'_KNOWN_GOOD_SETTINGS_HASH: str = "([0-9a-f]{64})"', content
    )
    gate_match = re.search(
        r'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', content
    )
    assert settings_match, "_KNOWN_GOOD_SETTINGS_HASH not found or not 64 hex chars"
    assert gate_match, "_KNOWN_GOOD_GATE_HASH not found or not 64 hex chars"


# ===========================================================================
# TST-640: templates/coding and templates copies are byte-for-byte identical
# ===========================================================================

def test_scripts_are_byte_for_byte_identical():
    default_bytes = _UPDATE_HASHES_PATH.read_bytes()
    template_bytes = _TEMPLATE_UPDATE_HASHES_PATH.read_bytes()
    assert default_bytes == template_bytes, (
        "templates/coding and templates copies of update_hashes.py differ"
    )
