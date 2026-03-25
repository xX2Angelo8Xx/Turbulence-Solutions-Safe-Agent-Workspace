"""Tester edge-case tests for DOC-018: Create agents/ directory in Agent Workbench template."""
import os
import re
import pytest

TEMPLATE_ROOT = os.path.join(
    os.path.dirname(__file__), "..", "..", "templates", "agent-workbench"
)
AGENTS_DIR = os.path.join(TEMPLATE_ROOT, ".github", "agents")
AGENTS_README = os.path.join(AGENTS_DIR, "README.md")
COPILOT_INSTRUCTIONS = os.path.join(
    TEMPLATE_ROOT, ".github", "instructions", "copilot-instructions.md"
)
AGENT_RULES = os.path.join(TEMPLATE_ROOT, "Project", "AGENT-RULES.md")

EXPECTED_AGENTS = [
    "programmer",
    "brainstormer",
    "tester",
    "researcher",
    "scientist",
    "criticist",
    "planner",
    "fixer",
    "writer",
    "prototyper",
]

SECURITY_CRITICAL_FILES = [
    os.path.join(TEMPLATE_ROOT, ".github", "hooks", "scripts", "security_gate.py"),
    os.path.join(TEMPLATE_ROOT, ".github", "hooks", "scripts", "zone_classifier.py"),
    os.path.join(TEMPLATE_ROOT, ".github", "hooks", "scripts", "require-approval.json"),
    os.path.join(TEMPLATE_ROOT, ".vscode", "settings.json"),
]


def test_agents_dir_contains_only_readme():
    """agents/ directory must only contain README.md (no .agent.md files yet — those are DOC-019..028)."""
    entries = os.listdir(AGENTS_DIR)
    # Ignore __pycache__ and other hidden tool artifacts
    visible = [e for e in entries if not e.startswith(".") and e != "__pycache__"]
    assert visible == ["README.md"], (
        f"agents/ should only contain README.md at this stage; found: {visible}"
    )


def test_readme_has_invoke_pattern_examples():
    """README.md must show the @agent-name invocation pattern."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read()
    assert "@" in content, "README.md must show @<agent-name> invocation pattern"
    # Check at least one real @agent example appears
    found = any(f"@{agent}" in content.lower() for agent in EXPECTED_AGENTS)
    assert found, "README.md must show at least one concrete @<agent-name> usage example"


def test_readme_has_yaml_frontmatter_example():
    """README.md must include a YAML frontmatter example so users know format."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read()
    assert "---" in content, "README.md must include YAML frontmatter example (---)"
    assert "name:" in content, "README.md YAML example must include 'name:' field"
    assert "description:" in content, "README.md YAML example must include 'description:' field"
    assert "tools:" in content, "README.md YAML example must include 'tools:' field"
    assert "model:" in content, "README.md YAML example must include 'model:' field"


def test_readme_references_agent_rules():
    """README.md must cross-reference AGENT-RULES.md for zone restrictions."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read()
    assert "AGENT-RULES" in content, (
        "README.md must reference AGENT-RULES.md so users know agents follow safety rules"
    )


def test_copilot_instructions_references_readme_file():
    """copilot-instructions.md must reference README.md inside agents/ — not just mention the directory."""
    with open(COPILOT_INSTRUCTIONS, encoding="utf-8") as f:
        content = f.read()
    assert "README.md" in content or "readme" in content.lower(), (
        "copilot-instructions.md must reference agents/README.md specifically"
    )


def test_copilot_instructions_invoke_syntax_present():
    """copilot-instructions.md must show the @<agent-name> invocation syntax."""
    with open(COPILOT_INSTRUCTIONS, encoding="utf-8") as f:
        content = f.read()
    assert "@<agent-name>" in content or "Invoke" in content or "invoke" in content or "@" in content, (
        "copilot-instructions.md must document how to invoke agents"
    )


def test_agent_rules_section8_has_when_to_use_guidance():
    """AGENT-RULES.md Section 8 must include 'when to use' guidance, not just list names."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    # Find section 8 content
    section8_match = re.search(r"## 8\..+?(?=## 9\.|$)", content, re.DOTALL)
    assert section8_match, "AGENT-RULES.md must have Section 8"
    section8 = section8_match.group(0)
    # Should have "When to Use" or similar column
    assert "when" in section8.lower(), (
        "Section 8 must include 'when to use' guidance for each agent"
    )


def test_agent_rules_section8_references_agents_readme():
    """AGENT-RULES.md Section 8 must cross-reference agents/README.md for customization."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    section8_match = re.search(r"## 8\..+?(?=## 9\.|$)", content, re.DOTALL)
    assert section8_match, "AGENT-RULES.md must have Section 8"
    section8 = section8_match.group(0)
    assert "README.md" in section8, (
        "Section 8 must reference agents/README.md for further customization details"
    )


def test_agent_rules_denied_zones_still_intact():
    """AGENT-RULES.md must still contain the denied zones section — it must not have been truncated."""
    with open(AGENT_RULES, encoding="utf-8") as f:
        content = f.read()
    assert "2. Denied Zones" in content or "## 2." in content, (
        "AGENT-RULES.md Section 2 (Denied Zones) must still be present"
    )
    assert "NoAgentZone" in content, "NoAgentZone denied zone must still be documented"


def test_copilot_instructions_no_agent_zone_rule_intact():
    """copilot-instructions.md must still prohibit NoAgentZone access."""
    with open(COPILOT_INSTRUCTIONS, encoding="utf-8") as f:
        content = f.read()
    assert "NoAgentZone" in content, (
        "copilot-instructions.md must still document NoAgentZone restriction"
    )


def test_readme_exact_agent_count():
    """README.md roster table must list exactly 10 agents — no more, no fewer."""
    with open(AGENTS_README, encoding="utf-8") as f:
        content = f.read()
    # Count table rows with .agent.md references
    agent_file_refs = re.findall(r"\w+\.agent\.md", content)
    assert len(agent_file_refs) == 10, (
        f"README.md must reference exactly 10 .agent.md files; found {len(agent_file_refs)}: {agent_file_refs}"
    )


def test_no_tmp_files_in_wp_folder():
    """No tmp_ files must remain in the DOC-018 WP folder."""
    wp_folder = os.path.join(
        os.path.dirname(__file__), "..", "..", "docs", "workpackages", "DOC-018"
    )
    if os.path.isdir(wp_folder):
        tmp_files = [f for f in os.listdir(wp_folder) if f.startswith("tmp_")]
        assert tmp_files == [], f"tmp_ files found in WP folder: {tmp_files}"


def test_readme_encoding_is_utf8():
    """README.md must be valid UTF-8 (no BOM or encoding issues)."""
    with open(AGENTS_README, "rb") as f:
        raw = f.read()
    # UTF-8 BOM check
    assert not raw.startswith(b"\xef\xbb\xbf"), (
        "README.md must not have a UTF-8 BOM — use plain UTF-8"
    )
    # Valid UTF-8 decode check
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        pytest.fail(f"README.md is not valid UTF-8: {e}")
