"""INS-004 — Template Bundling: comprehensive test suite.

Verifies that:
- templates/coding/ directory tree matches templates/coding/ (minus __pycache__)
- config.TEMPLATES_DIR constant exists, is a pathlib.Path, and resolves correctly
- project_creator.list_templates() is callable and returns correct results
- Integration: templates are discoverable and copyable at runtime
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

# Repository root used to locate well-known directories.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

TEMPLATES_DIR = REPO_ROOT / "templates"
CODING_TEMPLATE = TEMPLATES_DIR / "agent-workbench"

# ---------------------------------------------------------------------------
# 1. templates/ root
# ---------------------------------------------------------------------------


def test_templates_root_dir_exists():
    """templates/ directory must exist at the repository root."""
    assert TEMPLATES_DIR.is_dir(), f"Missing: {TEMPLATES_DIR}"


def test_coding_template_dir_exists():
    """templates/agent-workbench/ subdirectory must exist."""
    assert CODING_TEMPLATE.is_dir(), f"Missing: {CODING_TEMPLATE}"


# ---------------------------------------------------------------------------
# 2. Template file presence — top-level files
# ---------------------------------------------------------------------------


def test_coding_readme_exists():
    assert (CODING_TEMPLATE / "README.md").is_file()


def test_coding_gitignore_exists():
    assert (CODING_TEMPLATE / ".gitignore").is_file()


# ---------------------------------------------------------------------------
# 3. Template file presence — .github/
# ---------------------------------------------------------------------------


def test_coding_github_dir_exists():
    assert (CODING_TEMPLATE / ".github").is_dir()


def test_coding_hooks_json_exists():
    assert (CODING_TEMPLATE / ".github" / "hooks" / "require-approval.json").is_file()


def test_coding_hooks_scripts_security_gate_exists():
    assert (CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "security_gate.py").is_file()


def test_coding_hooks_scripts_zone_classifier_exists():
    assert (CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "zone_classifier.py").is_file()


def test_coding_hooks_scripts_ps1_exists():
    assert (CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "require-approval.ps1").is_file()


def test_coding_hooks_scripts_sh_exists():
    assert (CODING_TEMPLATE / ".github" / "hooks" / "scripts" / "require-approval.sh").is_file()


def test_coding_instructions_exists():
    assert (CODING_TEMPLATE / ".github" / "instructions" / "copilot-instructions.md").is_file()


def test_coding_prompts_review_exists():
    assert (CODING_TEMPLATE / ".github" / "prompts" / "review.prompt.md").is_file()


def test_coding_skill_exists():
    assert (CODING_TEMPLATE / ".github" / "skills" / "ts-code-review" / "SKILL.md").is_file()


# ---------------------------------------------------------------------------
# 4. Template file presence — .vscode/
# ---------------------------------------------------------------------------


def test_coding_vscode_dir_exists():
    assert (CODING_TEMPLATE / ".vscode").is_dir()


def test_coding_vscode_settings_exists():
    assert (CODING_TEMPLATE / ".vscode" / "settings.json").is_file()


# ---------------------------------------------------------------------------
# 5. Template file presence — NoAgentZone/ and Project/
# ---------------------------------------------------------------------------


def test_coding_noagentzone_dir_exists():
    assert (CODING_TEMPLATE / "NoAgentZone").is_dir()


def test_coding_noagentzone_readme_exists():
    assert (CODING_TEMPLATE / "NoAgentZone" / "README.md").is_file()


def test_coding_project_dir_exists():
    assert (CODING_TEMPLATE / "Project").is_dir()


def test_coding_project_app_exists():
    assert (CODING_TEMPLATE / "Project" / "app.py").is_file()


def test_coding_project_readme_exists():
    assert (CODING_TEMPLATE / "Project" / "README.md").is_file()


def test_coding_project_requirements_exists():
    assert (CODING_TEMPLATE / "Project" / "requirements.txt").is_file()


# ---------------------------------------------------------------------------
# 6. Quality guard — no __pycache__ in template
# ---------------------------------------------------------------------------


def test_no_pycache_in_template():
    """__pycache__ directories must not be bundled into the template."""
    pycache_dirs = [p for p in CODING_TEMPLATE.rglob("__pycache__") if p.is_dir()]
    assert pycache_dirs == [], f"Found __pycache__ in template: {pycache_dirs}"


def test_no_pyc_files_in_template():
    """*.pyc byte-cache files must not appear in the template tree."""
    pyc_files = list(CODING_TEMPLATE.rglob("*.pyc"))
    assert pyc_files == [], f"Found .pyc files in template: {pyc_files}"


# ---------------------------------------------------------------------------
# 7. config.TEMPLATES_DIR
# ---------------------------------------------------------------------------


def test_config_templates_dir_exists():
    """config.TEMPLATES_DIR attribute must be present after import."""
    from launcher import config  # type: ignore
    assert hasattr(config, "TEMPLATES_DIR"), "config.TEMPLATES_DIR is missing"


def test_config_templates_dir_is_path():
    from launcher import config  # type: ignore
    assert isinstance(config.TEMPLATES_DIR, Path), (
        f"Expected pathlib.Path, got {type(config.TEMPLATES_DIR)}"
    )


def test_config_templates_dir_resolves_to_templates():
    """TEMPLATES_DIR must resolve to the templates/ directory at the repo root."""
    from launcher import config  # type: ignore
    expected = (REPO_ROOT / "templates").resolve()
    actual = config.TEMPLATES_DIR.resolve()
    assert actual == expected, f"Expected {expected}, got {actual}"


def test_config_templates_dir_exists_on_disk():
    """The path pointed to by TEMPLATES_DIR must actually exist."""
    from launcher import config  # type: ignore
    assert config.TEMPLATES_DIR.is_dir(), (
        f"TEMPLATES_DIR path does not exist on disk: {config.TEMPLATES_DIR}"
    )


# ---------------------------------------------------------------------------
# 8. list_templates() — unit tests
# ---------------------------------------------------------------------------


def test_list_templates_function_exists():
    """list_templates must be importable from project_creator."""
    from launcher.core import project_creator  # type: ignore
    assert hasattr(project_creator, "list_templates"), (
        "list_templates() function is missing from project_creator"
    )


def test_list_templates_returns_coding():
    """list_templates(TEMPLATES_DIR) must include 'coding'."""
    from launcher.core.project_creator import list_templates  # type: ignore
    from launcher import config  # type: ignore
    result = list_templates(config.TEMPLATES_DIR)
    assert "agent-workbench" in result, f"'agent-workbench' not found in list_templates result: {result}"


def test_list_templates_returns_list():
    """list_templates() must return a list."""
    from launcher.core.project_creator import list_templates  # type: ignore
    from launcher import config  # type: ignore
    result = list_templates(config.TEMPLATES_DIR)
    assert isinstance(result, list), f"Expected list, got {type(result)}"


def test_list_templates_returns_sorted():
    """list_templates() output must be lexicographically sorted."""
    from launcher.core.project_creator import list_templates  # type: ignore
    from launcher import config  # type: ignore
    result = list_templates(config.TEMPLATES_DIR)
    assert result == sorted(result), "list_templates() result is not sorted"


def test_list_templates_empty_on_missing_dir():
    """list_templates() must return [] when the directory does not exist."""
    from launcher.core.project_creator import list_templates  # type: ignore
    result = list_templates(Path("/nonexistent/path/that/does/not/exist"))
    assert result == [], f"Expected [], got {result}"


def test_list_templates_excludes_files():
    """list_templates() must only return directory names, not files."""
    from launcher.core.project_creator import list_templates  # type: ignore
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "coding").mkdir()
        (tmp_path / "somefile.txt").touch()
        result = list_templates(tmp_path)
        assert "somefile.txt" not in result
        assert "coding" in result


def test_list_templates_with_multiple_templates():
    """list_templates() must return all template directories when multiple exist."""
    from launcher.core.project_creator import list_templates  # type: ignore
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "coding").mkdir()
        (tmp_path / "marketing").mkdir()
        result = list_templates(tmp_path)
        assert "coding" in result
        assert "marketing" in result
        assert len(result) == 2


def test_list_templates_empty_dir_returns_empty_list():
    """list_templates() on an empty but existing directory returns []."""
    from launcher.core.project_creator import list_templates  # type: ignore
    with tempfile.TemporaryDirectory() as tmp:
        result = list_templates(Path(tmp))
        assert result == []


# ---------------------------------------------------------------------------
# 9. Integration — template discoverable and copyable
# ---------------------------------------------------------------------------


def test_template_discoverable_and_copyable():
    """Integration: coding template is in list_templates() AND can be copied
    via create_project()."""
    from launcher.core.project_creator import list_templates, create_project  # type: ignore
    from launcher import config  # type: ignore

    templates = list_templates(config.TEMPLATES_DIR)
    assert "agent-workbench" in templates, "'coding' template not discoverable"

    coding_path = config.TEMPLATES_DIR / "agent-workbench"
    with tempfile.TemporaryDirectory() as tmp:
        result = create_project(coding_path, Path(tmp), "test-project")
        assert result.is_dir(), f"Copied project directory does not exist: {result}"
        assert result.name == "SAE-test-project"
        # Safety spot-checks: key files must propagate into the copy
        assert (result / ".vscode" / "settings.json").is_file()
        assert (result / ".github" / "hooks" / "require-approval.json").is_file()
        assert (result / ".github" / "hooks" / "scripts" / "security_gate.py").is_file()
        # GUI-016: 'Project/' is renamed to the user's project name after copytree.
        assert (result / "test-project" / "app.py").is_file()


# ---------------------------------------------------------------------------
# 10. Edge cases (Tester additions)
# ---------------------------------------------------------------------------


def test_template_files_match_default_project():
    """All files in templates/coding/ (minus __pycache__) must exist in templates/coding/."""
    default_project = REPO_ROOT / "templates" / "agent-workbench"
    if not default_project.is_dir():
        pytest.skip("templates/agent-workbench/ not found")

    missing = []
    for src_file in default_project.rglob("*"):
        if src_file.is_file() and "__pycache__" not in src_file.parts:
            relative = src_file.relative_to(default_project)
            target = CODING_TEMPLATE / relative
            if not target.is_file():
                missing.append(str(relative))

    assert missing == [], (
        f"Files present in templates/coding/ but missing from templates/coding/:\n"
        + "\n".join(f"  - {f}" for f in sorted(missing))
    )


def test_coding_template_has_no_extra_files_beyond_default_project():
    """templates/agent-workbench/ must not contain files absent from templates/coding/
    (prevents template drift / stale artifacts)."""
    default_project = REPO_ROOT / "templates" / "agent-workbench"
    if not default_project.is_dir():
        pytest.skip("templates/agent-workbench/ not found")

    extra = []
    for tmpl_file in CODING_TEMPLATE.rglob("*"):
        if tmpl_file.is_file() and "__pycache__" not in tmpl_file.parts:
            relative = tmpl_file.relative_to(CODING_TEMPLATE)
            source = default_project / relative
            if not source.is_file():
                extra.append(str(relative))

    assert extra == [], (
        f"Files in templates/coding/ that have no counterpart in templates/coding/:\n"
        + "\n".join(f"  - {f}" for f in sorted(extra))
    )


def test_list_templates_on_nonexistent_path_does_not_raise():
    """list_templates() must silently return [] on a missing path — no exception."""
    from launcher.core.project_creator import list_templates  # type: ignore
    try:
        result = list_templates(Path("/does/not/exist/at/all"))
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"list_templates raised unexpectedly: {exc}")
    assert result == []


def test_list_templates_on_file_path_returns_empty():
    """Passing a file path (not dir) to list_templates() must return []."""
    from launcher.core.project_creator import list_templates  # type: ignore
    with tempfile.NamedTemporaryFile() as tmp:
        result = list_templates(Path(tmp.name))
    assert result == []


# ---------------------------------------------------------------------------
# 11. Content-equality checks (Tester additions)
# ---------------------------------------------------------------------------


import json
import re as _re


def _strip_json_comments(text: str) -> str:
    """Strip JS-style line comments (// ...) from a JSONC string so it can be
    parsed as standard JSON.  Used to compare templates/coding settings files
    (which use JSONC comment syntax) with template files (clean JSON)."""
    return _re.sub(r"//[^\n]*", "", text)


def _load_json_ignoring_comments(path: Path) -> object:
    raw = path.read_text(encoding="utf-8")
    return json.loads(_strip_json_comments(raw))


def _key_security_files() -> list[str]:
    """Relative paths of the files with highest security importance."""
    return [
        ".github/hooks/require-approval.json",
        ".github/hooks/scripts/security_gate.py",
        ".github/hooks/scripts/zone_classifier.py",
        ".vscode/settings.json",
    ]


def test_template_security_files_match_default_project_content():
    """Key security files in templates/coding/ must have identical content to
    their counterparts in templates/coding/.

    For .json files, semantic equality is used (parsed JSON objects compared)
    so that differences in whitespace and JSONC-style comments do not cause
    false failures — templates/coding/ settings.json uses administrative
    comments for documentation while the template carries clean JSON.
    For all other files a byte-for-byte comparison is performed.
    """
    default_project = REPO_ROOT / "templates" / "agent-workbench"
    if not default_project.is_dir():
        pytest.skip("templates/agent-workbench/ not found")

    mismatches = []
    for rel in _key_security_files():
        src = default_project / rel
        dst = CODING_TEMPLATE / rel
        if src.is_file() and dst.is_file():
            if rel.endswith(".json"):
                if _load_json_ignoring_comments(src) != _load_json_ignoring_comments(dst):
                    mismatches.append(rel)
            else:
                if src.read_bytes() != dst.read_bytes():
                    mismatches.append(rel)
        elif not src.is_file():
            mismatches.append(f"MISSING in templates/coding/: {rel}")
        else:
            mismatches.append(f"MISSING in templates/coding/: {rel}")

    assert mismatches == [], (
        "Content mismatch between templates/coding/ and templates/coding/ for:\n"
        + "\n".join(f"  - {m}" for m in mismatches)
    )


def test_vscode_settings_json_has_all_required_keys():
    """templates/agent-workbench/.vscode/settings.json must contain every security-
    critical key present in templates/coding/.vscode/settings.json.

    This test is intentionally more lenient than a byte-for-byte comparison:
    templates/coding/ uses JSONC comment syntax for documentation; the template
    carries clean JSON.  What matters is that no security control is absent.
    """
    default_project = REPO_ROOT / "templates" / "agent-workbench"
    if not default_project.is_dir():
        pytest.skip("templates/agent-workbench/ not found")

    src_parsed = _load_json_ignoring_comments(
        default_project / ".vscode" / "settings.json"
    )
    dst_parsed = _load_json_ignoring_comments(
        CODING_TEMPLATE / ".vscode" / "settings.json"
    )

    assert isinstance(src_parsed, dict) and isinstance(dst_parsed, dict)
    missing_keys = [k for k in src_parsed if k not in dst_parsed]
    assert missing_keys == [], (
        "Security settings missing from templates/coding/.vscode/settings.json:\n"
        + "\n".join(f"  - {k}" for k in missing_keys)
    )

    # Spot-check the most critical safety controls have the correct values.
    critical = {
        "chat.tools.global.autoApprove": False,
        "github.copilot.chat.agent.autoFix": False,
        "chat.mcp.autoStart": False,
        "security.workspace.trust.enabled": True,
    }
    wrong_values = {
        k: dst_parsed.get(k)
        for k, expected in critical.items()
        if dst_parsed.get(k) != expected
    }
    assert wrong_values == {}, (
        "Critical security settings have wrong values in template settings.json:\n"
        + "\n".join(f"  - {k}: got {v}" for k, v in wrong_values.items())
    )


def test_template_files_are_non_empty():
    """Every file inside templates/coding/ must have at least 1 byte of content
    — empty placeholder files must not be bundled."""
    empty = [
        str(p.relative_to(CODING_TEMPLATE))
        for p in CODING_TEMPLATE.rglob("*")
        if p.is_file() and p.stat().st_size == 0
    ]
    assert empty == [], (
        "Empty (zero-byte) files found in templates/coding/:\n"
        + "\n".join(f"  - {e}" for e in sorted(empty))
    )


def test_list_templates_wrong_type_returns_empty():
    """Passing a non-Path argument (e.g. a string) to list_templates() must
    return [] without raising — guards the isinstance() check."""
    from launcher.core.project_creator import list_templates  # type: ignore
    result = list_templates("not_a_path")  # type: ignore[arg-type]
    assert result == [], f"Expected [], got {result}"


def test_template_non_json_files_match_default_project_byte_for_byte():
    """All non-JSON files in templates/coding/ must be byte-for-byte identical
    to their templates/coding/ counterparts.

    JSON files are excluded because templates/coding/ uses JSONC comment syntax
    while the template ships clean JSON — semantic equality is verified by
    test_template_security_files_match_default_project_content instead.
    """
    default_project = REPO_ROOT / "templates" / "agent-workbench"
    if not default_project.is_dir():
        pytest.skip("templates/agent-workbench/ not found")

    mismatches: list[str] = []
    for tmpl_file in CODING_TEMPLATE.rglob("*"):
        if not tmpl_file.is_file():
            continue
        if tmpl_file.suffix.lower() == ".json":
            continue  # compared semantically in other tests
        rel = tmpl_file.relative_to(CODING_TEMPLATE)
        src = default_project / rel
        if src.is_file() and src.read_bytes() != tmpl_file.read_bytes():
            mismatches.append(str(rel))

    assert mismatches == [], (
        "Non-JSON content mismatch between templates/coding/ and templates/coding/:\n"
        + "\n".join(f"  - {m}" for m in sorted(mismatches))
    )


def test_require_approval_json_is_valid_json():
    """require-approval.json in the template must contain valid JSON."""
    import json
    json_path = CODING_TEMPLATE / ".github" / "hooks" / "require-approval.json"
    if not json_path.is_file():
        pytest.skip("require-approval.json missing — covered by existence test")
    with open(json_path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            pytest.fail(f"require-approval.json is not valid JSON: {exc}")
    assert isinstance(data, dict), "require-approval.json root must be a JSON object"


def test_vscode_settings_json_is_valid_json():
    """.vscode/settings.json in the template must contain valid JSON."""
    import json
    settings_path = CODING_TEMPLATE / ".vscode" / "settings.json"
    if not settings_path.is_file():
        pytest.skip(".vscode/settings.json missing — covered by existence test")
    with open(settings_path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as exc:
            pytest.fail(f".vscode/settings.json is not valid JSON: {exc}")
    assert isinstance(data, dict), ".vscode/settings.json root must be a JSON object"


def test_template_copy_preserves_hidden_directories():
    """When the template is copied, hidden directories (.github, .vscode) must
    be present in the destination — shutil.copytree must not strip them."""
    from launcher.core.project_creator import list_templates, create_project  # type: ignore
    from launcher import config  # type: ignore

    templates = list_templates(config.TEMPLATES_DIR)
    if "coding" not in templates:
        pytest.skip("coding template not available — covered by discovery test")

    coding_path = config.TEMPLATES_DIR / "agent-workbench"
    with tempfile.TemporaryDirectory() as tmp:
        result = create_project(coding_path, Path(tmp), "hidden-dir-test")
        assert (result / ".github").is_dir(), ".github not copied to destination"
        assert (result / ".vscode").is_dir(), ".vscode not copied to destination"
