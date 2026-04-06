"""
DOC-062: Tests for clean-workspace copilot-instructions.md, README.md, and Project/README.md.

Verifies:
- copilot-instructions.md has no references to non-existent agents, AgentDocs, skills, or prompts.
- copilot-instructions.md contains the zone model table (Tier 1/2/3).
- copilot-instructions.md contains the security rules section with key safety mandates.
- copilot-instructions.md contains the Known Tool Limitations table.
- workspace README.md contains the security tiers table and About This Template section.
- workspace README.md does not reference agents/skills/prompts folders.
- Project/README.md contains zone summary and AGENT-RULES.md reference.
- MANIFEST.json entries exist for all three documentation files.
"""

import json
import re
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).parents[2] / "templates" / "clean-workspace"
COPILOT_INSTRUCTIONS = TEMPLATE_ROOT / ".github" / "instructions" / "copilot-instructions.md"
README = TEMPLATE_ROOT / "README.md"
PROJECT_README = TEMPLATE_ROOT / "Project" / "README.md"
MANIFEST = TEMPLATE_ROOT / "MANIFEST.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestCopilotInstructions:
    def test_no_agent_references(self):
        """copilot-instructions.md must not reference custom agents, AgentDocs, skills, or prompts folders."""
        content = _read(COPILOT_INSTRUCTIONS)
        forbidden_patterns = [
            r"\.github/agents",
            r"\.github/skills",
            r"\.github/prompts",
            r"AgentDocs",
            r"agent roster",
            r"@<agent-name>",
        ]
        for pattern in forbidden_patterns:
            assert not re.search(pattern, content, re.IGNORECASE), (
                f"copilot-instructions.md must not contain '{pattern}'"
            )

    def test_zone_model_table_present(self):
        """copilot-instructions.md must contain the Tier 1/2/3 zone model table."""
        content = _read(COPILOT_INSTRUCTIONS)
        assert "Tier 1" in content, "Zone model table must include Tier 1"
        assert "Tier 2" in content, "Zone model table must include Tier 2"
        assert "Tier 3" in content, "Zone model table must include Tier 3"
        assert "Auto-Allow" in content, "Zone model must label Tier 1 as Auto-Allow"
        assert "Force Ask" in content, "Zone model must label Tier 2 as Force Ask"
        assert "Hard Block" in content, "Zone model must label Tier 3 as Hard Block"

    def test_security_rules_section_present(self):
        """copilot-instructions.md must have a Security Rules section with key mandates."""
        content = _read(COPILOT_INSTRUCTIONS)
        assert "Security Rules" in content, "Security Rules section must be present"
        assert "path traversal" in content.lower(), "Security rules must mention path traversal"
        assert "exfiltrate" in content.lower(), "Security rules must mention exfiltration"
        assert "terminal commands" in content.lower(), "Security rules must mention terminal bypass"

    def test_known_tool_limitations_table_present(self):
        """copilot-instructions.md must contain the Known Tool Limitations table."""
        content = _read(COPILOT_INSTRUCTIONS)
        assert "Known Tool Limitations" in content
        assert "Out-File" in content
        assert "Set-Content" in content

    def test_skills_not_in_github_partial_read_section(self):
        """The .github/ partial read-only listing must not mention skills/, agents/, or prompts/."""
        content = _read(COPILOT_INSTRUCTIONS)
        # Find the line that describes .github/ partial read access
        for line in content.splitlines():
            if "Partial read-only" in line or ".github/" in line and "instructions/" in line:
                assert "skills/" not in line, (
                    "Clean-workspace .github/ listing must not mention skills/"
                )
                assert "agents/" not in line, (
                    "Clean-workspace .github/ listing must not mention agents/"
                )
                assert "prompts/" not in line, (
                    "Clean-workspace .github/ listing must not mention prompts/"
                )


class TestWorkspaceReadme:
    def test_security_tiers_table_present(self):
        """README.md must contain the three-tier security table."""
        content = _read(README)
        assert "Tier 1" in content
        assert "Tier 2" in content
        assert "Tier 3" in content
        assert "Auto-Allow" in content
        assert "Force Ask" in content
        assert "Hard Block" in content

    def test_about_template_section_present(self):
        """README.md must have an About This Template section explaining no agents/skills/prompts."""
        content = _read(README)
        assert "About This Template" in content
        # Confirm it explicitly says there are no agents/skills/prompts folders
        assert "agents" in content.lower(), "About section must mention absence of agents"
        assert "skills" in content.lower(), "About section must mention absence of skills"
        assert "prompts" in content.lower(), "About section must mention absence of prompts"

    def test_getting_started_section_expanded(self):
        """README.md Getting Started section must have numbered steps."""
        content = _read(README)
        assert "Getting Started" in content
        # At minimum 2 numbered steps should be present
        assert content.count("\n1.") + content.count("\n2.") >= 2


class TestProjectReadme:
    def test_agent_rules_reference_present(self):
        """Project/README.md must reference AGENT-RULES.md."""
        content = _read(PROJECT_README)
        assert "AGENT-RULES.md" in content

    def test_zone_summary_present(self):
        """Project/README.md must include a zone summary table."""
        content = _read(PROJECT_README)
        assert "Zone" in content or "Tier" in content or "NoAgentZone" in content


class TestManifest:
    def test_manifest_tracks_copilot_instructions(self):
        """MANIFEST.json must have an entry for copilot-instructions.md."""
        manifest = json.loads(_read(MANIFEST))
        assert ".github/instructions/copilot-instructions.md" in manifest["files"]

    def test_manifest_tracks_readme(self):
        """MANIFEST.json must have an entry for README.md."""
        manifest = json.loads(_read(MANIFEST))
        assert "README.md" in manifest["files"]

    def test_manifest_tracks_project_readme(self):
        """MANIFEST.json must have an entry for Project/README.md."""
        manifest = json.loads(_read(MANIFEST))
        assert "Project/README.md" in manifest["files"]
