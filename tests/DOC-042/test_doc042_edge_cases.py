"""
DOC-042: Edge-case tests for agent default model and tools settings.
Tester-added tests covering YAML validity, placeholder presence,
empty-field guards, and model exclusivity.
"""
import pathlib
import re

import yaml

AGENTS_DIR = (
    pathlib.Path(__file__).parent.parent.parent
    / "templates"
    / "agent-workbench"
    / ".github"
    / "agents"
)

AGENT_NAMES = [
    "brainstormer",
    "coordinator",
    "planner",
    "programmer",
    "researcher",
    "tester",
    "tidyup",
]

AGENT_FILES = {name: AGENTS_DIR / f"{name}.agent.md" for name in AGENT_NAMES}

SONNET_AGENTS = ["brainstormer", "coordinator", "programmer", "researcher", "tester", "tidyup"]
OPUS_AGENTS = ["planner"]


def _read_content(agent_name: str) -> str:
    return AGENT_FILES[agent_name].read_text(encoding="utf-8")


def _extract_frontmatter_text(agent_name: str) -> str:
    content = _read_content(agent_name)
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match, f"{agent_name}.agent.md: YAML frontmatter delimiters not found"
    return match.group(1)


def _parse_frontmatter(agent_name: str) -> dict:
    fm_text = _extract_frontmatter_text(agent_name)
    return yaml.safe_load(fm_text)


def _read_body(agent_name: str) -> str:
    """Return content after second --- delimiter."""
    content = _read_content(agent_name)
    match = re.match(r"^---\n.*?\n---\n(.*)", content, re.DOTALL)
    assert match, f"{agent_name}.agent.md: body not found after frontmatter"
    return match.group(1)


# ── YAML validity ─────────────────────────────────────────────────────────────

def test_brainstormer_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("brainstormer")


def test_coordinator_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("coordinator")


def test_planner_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("planner")


def test_programmer_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("programmer")


def test_researcher_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("researcher")


def test_tester_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("tester")


def test_tidyup_frontmatter_is_valid_yaml():
    """Frontmatter must parse without error."""
    _parse_frontmatter("tidyup")


# ── Required YAML keys present ────────────────────────────────────────────────

def test_all_agents_have_required_yaml_keys():
    """Each agent must have name, description, tools, and model fields."""
    required_keys = {"name", "description", "tools", "model"}
    for agent_name in AGENT_NAMES:
        try:
            fm = _parse_frontmatter(agent_name)
        except Exception as e:
            raise AssertionError(
                f"{agent_name}.agent.md: YAML parse failure prevents key check: {e}"
            )
        missing = required_keys - set(fm.keys())
        assert not missing, (
            f"{agent_name}.agent.md missing required YAML key(s): {missing}"
        )


# ── Non-empty fields ──────────────────────────────────────────────────────────

def test_no_agent_has_empty_tools():
    """tools field must be a non-empty list."""
    for agent_name in AGENT_NAMES:
        try:
            fm = _parse_frontmatter(agent_name)
        except Exception as e:
            raise AssertionError(
                f"{agent_name}.agent.md: YAML parse failure prevents tools check: {e}"
            )
        tools = fm.get("tools")
        assert tools, (
            f"{agent_name}.agent.md: tools field is empty or missing"
        )
        assert isinstance(tools, list), (
            f"{agent_name}.agent.md: tools field must be a list, got {type(tools)}"
        )
        assert len(tools) > 0, (
            f"{agent_name}.agent.md: tools list must not be empty"
        )


def test_no_agent_has_empty_model():
    """model field must be a non-empty value."""
    for agent_name in AGENT_NAMES:
        try:
            fm = _parse_frontmatter(agent_name)
        except Exception as e:
            raise AssertionError(
                f"{agent_name}.agent.md: YAML parse failure prevents model check: {e}"
            )
        model = fm.get("model")
        assert model, (
            f"{agent_name}.agent.md: model field is empty or missing"
        )


def test_no_agent_has_empty_name():
    """name field must be a non-empty string."""
    for agent_name in AGENT_NAMES:
        try:
            fm = _parse_frontmatter(agent_name)
        except Exception as e:
            raise AssertionError(
                f"{agent_name}.agent.md: YAML parse failure prevents name check: {e}"
            )
        name = fm.get("name")
        assert name and str(name).strip(), (
            f"{agent_name}.agent.md: name field is empty or missing"
        )


# ── Model exclusivity ─────────────────────────────────────────────────────────

def test_planner_is_only_opus_agent():
    """Only planner may use Opus; every other agent must use Sonnet."""
    for agent_name in AGENT_NAMES:
        try:
            fm = _parse_frontmatter(agent_name)
        except Exception as e:
            raise AssertionError(
                f"{agent_name}.agent.md: YAML parse failure: {e}"
            )
        model_val = str(fm.get("model", ""))
        if agent_name in OPUS_AGENTS:
            assert "Opus" in model_val, (
                f"{agent_name}.agent.md should use Opus, got: {model_val}"
            )
        else:
            assert "Opus" not in model_val, (
                f"{agent_name}.agent.md must NOT use Opus, got: {model_val}"
            )
            assert "Sonnet" in model_val, (
                f"{agent_name}.agent.md must use Sonnet, got: {model_val}"
            )


# ── Template placeholder preservation ─────────────────────────────────────────

def test_brainstormer_has_project_name_placeholder():
    """Body must still contain {{PROJECT_NAME}} template variable."""
    body = _read_body("brainstormer")
    assert "{{PROJECT_NAME}}" in body, (
        "brainstormer.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_coordinator_has_project_name_placeholder():
    body = _read_body("coordinator")
    assert "{{PROJECT_NAME}}" in body, (
        "coordinator.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_planner_has_project_name_placeholder():
    body = _read_body("planner")
    assert "{{PROJECT_NAME}}" in body, (
        "planner.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_programmer_has_project_name_placeholder():
    body = _read_body("programmer")
    assert "{{PROJECT_NAME}}" in body, (
        "programmer.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_researcher_has_project_name_placeholder():
    body = _read_body("researcher")
    assert "{{PROJECT_NAME}}" in body, (
        "researcher.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_tester_has_project_name_placeholder():
    body = _read_body("tester")
    assert "{{PROJECT_NAME}}" in body, (
        "tester.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


def test_tidyup_has_project_name_placeholder():
    body = _read_body("tidyup")
    assert "{{PROJECT_NAME}}" in body, (
        "tidyup.agent.md: {{PROJECT_NAME}} placeholder missing from body"
    )


# ── Frontmatter structure ─────────────────────────────────────────────────────

def test_all_files_start_with_yaml_delimiter():
    """Every agent file must begin with --- (YAML frontmatter open)."""
    for agent_name in AGENT_NAMES:
        content = _read_content(agent_name)
        assert content.startswith("---\n"), (
            f"{agent_name}.agent.md does not start with YAML frontmatter delimiter ---"
        )


def test_all_files_have_closing_yaml_delimiter():
    """Every agent file must have a second --- after the opening."""
    for agent_name in AGENT_NAMES:
        content = _read_content(agent_name)
        # Must have at least two --- lines
        matches = list(re.finditer(r"^---$", content, re.MULTILINE))
        assert len(matches) >= 2, (
            f"{agent_name}.agent.md: fewer than two --- delimiters found "
            f"(frontmatter not properly closed)"
        )
