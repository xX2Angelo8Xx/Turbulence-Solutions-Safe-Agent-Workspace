"""DOC-037: Verify structured prompt files are correctly created."""

import pathlib

TEMPLATE_PROMPTS = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "prompts"

EXPECTED_PROMPTS = ["critical-review", "prototype", "root-cause-analysis"]


def test_expected_prompts_exist():
    for name in EXPECTED_PROMPTS:
        path = TEMPLATE_PROMPTS / f"{name}.prompt.md"
        assert path.exists(), f"Missing prompt file: {path}"


def test_prompts_have_frontmatter():
    for name in EXPECTED_PROMPTS:
        path = TEMPLATE_PROMPTS / f"{name}.prompt.md"
        content = path.read_text(encoding="utf-8")
        parts = content.split("---")
        assert len(parts) >= 3, f"{path.name} missing YAML frontmatter"
        assert "description" in parts[1], f"{path.name} frontmatter missing description"


def test_prompts_have_three_phases():
    for name in EXPECTED_PROMPTS:
        path = TEMPLATE_PROMPTS / f"{name}.prompt.md"
        content = path.read_text(encoding="utf-8")
        assert "Phase 1" in content, f"{path.name} missing Phase 1"
        assert "Phase 2" in content, f"{path.name} missing Phase 2"
        assert "Phase 3" in content, f"{path.name} missing Phase 3"


def test_prompts_have_output_format():
    for name in EXPECTED_PROMPTS:
        path = TEMPLATE_PROMPTS / f"{name}.prompt.md"
        content = path.read_text(encoding="utf-8")
        assert "Output Format" in content, f"{path.name} missing Output Format section"


def test_debug_workspace_prompt_unchanged():
    path = TEMPLATE_PROMPTS / "debug-workspace.prompt.md"
    assert path.exists(), "debug-workspace.prompt.md should still exist"
    content = path.read_text(encoding="utf-8")
    assert "Workspace Debug" in content or "Debug" in content, "debug-workspace content looks wrong"
