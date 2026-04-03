"""
MNT-008: Tester edge-case tests added by Tester Agent.
Covers programmatic YAML parsing, escalation count reference, and handoff label.
"""
import re
import pathlib
import yaml

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "tester.agent.md"


def _raw_frontmatter() -> str:
    content = AGENT_FILE.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, "tester.agent.md does not contain valid YAML frontmatter"
    return match.group(1)


def _parsed_frontmatter() -> dict:
    raw = _raw_frontmatter()
    data = yaml.safe_load(raw)
    assert isinstance(data, dict), "YAML frontmatter did not parse to a dict"
    return data


def test_yaml_frontmatter_is_valid():
    """YAML frontmatter must parse without errors using yaml.safe_load."""
    data = _parsed_frontmatter()
    assert data is not None


def test_yaml_agents_is_list():
    """agents: field must be a list (not a scalar or mapping)."""
    data = _parsed_frontmatter()
    assert isinstance(data.get("agents"), list), (
        f"agents: must be a list, got {type(data.get('agents'))}"
    )


def test_yaml_handoffs_is_list():
    """handoffs: field must be a list of entries."""
    data = _parsed_frontmatter()
    assert isinstance(data.get("handoffs"), list), (
        f"handoffs: must be a list, got {type(data.get('handoffs'))}"
    )
    assert len(data["handoffs"]) >= 1, "handoffs: list must have at least one entry"


def test_handoff_entry_has_label():
    """Each handoff entry must have a non-empty label field."""
    data = _parsed_frontmatter()
    handoffs = data.get("handoffs", [])
    for i, handoff in enumerate(handoffs):
        assert isinstance(handoff, dict), f"handoffs[{i}] is not a dict"
        assert "label" in handoff, f"handoffs[{i}] is missing 'label'"
        assert handoff["label"].strip(), f"handoffs[{i}] label is empty"


def test_handoff_agent_matches_agents_list():
    """The handoff agent must be listed in the top-level agents: field."""
    data = _parsed_frontmatter()
    agents = data.get("agents", [])
    for i, handoff in enumerate(data.get("handoffs", [])):
        agent = handoff.get("agent", "")
        assert agent in agents, (
            f"handoffs[{i}].agent '{agent}' is not listed in agents: {agents}"
        )


def test_handoff_prompt_references_3_failures():
    """The escalation prompt must explicitly mention '3' failed iterations."""
    data = _parsed_frontmatter()
    handoffs = data.get("handoffs", [])
    assert handoffs, "handoffs: is empty"
    prompt = handoffs[0].get("prompt", "")
    assert "3" in prompt, (
        "Escalation handoff prompt must reference '3' failed iterations "
        f"(the cap from agent-workflow.md). Got: {prompt!r}"
    )


def test_handoff_prompt_references_agent_workflow():
    """The escalation prompt must reference agent-workflow.md or its rules."""
    data = _parsed_frontmatter()
    prompt = data["handoffs"][0].get("prompt", "")
    assert "agent-workflow" in prompt.lower() or "iteration cap" in prompt.lower(), (
        "Escalation prompt should reference agent-workflow.md or the iteration cap rule"
    )


def test_name_field_is_tester():
    """The name: field in frontmatter must be 'tester'."""
    data = _parsed_frontmatter()
    assert data.get("name") == "tester", (
        f"Expected name: tester, got: {data.get('name')!r}"
    )
