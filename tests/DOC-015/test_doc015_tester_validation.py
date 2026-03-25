"""
Tester validation tests for DOC-015: Agent Self-Identification Research Report.

These tests go beyond the Developer's structural validation to verify:
- completeness and depth of each section
- absence of placeholder/draft content
- cross-referencing consistency
- feasibility/trust/recommendation tables accuracy
- dev-log and report alignment
"""
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-015"
    / "research-report.md"
)

DEVLOG_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-015"
    / "dev-log.md"
)


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def _devlog_text() -> str:
    return DEVLOG_PATH.read_text(encoding="utf-8")


# ── Structural completeness ──────────────────────────────────────────

def test_all_seven_sections_present():
    """Report must have numbered sections 1 through 7."""
    content = _report_text()
    for i in range(1, 8):
        assert re.search(rf"^##\s+{i}\.", content, re.MULTILINE), (
            f"Section {i} heading (## {i}. ...) is missing from the report"
        )


def test_no_empty_sections():
    """Every numbered section must have at least 50 words of body text."""
    content = _report_text()
    sections = re.split(r"^## \d+\.", content, flags=re.MULTILINE)
    # First element is the preamble / executive summary; skip it
    for idx, sec in enumerate(sections[1:], start=1):
        words = len(sec.split())
        assert words >= 50, (
            f"Section {idx} has only {words} words — too shallow"
        )


def test_executive_summary_is_substantive():
    """Executive summary must contain at least 80 words."""
    content = _report_text()
    match = re.search(r"(?i)## executive summary\s*\n(.*?)(?=\n## )", content, re.DOTALL)
    assert match, "Executive Summary section not found"
    words = len(match.group(1).split())
    assert words >= 80, f"Executive Summary has only {words} words — expected ≥80"


# ── No placeholder / draft artefacts ─────────────────────────────────

def test_no_todo_or_placeholder():
    """Report must not contain TODO, FIXME, PLACEHOLDER, TBD, or XXX markers."""
    content = _report_text()
    hits = re.findall(r"\b(TODO|FIXME|PLACEHOLDER|TBD|XXX)\b", content)
    assert not hits, f"Placeholder markers found in report: {hits}"


def test_no_lorem_ipsum():
    """Report must not contain lorem ipsum filler text."""
    content = _report_text().lower()
    assert "lorem ipsum" not in content, "Lorem ipsum filler detected"


def test_report_metadata_fields():
    """Report header must include Author, Date, Workpackage, and Status."""
    content = _report_text()
    for field in ("Author", "Date", "Workpackage", "Status"):
        assert re.search(rf"\*\*{field}:\*\*", content), (
            f"Report header missing **{field}:** field"
        )


# ── Feasibility assessment table ─────────────────────────────────────

def test_feasibility_table_has_rows():
    """Section 3 feasibility table must list at least 4 variant rows."""
    content = _report_text()
    # The table has "|" delimited rows with "feasible" or "Feasib" in them
    feasibility_rows = re.findall(r"\|.*?[Ff]easib.*?\|", content)
    assert len(feasibility_rows) >= 4, (
        f"Feasibility table has only {len(feasibility_rows)} rows — expected ≥4"
    )


# ── Trust boundary table ─────────────────────────────────────────────

def test_trust_boundary_table_present():
    """Section 4 must contain a trust-boundary table with Trusted/Untrusted rows."""
    content = _report_text()
    assert re.search(r"(?i)trust boundary", content), "Trust boundary concept missing"
    # Table should list VS Code Copilot as trusted
    assert re.search(r"\|.*VS Code Copilot.*\|.*[Yy]es.*\|", content), (
        "VS Code Copilot must be marked as trusted in the trust boundary table"
    )
    # Agent-reported identity should be untrusted
    assert re.search(r"\|.*[Aa]gent.reported.*\|.*[Nn]o.*\|", content), (
        "Agent-reported identity must be marked as untrusted"
    )


# ── Recommendations table ────────────────────────────────────────────

def test_recommendations_summary_table():
    """Section 6 must include a summary table with Priority column."""
    content = _report_text()
    assert re.search(r"\| Recommendation.*\| Priority.*\|", content), (
        "Recommendations summary table with Priority column not found"
    )
    # Should have at least 3 recommendation rows
    rec_pattern = re.compile(r"\|.*\|\s*(Immediate|Near-term|Long-term|Future|Optional)", re.IGNORECASE)
    rows = rec_pattern.findall(content)
    assert len(rows) >= 3, (
        f"Recommendations table has only {len(rows)} prioritised entries — expected ≥3"
    )


# ── Cross-referencing ────────────────────────────────────────────────

