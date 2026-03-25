"""One-shot script to add US-040 through US-051 to user-stories.csv."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_utils import read_csv, write_csv

csv_path = Path(__file__).resolve().parent.parent / "docs" / "user-stories" / "user-stories.csv"
fieldnames, rows = read_csv(csv_path, strict=False)

stories = [
    {
        "ID": "US-040",
        "Title": "Windows Code Signing for Distribution",
        "As a": "developer distributing the launcher",
        "I want": "the Windows installer and executable to be Authenticode-signed",
        "So that": "Windows SmartScreen does not flag the software as dangerous and users trust the download",
        "Acceptance Criteria": "1. The .exe installer is signed with a valid Authenticode certificate; 2. Windows SmartScreen does not show Windows protected your PC warning for signed builds; 3. Signature is verifiable via signtool verify /pa; 4. Signing is automated in the CI/CD pipeline release.yml windows-build job; 5. Certificate renewal process is documented",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 1 - Windows code signing. macOS signing exists (US-025/026) but Windows has zero signing.",
    },
    {
        "ID": "US-041",
        "Title": "Rename Templates to Product Presets",
        "As a": "user",
        "I want": "to choose between Agent Workbench and Certification Pipeline presets when creating a workspace",
        "So that": "the template names clearly communicate their purpose and the product direction",
        "Acceptance Criteria": "1. templates/coding/ is renamed to templates/agent-workbench/; 2. templates/creative-marketing/ is renamed to templates/certification-pipeline/; 3. GUI dropdown shows Agent Workbench (selectable) and Certification Pipeline ...coming soon (greyed out); 4. All internal references (code tests docs) updated to new names; 5. Certification Pipeline remains a stub (README.md only) marked as coming soon; 6. Project creation with Agent Workbench produces identical workspace to former Coding template",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 2 - Template renaming. Replaces Coding and Creative / Marketing naming.",
    },
    {
        "ID": "US-042",
        "Title": "Programmer Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Programmer agent that writes and implements code",
        "So that": "I can delegate coding tasks to a focused implementation specialist",
        "Acceptance Criteria": "1. programmer.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as a practical coder focused on implementation; 3. Agent tools include read edit search execute; 4. Agent is invokable in VS Code Copilot after workspace creation; 5. Agent follows project AGENT-RULES.md conventions",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Programmer vs Pipeline future formal Developer.",
    },
    {
        "ID": "US-043",
        "Title": "Brainstormer Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Brainstormer agent that generates creative solutions and explores approaches",
        "So that": "I can get diverse ideas before committing to an implementation",
        "Acceptance Criteria": "1. brainstormer.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as a creative thinker that generates multiple approaches; 3. Agent tools include read and search (no edit - ideation only); 4. Agent explores trade-offs without premature commitment; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Brainstormer vs Pipeline future formal Architect.",
    },
    {
        "ID": "US-044",
        "Title": "Tester Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Tester agent that writes and runs tests",
        "So that": "my code is validated by a dedicated testing persona",
        "Acceptance Criteria": "1. tester.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as quality-focused test writer; 3. Agent tools include read edit search execute; 4. Agent writes unit and integration tests and finds edge cases; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Tester vs Pipeline future formal Quality Engineer.",
    },
    {
        "ID": "US-045",
        "Title": "Researcher Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Researcher agent that investigates technologies and solutions",
        "So that": "I can make informed technical decisions based on thorough investigation",
        "Acceptance Criteria": "1. researcher.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as an investigator that evaluates and compares; 3. Agent tools include read search and fetch_webpage; 4. Agent produces structured summaries with pros and cons; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Researcher vs Pipeline future formal Analyst.",
    },
    {
        "ID": "US-046",
        "Title": "Scientist Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Scientist agent that approaches problems with analytical rigor",
        "So that": "I get data-driven insights and validated hypotheses",
        "Acceptance Criteria": "1. scientist.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as analytical and hypothesis-driven; 3. Agent tools include read edit search execute; 4. Agent runs benchmarks and experiments and documents findings with evidence; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Scientist vs Pipeline future formal Data Engineer.",
    },
    {
        "ID": "US-047",
        "Title": "Criticist Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Criticist agent that reviews code and finds problems",
        "So that": "I get honest constructive feedback before shipping",
        "Acceptance Criteria": "1. criticist.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as a critical reviewer that identifies issues; 3. Agent tools include read and search only (does NOT fix - only identifies); 4. Agent finds bugs security issues and design flaws; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Criticist vs Pipeline future formal Auditor.",
    },
    {
        "ID": "US-048",
        "Title": "Planner Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Planner agent that breaks down tasks and organizes work",
        "So that": "complex projects are manageable with structured plans",
        "Acceptance Criteria": "1. planner.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as an organizer that creates structured plans; 3. Agent tools include read and search (planning only - no implementation); 4. Agent identifies dependencies and produces actionable task lists; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Planner vs Pipeline future formal Project Lead.",
    },
    {
        "ID": "US-049",
        "Title": "Fixer Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Fixer agent specialized in debugging and troubleshooting",
        "So that": "bugs are efficiently diagnosed and resolved",
        "Acceptance Criteria": "1. fixer.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as a debugger and root cause analyst; 3. Agent tools include read edit search execute; 4. Agent reads errors traces execution and proposes and implements fixes; 5. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Fixer vs Pipeline future formal Diagnostician.",
    },
    {
        "ID": "US-050",
        "Title": "Writer Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Writer agent that creates documentation",
        "So that": "my project has clear well-written docs without me writing them manually",
        "Acceptance Criteria": "1. writer.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as a technical writer; 3. Agent tools include read edit search; 4. Agent creates READMEs API docs inline comments and changelogs; 5. Agent adapts to project voice and structure; 6. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Writer vs Pipeline future formal Technical Writer.",
    },
    {
        "ID": "US-051",
        "Title": "Prototyper Agent for Agent Workbench",
        "As a": "developer using Agent Workbench",
        "I want": "a Prototyper agent that rapidly builds proof-of-concept implementations",
        "So that": "I can validate ideas quickly before investing in production code",
        "Acceptance Criteria": "1. prototyper.agent.md exists in templates/agent-workbench/.github/agents/; 2. Agent has a clear persona as speed-focused MVP builder; 3. Agent tools include read edit search execute; 4. Agent builds quick-and-dirty implementations that validate feasibility; 5. Agent trades perfection for speed; 6. Agent is invokable in VS Code Copilot after workspace creation",
        "Status": "Open",
        "Linked WPs": "",
        "Comments": "Phase 3 - Agent Workbench agents. Casual name Prototyper (no Pipeline equivalent).",
    },
]

# Check for duplicates
existing_ids = {r["ID"] for r in rows}
new_stories = [s for s in stories if s["ID"] not in existing_ids]
if len(new_stories) < len(stories):
    skipped = [s["ID"] for s in stories if s["ID"] in existing_ids]
    print(f"Skipping already existing: {skipped}")

rows.extend(new_stories)
write_csv(csv_path, fieldnames, rows)
print(f"Added {len(new_stories)} user stories: {[s['ID'] for s in new_stories]}")
