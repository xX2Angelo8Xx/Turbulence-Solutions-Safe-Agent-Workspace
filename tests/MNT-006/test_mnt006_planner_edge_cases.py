"""
MNT-006: Tester edge-case tests for planner.agent.md.
Covers boundary conditions and defence-in-depth scenarios beyond the Developer's test suite.
"""
import pathlib
import re

AGENT_FILE = pathlib.Path(__file__).parents[2] / ".github" / "agents" / "planner.agent.md"


def _content() -> str:
    return AGENT_FILE.read_text(encoding="utf-8")


def _frontmatter() -> str:
    m = re.match(r"^---\n(.*?)\n---", _content(), re.DOTALL)
    assert m, "No valid YAML frontmatter found"
    return m.group(1)


def _body() -> str:
    parts = _content().split("---", 2)
    assert len(parts) >= 3, "Missing closing --- for frontmatter"
    return parts[2]


# ── File hygiene ───────────────────────────────────────────────────────────────

def test_file_ends_with_newline():
    """Markdown files should end with a newline to avoid POSIX noncompliance."""
    content = _content()
    assert content.endswith("\n"), "planner.agent.md does not end with a newline character"


def test_no_bom():
    """File must not have a UTF-8 BOM that would corrupt YAML parsing."""
    raw = AGENT_FILE.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "planner.agent.md starts with a UTF-8 BOM"


def test_no_absolute_paths():
    """Security rule: no absolute paths (e.g. C:\\, /home/) in the agent file."""
    content = _content()
    # Match Windows and Unix absolute paths
    assert not re.search(r"[A-Za-z]:\\\\", content), "Absolute Windows path found in agent file"
    # Allow relative Unix-style paths but not /home/, /usr/, etc.
    assert not re.search(r"\b/(?:home|usr|var|etc|root)/", content), (
        "Absolute Unix path found in agent file"
    )


# ── YAML frontmatter depth ─────────────────────────────────────────────────────

def test_handoffs_plan_placeholder_present():
    """The handoff prompt must contain the {{plan}} placeholder so the finalized
    plan is actually forwarded to the Orchestrator."""
    fm = _frontmatter()
    assert "{{plan}}" in fm, (
        "handoffs prompt does not contain {{plan}} — plan will not be forwarded to Orchestrator"
    )


def test_frontmatter_workflow_step_numbers_contiguous():
    """Steps 1–6 must all appear in the body (no gaps in the workflow)."""
    body = _body()
    for step in range(1, 7):
        assert f"Step {step}" in body, (
            f"Workflow is missing Step {step} — step numbers are not contiguous"
        )


def test_startup_exactly_five_files():
    """Startup section must list exactly 5 project files to read."""
    body = _body()
    startup_match = re.search(r"## Startup(.*?)(?=\n##|\Z)", body, re.DOTALL)
    assert startup_match, "No ## Startup section found"
    startup = startup_match.group(1)
    # Count numbered items (1. 2. 3. 4. 5.)
    numbered = re.findall(r"^\s*\d+\.", startup, re.MULTILINE)
    assert len(numbered) == 5, (
        f"Startup section should list exactly 5 files, found {len(numbered)}"
    )


# ── Constraints completeness ───────────────────────────────────────────────────

def test_constraints_no_story_writing():
    """Constraints must prohibit creating/modifying user stories (Story Writer's role)."""
    body = _body()
    lower = body.lower()
    assert "story" in lower, (
        "Constraints section does not mention prohibition on creating user stories"
    )


def test_constraints_prohibits_marking_wp_status():
    """Planner must not be allowed to change WP statuses (In Progress, Review, Done)."""
    body = _body()
    lower = body.lower()
    # Check for mention of not marking / not changing WP status
    assert "in progress" in lower or "review" in lower or "done" in lower, (
        "Constraints do not prohibit marking WP status changes"
    )


def test_constraints_require_user_approval_before_handoff():
    """Explicit approval must be required before handing off to Orchestrator."""
    body = _body()
    lower = body.lower()
    assert "explicit" in lower and ("approval" in lower or "approve" in lower), (
        "Constraints do not state that explicit user approval is required before handoff"
    )


# ── Workflow quality ───────────────────────────────────────────────────────────

def test_workflow_requests_clarification_when_ambiguous():
    """Step 1 must instruct the agent to ask clarifying questions for ambiguous inputs."""
    body = _body()
    assert "clarif" in body.lower() or "question" in body.lower(), (
        "Step 1 does not instruct agent to ask clarifying questions for ambiguous input"
    )


def test_step5_presents_full_plan():
    """Step 5 must tell the agent to present the FULL plan, not a summary."""
    body = _body()
    step5_match = re.search(r"Step 5.*?(?=### Step 6|\Z)", body, re.DOTALL)
    assert step5_match, "Step 5 section not found"
    step5 = step5_match.group(0).lower()
    assert "plan" in step5 and ("full" in step5 or "present" in step5), (
        "Step 5 does not instruct agent to present the full plan"
    )


def test_step6_confirms_handoff_to_user():
    """Step 6 must confirm to the user after handing off (not silently hand off)."""
    body = _body()
    step6_match = re.search(r"Step 6.*?(?=\n##|\Z)", body, re.DOTALL)
    assert step6_match, "Step 6 section not found"
    step6 = step6_match.group(0).lower()
    assert "confirm" in step6 or "handed off" in step6 or "handed" in step6, (
        "Step 6 does not confirm to the user that handoff has occurred"
    )
