"""GUI-023 — Tester edge-case tests for template rename.

Supplements the Developer's 16 baseline tests with:
- Format function boundary / adversarial inputs
- list_templates() with non-directory entries in templates/
- is_template_ready() edge cases (empty dir, single README, deeply nested)
- Security-critical file presence verification
- No old names in source code
- launcher.spec bundles templates/ generically
- certification-pipeline has exactly one entry (README.md)
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"

sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher.gui.app import _format_template_name
from launcher.core.project_creator import list_templates, is_template_ready


# ---------------------------------------------------------------------------
# _format_template_name() — boundary / adversarial inputs
# ---------------------------------------------------------------------------

def test_format_empty_string():
    """Empty string input should return empty string (no crash)."""
    result = _format_template_name("")
    assert result == ""


def test_format_single_word():
    """Single word without separators should be title-cased."""
    assert _format_template_name("coding") == "Coding"


def test_format_underscore_separated():
    """Underscore separators should be treated like hyphens."""
    assert _format_template_name("agent_workbench") == "Agent Workbench"


def test_format_mixed_separators():
    """Mixed separators are all replaced with spaces."""
    result = _format_template_name("agent-work_bench")
    assert result == "Agent Work Bench"


def test_format_already_title_case():
    """Already title-cased input should remain unchanged."""
    assert _format_template_name("Agent-Workbench") == "Agent Workbench"


def test_format_triple_hyphen():
    """Three hyphens produce three spaces, resulting in correct title case."""
    result = _format_template_name("a-b-c")
    assert result == "A B C"


# ---------------------------------------------------------------------------
# list_templates() — robustness with non-directory entries
# ---------------------------------------------------------------------------

def test_list_templates_ignores_files(tmp_path):
    """Regular files in the templates root must NOT appear in the list."""
    (tmp_path / "agent-workbench").mkdir()
    (tmp_path / "not-a-template.txt").write_text("noise", encoding="utf-8")
    names = list_templates(tmp_path)
    assert "agent-workbench" in names
    assert "not-a-template.txt" not in names


def test_list_templates_empty_dir_returns_empty(tmp_path):
    """An empty templates directory returns []."""
    assert list_templates(tmp_path) == []


def test_list_templates_nonexistent_path():
    """A non-existent path returns [] without raising."""
    bogus = REPO_ROOT / "templates_does_not_exist_xyz"
    assert list_templates(bogus) == []


def test_list_templates_not_a_path_object():
    """Passing a non-Path object (e.g. str) returns [] without crashing."""
    result = list_templates("templates")  # str, not Path
    assert result == []


def test_list_templates_real_count():
    """Exactly two template directories should exist after the rename."""
    names = list_templates(TEMPLATES_DIR)
    assert len(names) == 2, f"Expected 2 templates, found {len(names)}: {names}"


# ---------------------------------------------------------------------------
# is_template_ready() — edge cases
# ---------------------------------------------------------------------------

def test_is_template_ready_empty_dir(tmp_path):
    """Completely empty template directory is NOT ready."""
    empty = tmp_path / "empty-template"
    empty.mkdir()
    assert is_template_ready(tmp_path, "empty-template") is False


def test_is_template_ready_readme_only(tmp_path):
    """Template with only README.md is NOT ready."""
    t = tmp_path / "readme-only"
    t.mkdir()
    (t / "README.md").write_text("# Coming soon", encoding="utf-8")
    assert is_template_ready(tmp_path, "readme-only") is False


def test_is_template_ready_one_non_readme_file(tmp_path):
    """A single non-README file makes the template ready."""
    t = tmp_path / "minimal"
    t.mkdir()
    (t / "something.py").write_text("# code", encoding="utf-8")
    assert is_template_ready(tmp_path, "minimal") is True


def test_is_template_ready_readme_plus_one_file(tmp_path):
    """README + one additional file = ready."""
    t = tmp_path / "partial"
    t.mkdir()
    (t / "README.md").write_text("# doc", encoding="utf-8")
    (t / "config.json").write_text("{}", encoding="utf-8")
    assert is_template_ready(tmp_path, "partial") is True


# ---------------------------------------------------------------------------
# Security-critical file presence
# ---------------------------------------------------------------------------

def test_security_gate_py_exists():
    """security_gate.py must be present in agent-workbench hooks."""
    sg = TEMPLATES_DIR / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
    assert sg.is_file(), f"Missing security-critical file: {sg}"


def test_zone_classifier_py_exists():
    """zone_classifier.py must be present in agent-workbench hooks."""
    zc = TEMPLATES_DIR / "agent-workbench" / ".github" / "hooks" / "scripts" / "zone_classifier.py"
    assert zc.is_file(), f"Missing security-critical file: {zc}"


def test_require_approval_json_exists():
    """require-approval.json must be present (the hook config)."""
    ra = TEMPLATES_DIR / "agent-workbench" / ".github" / "hooks" / "require-approval.json"
    assert ra.is_file(), f"Missing hook config: {ra}"


def test_agent_workbench_vscode_settings_exist():
    """The .vscode/settings.json file must be preserved."""
    vs = TEMPLATES_DIR / "agent-workbench" / ".vscode" / "settings.json"
    assert vs.is_file(), f"Missing VS Code settings: {vs}"


def test_agent_workbench_gitignore_exists():
    """.gitignore must be preserved in agent-workbench."""
    gi = TEMPLATES_DIR / "agent-workbench" / ".gitignore"
    assert gi.is_file(), f"Missing .gitignore: {gi}"


# ---------------------------------------------------------------------------
# certification-pipeline sanity
# ---------------------------------------------------------------------------

def test_certification_pipeline_has_readme():
    """certification-pipeline must contain README.md."""
    readme = TEMPLATES_DIR / "certification-pipeline" / "README.md"
    assert readme.is_file(), "certification-pipeline/README.md must exist"


def test_certification_pipeline_readme_content():
    """certification-pipeline README must mention 'Certification Pipeline'."""
    readme = TEMPLATES_DIR / "certification-pipeline" / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "Certification Pipeline" in content


def test_certification_pipeline_only_has_readme():
    """certification-pipeline must have ONLY README.md (not yet populated)."""
    items = list((TEMPLATES_DIR / "certification-pipeline").iterdir())
    names = [i.name for i in items]
    assert names == ["README.md"], (
        f"certification-pipeline should contain only README.md, found: {names}"
    )


# ---------------------------------------------------------------------------
# No broken references to old names in source code
# ---------------------------------------------------------------------------

def test_src_no_reference_to_templates_coding():
    """src/ must not reference templates/coding."""
    src_dir = REPO_ROOT / "src"
    bad_refs = []
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "templates/coding" in text or "templates\\coding" in text:
            bad_refs.append(str(py_file))
    assert not bad_refs, f"Broken references to templates/coding found in: {bad_refs}"


def test_src_no_reference_to_creative_marketing():
    """src/ must not reference creative-marketing."""
    src_dir = REPO_ROOT / "src"
    bad_refs = []
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "creative-marketing" in text or "creative_marketing" in text:
            bad_refs.append(str(py_file))
    assert not bad_refs, f"Broken references to creative-marketing found in: {bad_refs}"


# ---------------------------------------------------------------------------
# launcher.spec — generic templates/ bundling
# ---------------------------------------------------------------------------

def test_launcher_spec_bundles_templates_generically():
    """launcher.spec must bundle templates/ without naming specific subdirs."""
    spec = REPO_ROOT / "launcher.spec"
    text = spec.read_text(encoding="utf-8")
    # Must contain the generic templates bundle line
    assert "'templates'" in text or '"templates"' in text, \
        "launcher.spec must bundle the templates directory"
    # Must NOT hard-code old template names
    assert "templates/coding" not in text, \
        "launcher.spec must not reference templates/coding"
    assert "creative-marketing" not in text, \
        "launcher.spec must not reference creative-marketing"
