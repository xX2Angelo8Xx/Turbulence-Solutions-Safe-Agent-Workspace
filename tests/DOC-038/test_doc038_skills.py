"""DOC-038: Verify skills replacement — ts-code-review removed, new skills created."""

import pathlib

SKILLS_DIR = pathlib.Path(__file__).resolve().parents[2] / "templates" / "agent-workbench" / ".github" / "skills"


def test_ts_code_review_deleted():
    assert not (SKILLS_DIR / "ts-code-review").exists(), "ts-code-review should be deleted"


def test_agentdocs_update_skill_exists():
    path = SKILLS_DIR / "agentdocs-update" / "SKILL.md"
    assert path.exists()


def test_safety_critical_skill_exists():
    path = SKILLS_DIR / "safety-critical" / "SKILL.md"
    assert path.exists()


def test_agentdocs_update_has_frontmatter():
    content = (SKILLS_DIR / "agentdocs-update" / "SKILL.md").read_text(encoding="utf-8")
    parts = content.split("---")
    assert len(parts) >= 3
    assert "agentdocs-update" in parts[1]


def test_safety_critical_has_frontmatter():
    content = (SKILLS_DIR / "safety-critical" / "SKILL.md").read_text(encoding="utf-8")
    parts = content.split("---")
    assert len(parts) >= 3
    assert "safety-critical" in parts[1]


def test_agentdocs_update_references_agentdocs():
    content = (SKILLS_DIR / "agentdocs-update" / "SKILL.md").read_text(encoding="utf-8")
    assert "AgentDocs" in content


def test_safety_critical_references_decisions():
    content = (SKILLS_DIR / "safety-critical" / "SKILL.md").read_text(encoding="utf-8")
    assert "decisions.md" in content


def test_safety_critical_has_checklist():
    content = (SKILLS_DIR / "safety-critical" / "SKILL.md").read_text(encoding="utf-8")
    assert "Checklist" in content
    assert "Fail Safe" in content or "Fail safe" in content or "fail safe" in content
