"""
MNT-006: Tests for planner.agent.md body content.
Verifies all required sections and key constraints are present.
"""
import pathlib

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "planner.agent.md"


def _load_body() -> str:
    content = AGENT_FILE.read_text(encoding="utf-8")
    # Strip YAML frontmatter (between first and second ---)
    parts = content.split("---", 2)
    assert len(parts) >= 3, "planner.agent.md missing closing --- for frontmatter"
    return parts[2]


def test_startup_section_exists():
    body = _load_body()
    assert "## Startup" in body, "planner.agent.md is missing '## Startup' section"


def test_startup_reads_architecture():
    body = _load_body()
    assert "architecture.md" in body, (
        "Startup section does not mention reading 'architecture.md'"
    )


def test_startup_reads_project_scope():
    body = _load_body()
    assert "project-scope.md" in body, (
        "Startup section does not mention reading 'project-scope.md'"
    )


def test_startup_reads_decisions_index():
    body = _load_body()
    assert "decisions/index.csv" in body or "index.csv" in body, (
        "Startup section does not mention reading the ADR index"
    )


def test_startup_reads_workpackages_csv():
    body = _load_body()
    assert "workpackages.csv" in body, (
        "Startup section does not mention reading 'workpackages.csv'"
    )


def test_startup_reads_bugs_csv():
    body = _load_body()
    assert "bugs.csv" in body, (
        "Startup section does not mention reading 'bugs.csv'"
    )


def test_workflow_section_exists():
    body = _load_body()
    assert "## Workflow" in body, "planner.agent.md is missing '## Workflow' section"


def test_workflow_understand_step():
    body = _load_body()
    assert "Step 1" in body, "Workflow is missing Step 1 (Understand the Input)"
    assert "Feature Request" in body, (
        "Workflow does not mention 'Feature Request' as an input type"
    )
    assert "Bug Report" in body, "Workflow does not mention 'Bug Report' as an input type"
    assert "Security Gap" in body, "Workflow does not mention 'Security Gap' as an input type"


def test_workflow_investigate_step():
    body = _load_body()
    assert "Step 2" in body, "Workflow is missing Step 2 (Investigate)"


def test_workflow_adr_check_step():
    body = _load_body()
    assert "Step 3" in body, "Workflow is missing Step 3 (ADR check)"
    assert "ADR" in body, "Workflow does not reference ADR check"


def test_workflow_draft_plan_step():
    body = _load_body()
    assert "Step 4" in body, "Workflow is missing Step 4 (Draft Plan)"
    assert "Impact" in body, "Plan template does not include Impact Assessment"
    assert "Risk" in body, "Plan template does not include Risk Assessment"


def test_workflow_present_step():
    body = _load_body()
    assert "Step 5" in body, "Workflow is missing Step 5 (Present for Feedback)"
    assert "approve" in body.lower(), (
        "Workflow does not mention requesting user approval"
    )


def test_workflow_handoff_step():
    body = _load_body()
    assert "Step 6" in body, "Workflow is missing Step 6 (Hand Off)"
    assert "Orchestrator" in body, "Workflow does not mention handing off to Orchestrator"


def test_constraints_section_exists():
    body = _load_body()
    assert "## Constraints" in body, "planner.agent.md is missing '## Constraints' section"


def test_constraints_no_wp_creation():
    body = _load_body()
    assert "DO NOT" in body, "Constraints section has no DO NOT rules"
    lower = body.lower()
    assert "workpackage" in lower or "workpackages.csv" in lower, (
        "Constraints do not mention prohibiting WP creation or CSV edits"
    )


def test_constraints_no_code_writing():
    body = _load_body()
    lower = body.lower()
    assert "code" in lower or "implement" in lower, (
        "Constraints do not mention prohibition on writing code"
    )


def test_constraints_no_handoff_before_approval():
    body = _load_body()
    assert "explicit" in body.lower(), (
        "Constraints do not mention requiring explicit user approval before handoff"
    )


def test_constraints_no_csv_editing():
    body = _load_body()
    assert "csv" in body.lower(), (
        "Constraints do not explicitly mention prohibiting CSV editing"
    )
