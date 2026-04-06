"""Tester edge-case tests for FIX-122: Move MANIFEST.json inside .github/hooks/scripts/.

Additional tests beyond the Developer's regression suite covering:
- MANIFEST.json content schema validation (both templates).
- Old-path references absent from all consumers (no stale "MANIFEST.json" at root).
- generate_manifest.py _SKIP_FILES contains ONLY the new path, not the old root path.
- No symlinks placed at the old MANIFEST.json locations.
- Both MANIFEST.json files are consistent in schema/top-level keys.
- Security: MANIFEST.json does not track itself or executable scripts unsafely.
- generate_manifest.py does not hard-code the old root-level manifest path.
- workspace_upgrader.py does not reference the stale _MANIFEST_NAME = "MANIFEST.json".
- verify_parity.py does not reference the stale agent-workbench/MANIFEST.json root path.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_WORKBENCH = REPO_ROOT / "templates" / "agent-workbench"
CLEAN_WORKSPACE = REPO_ROOT / "templates" / "clean-workspace"
_NEW_SUBPATH = Path(".github") / "hooks" / "scripts" / "MANIFEST.json"


# ---------------------------------------------------------------------------
# Schema / content validation
# ---------------------------------------------------------------------------

def test_manifest_schema_agent_workbench():
    """MANIFEST.json in agent-workbench must have required top-level keys."""
    manifest_path = AGENT_WORKBENCH / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ("_comment", "_generated", "template", "file_count", "files"):
        assert key in data, f"MANIFEST.json missing required key: {key!r}"


def test_manifest_schema_clean_workspace():
    """MANIFEST.json in clean-workspace must have required top-level keys."""
    manifest_path = CLEAN_WORKSPACE / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ("_comment", "_generated", "template", "file_count", "files"):
        assert key in data, f"clean-workspace MANIFEST.json missing required key: {key!r}"


def test_manifest_files_count_matches_agent_workbench():
    """file_count in agent-workbench MANIFEST.json must match len(files)."""
    manifest_path = AGENT_WORKBENCH / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["file_count"] == len(data["files"]), (
        f"file_count {data['file_count']} != len(files) {len(data['files'])}"
    )


def test_manifest_files_count_matches_clean_workspace():
    """file_count in clean-workspace MANIFEST.json must match len(files)."""
    manifest_path = CLEAN_WORKSPACE / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["file_count"] == len(data["files"]), (
        f"file_count {data['file_count']} != len(files) {len(data['files'])}"
    )


def test_manifest_template_field_agent_workbench():
    """MANIFEST.json 'template' field must equal 'agent-workbench'."""
    manifest_path = AGENT_WORKBENCH / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("template") == "agent-workbench", (
        f"Expected template='agent-workbench', got {data.get('template')!r}"
    )


def test_manifest_template_field_clean_workspace():
    """MANIFEST.json 'template' field must equal 'clean-workspace'."""
    manifest_path = CLEAN_WORKSPACE / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("template") == "clean-workspace", (
        f"Expected template='clean-workspace', got {data.get('template')!r}"
    )


def test_manifest_files_are_strings_with_sha256_agent_workbench():
    """Every entry in agent-workbench MANIFEST.json files must contain a sha256 key."""
    manifest_path = AGENT_WORKBENCH / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel_path, entry in data["files"].items():
        assert "sha256" in entry, (
            f"File entry {rel_path!r} is missing 'sha256' key"
        )
        assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64, (
            f"File entry {rel_path!r} sha256 is not a valid 64-char hex string"
        )


def test_manifest_files_are_strings_with_sha256_clean_workspace():
    """Every entry in clean-workspace MANIFEST.json files must contain a sha256 key."""
    manifest_path = CLEAN_WORKSPACE / _NEW_SUBPATH
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel_path, entry in data["files"].items():
        assert "sha256" in entry, (
            f"clean-workspace file entry {rel_path!r} is missing 'sha256' key"
        )
        assert isinstance(entry["sha256"], str) and len(entry["sha256"]) == 64, (
            f"clean-workspace file entry {rel_path!r} sha256 is not a valid 64-char hex string"
        )


# ---------------------------------------------------------------------------
# Old-path references absent in consumers (no stale paths)
# ---------------------------------------------------------------------------

def test_generate_manifest_no_stale_root_manifest_path():
    """generate_manifest.py must NOT reference 'templates/agent-workbench/MANIFEST.json' (old root path)."""
    script = (REPO_ROOT / "scripts" / "generate_manifest.py").read_text(encoding="utf-8")
    stale_patterns = [
        '"agent-workbench" / "MANIFEST.json"',
        '"agent-workbench/MANIFEST.json"',
        "agent-workbench/MANIFEST.json",
    ]
    for pat in stale_patterns:
        # Allow the stale pattern only in comments
        for line in script.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue  # comments are ok
            assert pat not in line, (
                f"generate_manifest.py contains stale path in non-comment: {pat!r}"
            )


def test_workspace_upgrader_no_stale_manifest_name():
    """workspace_upgrader.py must NOT set _MANIFEST_NAME to bare 'MANIFEST.json'."""
    upgrader = (REPO_ROOT / "src" / "launcher" / "core" / "workspace_upgrader.py").read_text(encoding="utf-8")
    assert '_MANIFEST_NAME = "MANIFEST.json"' not in upgrader, (
        "workspace_upgrader.py still uses stale _MANIFEST_NAME = 'MANIFEST.json'"
    )
    assert "_MANIFEST_NAME = Path('MANIFEST.json')" not in upgrader, (
        "workspace_upgrader.py still uses stale _MANIFEST_NAME = Path('MANIFEST.json')"
    )


def test_verify_parity_no_stale_manifest_root_path():
    """verify_parity.py must NOT reference the old MANIFEST.json at template root."""
    parity = (REPO_ROOT / "scripts" / "verify_parity.py").read_text(encoding="utf-8")
    stale = '"agent-workbench" / "MANIFEST.json"'
    for line in parity.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        assert stale not in line, (
            "verify_parity.py contains stale root path in non-comment: "
            f"{stale!r}"
        )


# ---------------------------------------------------------------------------
# Symlink guard: old path must not be a symlink pointing to new location
# ---------------------------------------------------------------------------

def test_no_symlink_at_old_location_agent_workbench():
    """templates/agent-workbench/MANIFEST.json must not exist — not even as a symlink."""
    old_path = AGENT_WORKBENCH / "MANIFEST.json"
    assert not old_path.exists() and not old_path.is_symlink(), (
        f"MANIFEST.json still present (possibly as symlink) at old root: {old_path}"
    )


def test_no_symlink_at_old_location_clean_workspace():
    """templates/clean-workspace/MANIFEST.json must not exist — not even as a symlink."""
    old_path = CLEAN_WORKSPACE / "MANIFEST.json"
    assert not old_path.exists() and not old_path.is_symlink(), (
        f"MANIFEST.json still present (possibly as symlink) at old root: {old_path}"
    )


# ---------------------------------------------------------------------------
# New MANIFEST.json directory must not be a symlink
# ---------------------------------------------------------------------------

def test_manifest_not_a_symlink_agent_workbench():
    """MANIFEST.json at new location must be a regular file, not a symlink."""
    p = AGENT_WORKBENCH / _NEW_SUBPATH
    assert p.is_file() and not p.is_symlink(), (
        f"MANIFEST.json at {p} is a symlink, not a regular file"
    )


def test_manifest_not_a_symlink_clean_workspace():
    """MANIFEST.json at new location must be a regular file, not a symlink."""
    p = CLEAN_WORKSPACE / _NEW_SUBPATH
    assert p.is_file() and not p.is_symlink(), (
        f"MANIFEST.json at {p} is a symlink, not a regular file"
    )


# ---------------------------------------------------------------------------
# _SKIP_FILES in generate_manifest.py must contain new path, not old
# ---------------------------------------------------------------------------

def test_generate_manifest_skip_files_has_new_path():
    """generate_manifest.py _SKIP_FILES must contain the new MANIFEST path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_manifest",
        str(REPO_ROOT / "scripts" / "generate_manifest.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    skip_files = getattr(mod, "_SKIP_FILES", set())
    assert ".github/hooks/scripts/MANIFEST.json" in skip_files, (
        f"_SKIP_FILES must include new manifest path; got: {skip_files}"
    )


def test_generate_manifest_skip_files_not_old_root():
    """generate_manifest.py _SKIP_FILES must NOT contain the old root path 'MANIFEST.json'."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_manifest",
        str(REPO_ROOT / "scripts" / "generate_manifest.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    skip_files = getattr(mod, "_SKIP_FILES", set())
    assert "MANIFEST.json" not in skip_files, (
        "_SKIP_FILES must not contain bare 'MANIFEST.json' (old root path)"
    )


# ---------------------------------------------------------------------------
# Both MANIFEST.json files share the same top-level schema keys
# ---------------------------------------------------------------------------

def test_both_manifest_files_share_schema():
    """Both templates' MANIFEST.json files must have identical top-level key sets."""
    aw = json.loads((AGENT_WORKBENCH / _NEW_SUBPATH).read_text(encoding="utf-8"))
    cw = json.loads((CLEAN_WORKSPACE / _NEW_SUBPATH).read_text(encoding="utf-8"))
    aw_keys = set(aw.keys())
    cw_keys = set(cw.keys())
    assert aw_keys == cw_keys, (
        f"Schema mismatch between templates:\n"
        f"  agent-workbench keys: {sorted(aw_keys)}\n"
        f"  clean-workspace keys: {sorted(cw_keys)}"
    )


# ---------------------------------------------------------------------------
# Security: no path-traversal sequences in MANIFEST.json file keys
# ---------------------------------------------------------------------------

def test_manifest_no_path_traversal_agent_workbench():
    """MANIFEST.json file keys must not contain '..' (path traversal)."""
    data = json.loads((AGENT_WORKBENCH / _NEW_SUBPATH).read_text(encoding="utf-8"))
    for rel_path in data.get("files", {}):
        assert ".." not in rel_path, (
            f"Path traversal detected in agent-workbench MANIFEST.json key: {rel_path!r}"
        )


def test_manifest_no_path_traversal_clean_workspace():
    """MANIFEST.json file keys must not contain '..' (path traversal)."""
    data = json.loads((CLEAN_WORKSPACE / _NEW_SUBPATH).read_text(encoding="utf-8"))
    for rel_path in data.get("files", {}):
        assert ".." not in rel_path, (
            f"Path traversal detected in clean-workspace MANIFEST.json key: {rel_path!r}"
        )
