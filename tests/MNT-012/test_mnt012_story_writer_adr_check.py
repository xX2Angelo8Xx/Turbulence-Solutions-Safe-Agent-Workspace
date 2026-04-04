"""
MNT-012: Story Writer ADR Check
Tests that story-writer.agent.md contains the ADR index read step and the
ADR contradiction checklist item.
"""

import pathlib

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "story-writer.agent.md"


def _content() -> str:
    return AGENT_FILE.read_text(encoding="utf-8")


def test_agent_file_exists():
    assert AGENT_FILE.exists(), "story-writer.agent.md must exist"


def test_startup_has_adr_step():
    content = _content()
    assert "docs/decisions/index.jsonl" in content, (
        "Startup section must reference docs/decisions/index.jsonl"
    )


def test_startup_adr_step_number():
    content = _content()
    # Step 4 must appear in the Startup block before the Workflow section
    startup_section = content.split("## Workflow")[0]
    assert "4." in startup_section, (
        "Step 4 must be present in the Startup section"
    )


def test_startup_adr_step_mentions_conflict_check():
    content = _content()
    startup_section = content.split("## Workflow")[0]
    assert "conflict" in startup_section.lower() or "contradict" in startup_section.lower(), (
        "Step 4 must mention conflict or contradiction checking"
    )


def test_quality_checklist_has_adr_item():
    content = _content()
    assert "No contradiction with existing ADRs" in content, (
        "Quality checklist must contain 'No contradiction with existing ADRs'"
    )


def test_quality_checklist_adr_item_references_index():
    content = _content()
    # The checklist item should also reference decisions/index.jsonl
    assert "decisions/index.jsonl" in content, (
        "Quality checklist ADR item must reference docs/decisions/index.jsonl"
    )


def test_adr_checklist_item_is_checkbox():
    content = _content()
    # Find the line and confirm it is a checklist item
    for line in content.splitlines():
        if "No contradiction with existing ADRs" in line:
            assert line.strip().startswith("- [ ]"), (
                "ADR checklist item must use '- [ ]' format"
            )
            break
    else:
        raise AssertionError("ADR checklist item not found in file")


def test_startup_step_order():
    """Step 4 (ADR check) must come after step 3 (user-stories.jsonl read)."""
    content = _content()
    startup_section = content.split("## Workflow")[0]
    pos_step3 = startup_section.find("user-stories/user-stories.jsonl")
    pos_step4 = startup_section.find("docs/decisions/index.jsonl")
    assert pos_step3 != -1, "Step 3 reference to user-stories.jsonl not found"
    assert pos_step4 != -1, "Step 4 reference to decisions/index.jsonl not found"
    assert pos_step3 < pos_step4, (
        "Step 3 (user-stories.jsonl) must appear before step 4 (decisions/index.jsonl)"
    )


def test_front_matter_present():
    content = _content()
    assert content.startswith("---"), "story-writer.agent.md must have YAML front-matter"
    assert "name: story-writer" in content, (
        "Front-matter must contain 'name: story-writer'"
    )
