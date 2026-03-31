"""
DOC-044: Edge-case tests for the Tidyup → Workspace-Cleaner rename.
Tester-authored — covers YAML parsability, field presence, placeholder integrity,
coordinator agent list completeness, and full case-insensitive tidyup scan.
"""

import re
import yaml
from pathlib import Path

AGENTS_DIR = Path(__file__).parents[2] / "templates" / "agent-workbench" / ".github" / "agents"
CLEANER_FILE = AGENTS_DIR / "workspace-cleaner.agent.md"
COORDINATOR_FILE = AGENTS_DIR / "coordinator.agent.md"
AGENT_RULES_FILE = (
    Path(__file__).parents[2]
    / "templates" / "agent-workbench" / "Project" / "AGENT-RULES.md"
)
TEMPLATE_ROOT = Path(__file__).parents[2] / "templates" / "agent-workbench"

# Expected set of agents in the coordinator
EXPECTED_AGENTS = {"Programmer", "Tester", "Brainstormer", "Researcher", "Planner", "Workspace-Cleaner"}


def _extract_frontmatter(text: str) -> dict:
    """Extract and parse YAML frontmatter between the first two '---' lines."""
    lines = text.splitlines()
    if lines[0].strip() != "---":
        raise ValueError("Frontmatter does not start with '---'")
    end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
    yaml_block = "\n".join(lines[1:end])
    return yaml.safe_load(yaml_block)


# ---------------------------------------------------------------------------
# YAML parsability
# ---------------------------------------------------------------------------

def test_workspace_cleaner_frontmatter_is_valid_yaml():
    """workspace-cleaner.agent.md frontmatter must parse as valid YAML."""
    content = CLEANER_FILE.read_text(encoding="utf-8")
    try:
        fm = _extract_frontmatter(content)
    except Exception as exc:
        raise AssertionError(f"YAML frontmatter parse failed: {exc}")
    assert isinstance(fm, dict), "Frontmatter must be a YAML mapping"


def test_coordinator_frontmatter_is_valid_yaml():
    """coordinator.agent.md frontmatter must parse as valid YAML."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    try:
        fm = _extract_frontmatter(content)
    except Exception as exc:
        raise AssertionError(f"coordinator.agent.md frontmatter parse failed: {exc}")
    assert isinstance(fm, dict), "Frontmatter must be a YAML mapping"


# ---------------------------------------------------------------------------
# argument-hint field
# ---------------------------------------------------------------------------

def test_workspace_cleaner_has_argument_hint():
    """workspace-cleaner.agent.md must still have an argument-hint field."""
    content = CLEANER_FILE.read_text(encoding="utf-8")
    fm = _extract_frontmatter(content)
    assert "argument-hint" in fm, "argument-hint field is missing from workspace-cleaner.agent.md"
    assert fm["argument-hint"], "argument-hint field must not be empty"


# ---------------------------------------------------------------------------
# {{PROJECT_NAME}} placeholder
# ---------------------------------------------------------------------------

def test_workspace_cleaner_contains_project_name_placeholder():
    """workspace-cleaner.agent.md must retain {{PROJECT_NAME}} in the body."""
    content = CLEANER_FILE.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in content, (
        "{{PROJECT_NAME}} placeholder is missing from workspace-cleaner.agent.md"
    )


def test_coordinator_contains_project_name_placeholder():
    """coordinator.agent.md must retain {{PROJECT_NAME}} in the body."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    assert "{{PROJECT_NAME}}" in content, (
        "{{PROJECT_NAME}} placeholder is missing from coordinator.agent.md"
    )


# ---------------------------------------------------------------------------
# Coordinator agents: list completeness
# ---------------------------------------------------------------------------

def test_coordinator_agents_frontmatter_has_exactly_six_agents():
    """coordinator.agent.md agents: list must have exactly 6 agents."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    fm = _extract_frontmatter(content)
    agents = fm.get("agents", [])
    assert isinstance(agents, list), "agents field must be a list"
    assert len(agents) == 6, (
        f"Expected 6 agents, got {len(agents)}: {agents}"
    )


def test_coordinator_agents_frontmatter_exact_names():
    """coordinator.agent.md agents: list must contain exactly the expected agent names."""
    content = COORDINATOR_FILE.read_text(encoding="utf-8")
    fm = _extract_frontmatter(content)
    agents = set(fm.get("agents", []))
    assert agents == EXPECTED_AGENTS, (
        f"Agent list mismatch.\n  Expected: {sorted(EXPECTED_AGENTS)}\n  Got:      {sorted(agents)}"
    )


# ---------------------------------------------------------------------------
# Case-insensitive tidyup scan of the entire template tree
# ---------------------------------------------------------------------------

def test_no_tidyup_references_case_insensitive_all_files():
    """No file anywhere in templates/agent-workbench/ may reference 'tidyup' (any case)."""
    found = []
    for path in TEMPLATE_ROOT.rglob("*"):
        if path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"tidyup", text, re.IGNORECASE):
            found.append(str(path.relative_to(TEMPLATE_ROOT)))
    assert not found, f"'tidyup' (case-insensitive) still found in: {found}"


def test_no_tidyup_agent_file_any_case():
    """No file named tidyup* (any case) should exist in the agents directory."""
    tidyup_files = [
        p for p in AGENTS_DIR.iterdir()
        if re.match(r"tidyup", p.name, re.IGNORECASE)
    ]
    assert not tidyup_files, (
        f"Found tidyup-named file(s): {[p.name for p in tidyup_files]}"
    )


# ---------------------------------------------------------------------------
# File naming convention
# ---------------------------------------------------------------------------

def test_workspace_cleaner_filename_follows_convention():
    """The agent file must be named 'workspace-cleaner.agent.md' (kebab-case)."""
    assert CLEANER_FILE.name == "workspace-cleaner.agent.md", (
        f"Unexpected filename: {CLEANER_FILE.name}"
    )


# ---------------------------------------------------------------------------
# AGENT-RULES.md Workspace-Cleaner is in agent-to-doc mapping
# ---------------------------------------------------------------------------

def test_agent_rules_workspace_cleaner_in_doc_mapping():
    """AGENT-RULES.md section 1a must map Workspace-Cleaner to an AgentDocs document."""
    content = AGENT_RULES_FILE.read_text(encoding="utf-8")
    # The mapping section (1a) should list Workspace-Cleaner → all AgentDocs documents
    section_match = re.search(
        r"## 1a.*?(?=^## |\Z)", content, re.DOTALL | re.MULTILINE
    )
    assert section_match, "Section 1a not found in AGENT-RULES.md"
    section_text = section_match.group(0)
    assert "Workspace-Cleaner" in section_text, (
        "Workspace-Cleaner not found in AGENT-RULES.md section 1a"
    )
