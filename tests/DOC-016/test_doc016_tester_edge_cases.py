"""DOC-016 Tester edge-case tests — beyond the Developer's baseline.

Checks that the research report:
- Contains no placeholder / incomplete content
- Has all required structural sections as Markdown headings
- Includes a risk register
- Covers all three implementation phases (A, B, C)
- Provides actionable steps (numbered lists / code blocks)
- Has a minimum meaningful length per major section
- Comparison matrix has all expected columns
- References section contains actual URLs
"""
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "docs" / "plans" / "windows-code-signing.md"


def _read() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Placeholder / incomplete content detection
# ---------------------------------------------------------------------------

def test_no_todo_placeholders():
    content = _read()
    for placeholder in ("TODO", "FIXME", "PLACEHOLDER", "lorem ipsum", "TBD"):
        assert placeholder.lower() not in content.lower(), (
            f"Report contains unresolved placeholder: '{placeholder}'"
        )


def test_no_empty_sections():
    """Every H2 section should have at least 50 characters of content after it."""
    content = _read()
    lines = content.splitlines()
    sections = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            sections.append((i, line.strip()))

    assert len(sections) >= 5, "Expected at least 5 H2 sections in the report"

    for idx, (line_no, heading) in enumerate(sections):
        # Collect text until the next H2 or end of file
        end = sections[idx + 1][0] if idx + 1 < len(sections) else len(lines)
        body = "\n".join(lines[line_no + 1:end]).strip()
        assert len(body) >= 50, (
            f"Section '{heading}' appears to have very little content (body length {len(body)})"
        )


# ---------------------------------------------------------------------------
# Structural completeness
# ---------------------------------------------------------------------------

def test_has_executive_summary_heading():
    content = _read()
    assert re.search(r"##.*[Ee]xecutive\s+[Ss]ummary", content), \
        "Report must have an Executive Summary heading"


def test_has_recommendation_heading():
    content = _read()
    assert re.search(r"##.*[Rr]ecommend", content), \
        "Report must have a Recommendation heading"


def test_has_risks_section():
    content = _read()
    assert re.search(r"[Rr]isk", content), \
        "Report must contain a risks section or risk register"


def test_has_phase_a_setup():
    content = _read()
    assert "Phase A" in content or "Account Setup" in content, \
        "Report must describe Phase A (account setup)"


def test_has_phase_b_workflow():
    content = _read()
    assert "Phase B" in content or "Workflow Integration" in content, \
        "Report must describe Phase B (CI workflow integration)"


def test_has_phase_c_verification():
    content = _read()
    assert "Phase C" in content or "Verification" in content, \
        "Report must describe Phase C or a verification step"


# ---------------------------------------------------------------------------
# Actionability
# ---------------------------------------------------------------------------

def test_has_yaml_code_block():
    """The CI integration section must contain a YAML snippet."""
    content = _read()
    assert "```yaml" in content or "```yml" in content, \
        "Report must include a YAML code block for the CI workflow snippet"


def test_has_github_secret_instructions():
    """Developer must know where to store the API token."""
    content = _read()
    lower = content.lower()
    assert "secret" in lower and ("github" in lower or "repository" in lower), \
        "Report must instruct the developer to add a GitHub repository Secret"


def test_comparison_matrix_has_expected_columns():
    """All key evaluation columns must appear in the comparison matrix."""
    content = _read()
    required_columns = ["Free", "Certificate", "SmartScreen", "CI", "Key"]
    for col in required_columns:
        assert col in content, (
            f"Comparison matrix must contain column '{col}'"
        )


def test_signpath_action_version_specified():
    """The GitHub Action reference should include a version tag (@v1 or similar)."""
    content = _read()
    assert re.search(r"signpath/github-action-submit-signing-request@v\d", content), \
        "CI snippet must pin the SignPath GitHub Action to a specific version"


def test_references_contain_urls():
    """References section must contain at least 3 http(s) URLs."""
    content = _read()
    urls = re.findall(r"https?://[^\s)>]+", content)
    assert len(urls) >= 3, (
        f"Report must include at least 3 reference URLs, found {len(urls)}"
    )


def test_all_three_candidates_have_verdict():
    """Each evaluated service must have documented verdicts / conclusions."""
    content = _read()
    # SignPath must be recommended somewhere
    assert "Recommended" in content or re.search(r"[Rr]ecommend.*[Ss]ignPath|[Ss]ignPath.*[Rr]ecommend", content), \
        "Report must contain a recommendation for SignPath"
    # At least 2 explicit Verdict lines (for Azure and SSL.com, which are excluded)
    verdict_count = len(re.findall(r"\*\*Verdict", content))
    assert verdict_count >= 2, (
        f"Report must have at least 2 explicit Verdict statements (one per excluded candidate), found {verdict_count}"
    )
    # Each non-recommended candidate must be excluded
    assert re.search(r"[Ee]xcluded|[Nn]ot.*recommended|[Nn]o.*free.*tier|[Nn]o.*structured", content), \
        "Report must explicitly exclude or reject at least one candidate"


def test_certificate_renewal_documented():
    """Certificate management / renewal must be explicitly mentioned."""
    content = _read()
    assert re.search(r"renew|rotation|renewal|expire", content, re.IGNORECASE), \
        "Report must address certificate renewal or rotation"


def test_smartscreen_bypass_explained():
    """The report must explain how signing resolves the SmartScreen problem."""
    content = _read()
    lower = content.lower()
    assert "smartscreen" in lower, \
        "Report must reference Windows SmartScreen"
    assert "reputation" in lower or "ev" in lower.split() or "ev-grade" in lower or "extended validation" in lower, \
        "Report must explain SmartScreen reputation building or EV bypass"


def test_report_length_substantial():
    """The full report should be at least 5 000 characters (detailed research)."""
    content = _read()
    assert len(content) >= 5000, (
        f"Report length {len(content)} chars is below the 5 000-char minimum for a research document"
    )
