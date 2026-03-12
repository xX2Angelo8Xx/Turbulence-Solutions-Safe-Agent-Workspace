"""INS-004 — Template Bundling edge-case tests (Tester Agent, Iteration 1).

Edge cases NOT covered by the Developer's test_ins004_template_bundling.py:

- require-approval.json presence (developer's test blocked by ImportError)
- JSON/JSONC validity of safety config files
- No individual .pyc files (not just __pycache__ dirs)
- File content parity between Default-Project/ and templates/coding/
- Zero-byte files absent from critical safety files
- No symlinks in template (cross-platform copy safety)
- templates/ root contains no loose files
- .github/skills/ and .github/prompts/ subdirectories present
- list_templates() sorted-return guarantee with multiple entries
- config.TEMPLATES_DIR is defined, is a Path, and points to an existing dir

This file is intentionally independent of the developer's test file so it
can run even when the developer's module-level import of `list_templates` fails.
Tests that depend on the (currently missing) code changes use test-level imports
and produce informative FAIL messages until the code is added.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_TEMPLATES_ROOT = _REPO_ROOT / "templates"
_CODING_TEMPLATE = _TEMPLATES_ROOT / "coding"
_DEFAULT_PROJECT = _REPO_ROOT / "Default-Project"


# ---------------------------------------------------------------------------
# Presence check — runs independently of the broken import in the dev's file
# ---------------------------------------------------------------------------

def test_require_approval_json_exists_in_template():
    """require-approval.json must exist at templates/coding/.github/hooks/.

    The developer's test_coding_hooks_json_exists covers this, but that
    entire test module is currently blocked by an ImportError.  This test
    runs independently to surface the missing file immediately.
    """
    path = _CODING_TEMPLATE / ".github" / "hooks" / "require-approval.json"
    assert path.is_file(), (
        "require-approval.json is missing from templates/coding/.github/hooks/. "
        "It is present in Default-Project/.github/hooks/ but was not copied to the template."
    )


# ---------------------------------------------------------------------------
# JSON / JSONC validity
# ---------------------------------------------------------------------------

def _strip_jsonc_line_comments(text: str) -> str:
    """Strip // single-line comments from JSONC text for json.loads compatibility."""
    lines = []
    for line in text.splitlines():
        # Remove everything after an unquoted //
        stripped = re.sub(r'(?<!:)//.*$', '', line)
        lines.append(stripped)
    return "\n".join(lines)


def test_vscode_settings_is_valid_jsonc():
    """templates/coding/.vscode/settings.json must be parseable JSONC.

    VS Code settings files use JSONC (JSON with Comments).  Strip the
    // line-comments before parsing so standard json.loads can validate
    the structure.
    """
    settings_path = _CODING_TEMPLATE / ".vscode" / "settings.json"
    assert settings_path.is_file(), ".vscode/settings.json must exist"
    raw = settings_path.read_text(encoding="utf-8")
    clean = _strip_jsonc_line_comments(raw)
    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        pytest.fail(f".vscode/settings.json is not valid JSONC: {exc}")
    assert isinstance(data, dict), "settings.json must be a JSON object"


def test_require_approval_json_is_valid_json():
    """templates/coding/.github/hooks/require-approval.json must be valid JSON."""
    json_path = _CODING_TEMPLATE / ".github" / "hooks" / "require-approval.json"
    assert json_path.is_file(), (
        "require-approval.json must exist before JSON validity can be tested"
    )
    content = json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        pytest.fail(f"require-approval.json is not valid JSON: {exc}")
    assert isinstance(data, (dict, list)), (
        "require-approval.json must be a JSON object or array"
    )


# ---------------------------------------------------------------------------
# No bytecode in template
# ---------------------------------------------------------------------------

def test_no_pyc_files_in_template():
    """No individual .pyc files must exist in templates/coding/."""
    pyc_files = list(_CODING_TEMPLATE.rglob("*.pyc"))
    assert len(pyc_files) == 0, (
        f".pyc files must not be bundled; found: {pyc_files}"
    )


def test_no_pyo_files_in_template():
    """No .pyo files (Python 2 optimised bytecode) must exist in templates/coding/."""
    pyo_files = list(_CODING_TEMPLATE.rglob("*.pyo"))
    assert len(pyo_files) == 0, (
        f".pyo files must not be bundled; found: {pyo_files}"
    )


# ---------------------------------------------------------------------------
# File content parity: Default-Project/ vs templates/coding/
# ---------------------------------------------------------------------------

def test_readme_content_matches_default_project():
    """templates/coding/README.md content must exactly match Default-Project/README.md."""
    template_file = _CODING_TEMPLATE / "README.md"
    source_file = _DEFAULT_PROJECT / "README.md"
    assert template_file.is_file(), "templates/coding/README.md must exist"
    assert source_file.is_file(), "Default-Project/README.md must exist"
    assert template_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
        "templates/coding/README.md differs from Default-Project/README.md"
    )


def test_gitignore_content_matches_default_project():
    """templates/coding/.gitignore content must exactly match Default-Project/.gitignore."""
    template_file = _CODING_TEMPLATE / ".gitignore"
    source_file = _DEFAULT_PROJECT / ".gitignore"
    assert template_file.is_file(), "templates/coding/.gitignore must exist"
    assert source_file.is_file(), "Default-Project/.gitignore must exist"
    assert template_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
        "templates/coding/.gitignore differs from Default-Project/.gitignore"
    )


