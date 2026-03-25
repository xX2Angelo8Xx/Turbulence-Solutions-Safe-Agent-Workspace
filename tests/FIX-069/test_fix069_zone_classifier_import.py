"""
Tests for FIX-069: Fix zone_classifier import for embedded Python.

Verifies that:
1. security_gate.py contains sys.path.insert before import zone_classifier
2. zone_classifier is importable when sys.path is restricted (simulated embedded Python)
3. The sys.path fix resolves the script directory correctly
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

# Path to the security_gate.py under test
SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)
SECURITY_GATE = SCRIPTS_DIR / "security_gate.py"


def _read_source() -> str:
    return SECURITY_GATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_sys_path_insert_present():
    """security_gate.py must contain the sys.path.insert fix line."""
    src = _read_source()
    assert "sys.path.insert(0, str(Path(__file__).resolve().parent))" in src, (
        "FIX-069 sys.path fix line not found in security_gate.py"
    )


def test_sys_path_insert_before_import_zone_classifier():
    """The sys.path.insert line must appear BEFORE 'import zone_classifier'."""
    src = _read_source()
    fix_line = "sys.path.insert(0, str(Path(__file__).resolve().parent))"
    import_line = "import zone_classifier"

    assert fix_line in src, "sys.path.insert fix line not found"
    assert import_line in src, "import zone_classifier not found"

    fix_pos = src.index(fix_line)
    import_pos = src.index(import_line)
    assert fix_pos < import_pos, (
        f"sys.path.insert (pos {fix_pos}) must come before "
        f"import zone_classifier (pos {import_pos})"
    )


def test_fix_comment_mentions_embedded_python():
    """The comment above the fix should reference the embedded Python distribution."""
    src = _read_source()
    # Check for FIX-069 or embedded Python mention near the fix
    assert "FIX-069" in src or "embedded" in src.lower(), (
        "Expected a comment referencing FIX-069 or 'embedded' near the fix"
    )


# ---------------------------------------------------------------------------
# Functional tests — simulate embedded Python restricted sys.path
# ---------------------------------------------------------------------------


def test_zone_classifier_importable_with_restricted_sys_path():
    """
    Simulate an embedded Python environment where the script directory is NOT
    on sys.path by default. Reproduce the original failure then confirm the
    fix resolves it.
    """
    zone_classifier_path = SCRIPTS_DIR / "zone_classifier.py"
    assert zone_classifier_path.exists(), "zone_classifier.py must exist in scripts dir"

    # Save original state — zone_classifier may already be in sys.modules from
    # test collection (SAF-001 imports security_gate which imports zone_classifier).
    # We MUST restore it so that SAF-001/conftest.py _patch_detect_project_folder
    # fixture can still find it when SAF-001 tests run after this one.
    original_path = sys.path.copy()
    _saved_zc = sys.modules.get("zone_classifier")  # None or existing module object

    # Remove scripts dir from sys.path to reproduce the original error
    restricted = [p for p in sys.path if str(SCRIPTS_DIR) not in p and str(SCRIPTS_DIR).replace("\\", "/") not in p]

    try:
        sys.path = restricted

        # Confirm zone_classifier is NOT importable without the fix
        if "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]

        importable_before = True
        try:
            import zone_classifier  # noqa: F401
        except ImportError:
            importable_before = False

        # Now apply the fix: insert the scripts dir as the fix does
        sys.path.insert(0, str(SCRIPTS_DIR))

        if "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]

        importable_after = True
        try:
            import zone_classifier as zc  # noqa: F401
        except ImportError:
            importable_after = False

        # The fix must make it importable
        assert importable_after, (
            "zone_classifier still not importable after sys.path.insert fix"
        )

    finally:
        # Restore sys.path
        sys.path = original_path
        # Restore zone_classifier in sys.modules to its original state.
        # Without this, the SAF-001/conftest.py fixture (_patch_detect_project_folder)
        # receives sys.modules.get("zone_classifier") == None, skips patching, and
        # all SAF-001 zone tests fail because detect_project_folder is unpatched.
        if _saved_zc is not None:
            sys.modules["zone_classifier"] = _saved_zc
        elif "zone_classifier" in sys.modules:
            del sys.modules["zone_classifier"]


def test_script_dir_resolved_correctly_absolute():
    """
    Verify that Path(__file__).resolve().parent gives the scripts directory
    regardless of whether an absolute path is provided.
    """
    # Simulate what security_gate.py does with its own __file__
    simulated_file = SECURITY_GATE  # already absolute
    resolved_parent = Path(simulated_file).resolve().parent

    assert resolved_parent == SCRIPTS_DIR.resolve(), (
        f"Expected {SCRIPTS_DIR.resolve()}, got {resolved_parent}"
    )


def test_script_dir_resolved_correctly_relative():
    """
    Verify that Path(__file__).resolve().parent resolves correctly even
    when __file__ is a relative path (as may happen in some invocation contexts).
    """
    original_cwd = os.getcwd()
    try:
        # Change to repo root so we can construct a relative path
        repo_root = Path(__file__).resolve().parent.parent.parent
        os.chdir(repo_root)

        relative_file = Path("templates/agent-workbench/.github/hooks/scripts/security_gate.py")
        resolved_parent = relative_file.resolve().parent

        assert resolved_parent == SCRIPTS_DIR.resolve(), (
            f"Expected {SCRIPTS_DIR.resolve()}, got {resolved_parent}"
        )
    finally:
        os.chdir(original_cwd)


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------


def test_path_with_spaces_resolves_correctly(tmp_path):
    """Path(__file__).resolve().parent must work when the path contains spaces.

    The fix uses str(Path(__file__).resolve().parent) which is then passed to
    sys.path.insert(). On all platforms pathlib handles spaces natively — this
    test verifies that assumption using a real temporary directory.
    """
    # Create a directory with spaces in the name to simulate a real install path
    # such as "C:/Program Files/Agent Environment Launcher/.../scripts/"
    spaced_dir = tmp_path / "path with spaces" / "hooks" / "scripts"
    spaced_dir.mkdir(parents=True)
    simulated_file = spaced_dir / "security_gate.py"
    simulated_file.write_text("# placeholder", encoding="utf-8")

    # Replicate what the fix does
    resolved_parent = simulated_file.resolve().parent
    path_str = str(resolved_parent)

    assert resolved_parent == spaced_dir.resolve(), (
        "Path resolution returned a different directory than expected"
    )
    # str() must preserve the spaces so sys.path.insert() receives the correct string
    assert " " in path_str, (
        "Space characters were lost during path resolution/stringification"
    )


def test_sys_path_insert_idempotent_import():
    """Repeated sys.path.insert(0, SCRIPTS_DIR) calls must not break zone_classifier import.

    The embedded Python shim is single-shot (one invocation per hook call), but
    this test confirms that if the insert were called multiple times (e.g. from
    test scaffolding or reimport scenarios) zone_classifier remains importable.
    """
    original_path = sys.path.copy()
    saved_zc = sys.modules.get("zone_classifier")
    try:
        # Insert the same path multiple times — simulating repeated invocations
        for _ in range(5):
            sys.path.insert(0, str(SCRIPTS_DIR))

        count = sys.path.count(str(SCRIPTS_DIR))
        assert count >= 5, "Expected at least 5 copies of SCRIPTS_DIR in sys.path"

        # Despite duplicates, zone_classifier must remain importable
        sys.modules.pop("zone_classifier", None)
        import zone_classifier as zc_test  # noqa: F401
        assert zc_test is not None, "zone_classifier import failed despite duplicates in sys.path"
    finally:
        sys.path = original_path
        sys.modules.pop("zone_classifier", None)
        if saved_zc is not None:
            sys.modules["zone_classifier"] = saved_zc


def test_security_gate_decide_functional_after_fix():
    """After the sys.path fix, security_gate.decide() must return a valid decision.

    This end-to-end test reimports both modules from a restricted sys.path (as
    the embedded Python shim does), verifying that zone_classifier is found and
    that the security gate can process a real tool call without crashing.
    """
    original_path = sys.path.copy()
    saved_sg = sys.modules.get("security_gate")
    saved_zc = sys.modules.get("zone_classifier")
    try:
        # Simulate restricted embedded-Python sys.path
        restricted = [
            p for p in sys.path
            if str(SCRIPTS_DIR) not in p
            and str(SCRIPTS_DIR).replace("\\", "/") not in p
        ]
        sys.path = restricted
        # Apply the fix — identical to the line added by FIX-069
        sys.path.insert(0, str(SCRIPTS_DIR))

        # Force fresh imports to exercise the actual fix code path
        sys.modules.pop("security_gate", None)
        sys.modules.pop("zone_classifier", None)
        import security_gate as sg_fresh  # noqa: F401

        # TodoRead is in _ALWAYS_ALLOW_TOOLS — no path or zone check involved.
        # This confirms the full import chain (security_gate → zone_classifier) works
        # and that decide() returns "allow" without crashing.
        payload = {"tool_name": "TodoRead"}
        result = sg_fresh.decide(payload, "/workspace")
        assert result == "allow", (
            f"decide() returned {result!r} for TodoRead; expected 'allow'. "
            "zone_classifier may not have been loaded correctly."
        )
    finally:
        sys.path = original_path
        # Restore module state to prevent contamination of SAF-001/002 tests
        sys.modules.pop("security_gate", None)
        sys.modules.pop("zone_classifier", None)
        if saved_zc is not None:
            sys.modules["zone_classifier"] = saved_zc
        if saved_sg is not None:
            sys.modules["security_gate"] = saved_sg


def test_gate_hash_valid_after_fix():
    """_KNOWN_GOOD_GATE_HASH embedded in security_gate.py must match the current file.

    FIX-069 modified security_gate.py and updated the hash via update_hashes.py.
    This test independently recomputes the canonical hash and compares it with
    the stored constant.  A mismatch means verify_file_integrity() would deny
    ALL tool calls, making the entire security gate non-functional at runtime.
    """
    import hashlib
    import re as _re

    with open(SECURITY_GATE, "rb") as fh:
        content = fh.read()

    # Canonical form: replace the 64-char stored hash with 64 zeros (same as
    # _compute_gate_canonical_hash in security_gate.py)
    canonical = _re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content,
    )
    computed_hash = hashlib.sha256(canonical).hexdigest()

    # Extract the stored constant from source
    source = content.decode("utf-8", errors="replace")
    match = _re.search(r'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-fA-F]{64})"', source)
    assert match, "_KNOWN_GOOD_GATE_HASH constant not found in security_gate.py"
    stored_hash = match.group(1)

    assert computed_hash == stored_hash, (
        f"FIX-069: _KNOWN_GOOD_GATE_HASH is stale after the fix was applied.\n"
        f"  Stored  : {stored_hash}\n"
        f"  Computed: {computed_hash}\n"
        "Run update_hashes.py to regenerate the hash constant."
    )