def test_section_cross_references():
    """Report should internally reference other sections (e.g. 'see Section 4')."""
    content = _report_text()
    refs = re.findall(r"[Ss]ection \d", content)
    assert len(refs) >= 2, (
        "Report should contain at least 2 cross-references between sections"
    )


def test_report_references_otel_file():
    """Report must specifically mention copilot-otel.jsonl as the telemetry source."""
    content = _report_text()
    assert "copilot-otel.jsonl" in content, (
        "Report must mention the copilot-otel.jsonl file by name"
    )


def test_report_references_hook_state_json():
    """Report must mention .hook_state.json as fallback session storage."""
    content = _report_text()
    assert ".hook_state.json" in content, (
        "Report must mention .hook_state.json as the stateful fallback"
    )


# ── Model coverage ───────────────────────────────────────────────────

def test_at_least_three_model_families_discussed():
    """Section 2 must explicitly discuss at least 3 distinct model families."""
    content = _report_text()
    families_found = 0
    for pattern in [r"GPT-4|OpenAI", r"Claude|Anthropic", r"Gemini|Google"]:
        if re.search(pattern, content):
            families_found += 1
    assert families_found >= 3, (
        f"Only {families_found} model families discussed — expected ≥3"
    )


def test_mentions_http_versus_stdio():
    """Report must clarify that the hook is invoked via stdin/stdout, not HTTP."""
    content = _report_text()
    assert re.search(r"(?i)stdin|stdout|subprocess|child process", content), (
        "Report must explain the hook communication channel (stdin/stdout)"
    )
    assert re.search(r"(?i)no http|not http|no.*http header|not.*http server", content), (
        "Report must clarify the hook is NOT an HTTP server"
    )


# ── Security depth ───────────────────────────────────────────────────

def test_multiple_spoofing_scenarios():
    """Section 4 must include at least 3 distinct spoofing/threat scenarios."""
    content = _report_text()
    scenarios = re.findall(r"\*\*Scenario [A-Z]", content)
    assert len(scenarios) >= 3, (
        f"Only {len(scenarios)} spoofing scenarios found — expected ≥3"
    )


def test_discusses_prompt_injection():
    """Section 4 should mention prompt injection as an attack vector."""
    content = _report_text()
    assert re.search(r"(?i)prompt injection", content), (
        "Report should discuss prompt injection as a relevant threat"
    )


# ── Dev-log / report consistency ─────────────────────────────────────

def test_devlog_exists():
    """dev-log.md must exist in the DOC-015 workpackage folder."""
    assert DEVLOG_PATH.exists(), f"dev-log.md not found at {DEVLOG_PATH}"


def test_devlog_references_report():
    """dev-log.md must reference research-report.md as a deliverable."""
    content = _devlog_text()
    assert "research-report.md" in content, (
        "dev-log.md must reference research-report.md as a deliverable"
    )


def test_devlog_lists_security_gate():
    """dev-log.md must reference security_gate.py as an inspected file."""
    content = _devlog_text()
    assert re.search(r"security.gate", content, re.IGNORECASE), (
        "dev-log.md must mention security_gate.py"
    )


def test_report_final_status():
    """Report header Status must be 'Final', not Draft or In Progress."""
    content = _report_text()
    match = re.search(r"\*\*Status:\*\*\s*(.+)", content)
    assert match, "Report Status field not found"
    assert match.group(1).strip().lower() == "final", (
        f"Report status is '{match.group(1).strip()}' — expected 'Final'"
    )


# ── Report ending ────────────────────────────────────────────────────

def test_report_has_explicit_end_marker():
    """Report must have a clear ending (e.g. 'End of Research Report')."""
    content = _report_text()
    assert re.search(r"(?i)end of research report", content), (
        "Report must have an explicit 'End of Research Report' marker"
    )


def test_references_section_present():
    """Report must contain a References / Files Inspected section."""
    content = _report_text()
    assert re.search(r"(?i)## 7\.\s*References|Files Inspected", content), (
        "Section 7 (References and Files Inspected) missing"
    )


def test_references_list_at_least_four_sources():
    """Section 7 must list at least 4 inspected resources."""
    content = _report_text()
    # Find all table rows in section 7 that contain a pipe-delimited resource
    sec7_match = re.search(r"## 7\..+?\n(.*)", content, re.DOTALL)
    assert sec7_match, "Section 7 not found"
    sec7_text = sec7_match.group(1)
    rows = [line for line in sec7_text.split("\n") if line.strip().startswith("|") and "---" not in line and "Resource" not in line]
    assert len(rows) >= 4, (
        f"Section 7 lists only {len(rows)} resources — expected ≥4"
    )