def test_vscode_settings_content_matches_default_project():
    """.vscode/settings.json must match between template and Default-Project/."""
    template_file = _CODING_TEMPLATE / ".vscode" / "settings.json"
    source_file = _DEFAULT_PROJECT / ".vscode" / "settings.json"
    assert template_file.is_file(), "templates/coding/.vscode/settings.json must exist"
    assert source_file.is_file(), "Default-Project/.vscode/settings.json must exist"
    assert template_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
        ".vscode/settings.json differs between template and Default-Project/"
    )


def test_security_gate_content_matches_default_project():
    """security_gate.py must match between template and Default-Project/."""
    template_file = _CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py"
    source_file = _DEFAULT_PROJECT / ".github" / "hooks" / "scripts" / "security_gate.py"
    assert template_file.is_file(), "templates security_gate.py must exist"
    assert source_file.is_file(), "Default-Project security_gate.py must exist"
    assert template_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
        "security_gate.py differs between template and Default-Project/"
    )


def test_zone_classifier_content_matches_default_project():
    """zone_classifier.py must match between template and Default-Project/."""
    template_file = _CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    source_file = _DEFAULT_PROJECT / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    assert template_file.is_file(), "templates zone_classifier.py must exist"
    assert source_file.is_file(), "Default-Project zone_classifier.py must exist"
    assert template_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8"), (
        "zone_classifier.py differs between template and Default-Project/"
    )


# ---------------------------------------------------------------------------
# Template structural integrity
# ---------------------------------------------------------------------------

def test_coding_template_key_files_not_empty():
    """Safety-critical files must not be zero-byte placeholders."""
    key_files = [
        _CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py",
        _CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "zone_classifier.py",
        _CODING_TEMPLATE / ".vscode" / "settings.json",
        _CODING_TEMPLATE / ".github" / "hooks" / "require-approval.json",
        _CODING_TEMPLATE / ".github" / "instructions" / "copilot-instructions.md",
    ]
    for f in key_files:
        assert f.is_file(), f"{f.name} must exist"
        assert f.stat().st_size > 0, f"{f.name} must not be a zero-byte file"


def test_coding_template_has_no_symlinks():
    """No symlinks are allowed in templates/coding/ — they break cross-platform copies."""
    symlinks = [p for p in _CODING_TEMPLATE.rglob("*") if p.is_symlink()]
    assert len(symlinks) == 0, (
        f"Symlinks must not be present in the template: {symlinks}"
    )


def test_coding_skills_dir_exists():
    """templates/coding/.github/skills/ must exist."""
    assert (_CODING_TEMPLATE / ".github" / "skills").is_dir(), (
        "templates/coding/.github/skills/ must exist"
    )


def test_coding_prompts_dir_exists():
    """templates/coding/.github/prompts/ must exist."""
    assert (_CODING_TEMPLATE / ".github" / "prompts").is_dir(), (
        "templates/coding/.github/prompts/ must exist"
    )


def test_templates_root_contains_only_directories():
    """templates/ root must contain only subdirectories — no loose files."""
    for item in _TEMPLATES_ROOT.iterdir():
        assert item.is_dir(), (
            f"templates/ root must not contain files; found: {item.name}"
        )


# ---------------------------------------------------------------------------
# list_templates() additional edge cases
# (test-level import: informative failure when function is missing)
# ---------------------------------------------------------------------------

def test_list_templates_returns_sorted_results(tmp_path):
    """list_templates() must return directory names in sorted order."""
    try:
        from launcher.core.project_creator import list_templates
    except ImportError:
        pytest.fail(
            "list_templates() is not importable from launcher.core.project_creator. "
            "The function was never added to project_creator.py (INS-004 code change missing)."
        )
    (tmp_path / "zebra").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "mango").mkdir()
    result = list_templates(tmp_path)
    assert result == sorted(result), (
        f"list_templates() must return sorted names; got {result}"
    )
    assert result == ["alpha", "mango", "zebra"], (
        f"Expected ['alpha', 'mango', 'zebra'], got {result}"
    )


# ---------------------------------------------------------------------------
# config.TEMPLATES_DIR additional edge cases
# (test-level attribute access: informative failure when constant is missing)
# ---------------------------------------------------------------------------

def test_config_templates_dir_is_defined():
    """config.TEMPLATES_DIR must be defined, be a Path, and point to an existing dir."""
    from launcher import config
    if not hasattr(config, "TEMPLATES_DIR"):
        pytest.fail(
            "config.TEMPLATES_DIR is not defined in src/launcher/config.py. "
            "The constant was never added (INS-004 code change missing)."
        )
    from pathlib import Path as _Path
    assert isinstance(config.TEMPLATES_DIR, _Path), (
        "config.TEMPLATES_DIR must be a pathlib.Path instance"
    )
    assert config.TEMPLATES_DIR.is_dir(), (
        f"config.TEMPLATES_DIR must point to an existing directory; got {config.TEMPLATES_DIR}"
    )


def test_config_templates_dir_is_absolute():
    """config.TEMPLATES_DIR must be an absolute path, not a relative one."""
    from launcher import config
    if not hasattr(config, "TEMPLATES_DIR"):
        pytest.fail(
            "config.TEMPLATES_DIR is not defined — cannot verify it is absolute."
        )
    assert config.TEMPLATES_DIR.is_absolute(), (
        f"config.TEMPLATES_DIR must be absolute; got {config.TEMPLATES_DIR}"
    )
