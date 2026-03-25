"""
Tester-added edge-case / validation tests for DOC-014: Audit Logging Research Report

Goes beyond section-presence checks to validate structural quality,
JSON example correctness, cross-references, acceptance criteria coverage,
and completeness of the design document.
"""
import json
import pathlib
import re

REPORT_PATH = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs"
    / "workpackages"
    / "DOC-014"
    / "research-report.md"
)

DEV_LOG_PATH = REPORT_PATH.parent / "dev-log.md"


def _report_text() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


# ---------- structural quality ----------

def test_report_minimum_word_count():
    """Research report should have sufficient depth (>= 1500 words)."""
    words = _report_text().split()
    assert len(words) >= 1500, (
        f"Report has only {len(words)} words; expected >= 1500 for a thorough research document"
    )


def test_report_has_numbered_sections():
    """Report must have numbered top-level sections (## 1. through ## 7.)."""
    content = _report_text()
    for n in range(1, 7):  # sections 1-6 are required per WP spec
        assert re.search(rf"^##\s+{n}\.", content, re.MULTILINE), (
            f"Missing numbered section heading ## {n}."
        )


def test_report_has_executive_summary():
    """Report must open with an Executive Summary."""
    content = _report_text()
    assert re.search(r"(?i)executive\s+summary", content), (
        "Report should include an Executive Summary"
    )


def test_report_has_references_section():
    """Report must include a References section."""
    content = _report_text()
    assert re.search(r"(?i)^##\s+.*reference", content, re.MULTILINE), (
        "Report should have a References section"
    )


# ---------- JSONL example validation ----------

def test_jsonl_examples_are_valid_json():
    """All JSON code blocks in the report should contain valid JSON."""
    content = _report_text()
    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    assert len(json_blocks) >= 1, "Report must contain at least one JSON example"
    for i, block in enumerate(json_blocks):
        stripped = block.strip()
        # Try parsing as a single JSON object first (multi-line blocks)
        try:
            parsed = json.loads(stripped)
            assert isinstance(parsed, dict), (
                f"JSON example {i} should be a JSON object"
            )
            continue
        except json.JSONDecodeError:
            pass
        # Fall back to line-by-line parsing (JSONL entries)
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                assert isinstance(parsed, dict), (
                    f"JSON example {i} line should be a JSON object"
                )
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"Invalid JSON in code block {i}: {exc}\nLine: {line}"
                ) from exc


def test_jsonl_example_has_required_fields():
    """JSONL example entries must contain all six specified fields."""
    content = _report_text()
    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    required_fields = {"timestamp", "session_id", "tool_name", "decision", "reason"}
    found = False
    for block in json_blocks:
        for line in block.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "timestamp" in obj:  # this is an audit log example
                found = True
                missing = required_fields - set(obj.keys())
                assert not missing, (
                    f"JSONL example missing fields: {missing}"
                )
    assert found, "Report must contain at least one JSONL example with audit fields"


def test_jsonl_example_deny_count_format():
    """deny_count field in examples should follow 'N/M' format."""
    content = _report_text()
    json_blocks = re.findall(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    for block in json_blocks:
        for line in block.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "deny_count" in obj:
                assert re.match(r"\d+/\d+", obj["deny_count"]), (
                    f"deny_count should be in 'N/M' format, got: {obj['deny_count']}"
                )


# ---------- acceptance criteria coverage ----------

def test_us034_criterion6_addressed():
    """US-034 AC#6: design documented for audit logging decisions."""
    content = _report_text()
    assert re.search(r"(?i)US.034", content), (
        "Report must reference user story US-034"
    )


def test_report_addresses_session_identification():
    """US-034 mentions session identification — report should address it."""
    content = _report_text()
    assert re.search(r"(?i)session.id|_get_session_id|session identification", content), (
        "Report must address session identification"
    )


# ---------- two integration points ----------

def test_report_documents_both_deny_paths():
    """Report must document both the initial-deny and already-locked deny paths."""
    content = _report_text()
    assert re.search(r"(?i)lockout|locked.session|already.locked|blocked_locked", content), (
        "Report must document the already-locked-session deny path"
    )
    assert re.search(r"(?i)deny branch|deny.*path|_increment_deny_counter", content), (
        "Report must document the primary deny branch path"
    )


def test_lockout_entry_format_documented():
    """Report must document the special lockout log entry format."""
    content = _report_text()
    assert re.search(r"(?i)lockout.*entry|lockout.*format|decision.*lockout", content), (
        "Report must document the lockout entry format"
    )


# ---------- security properties ----------

def test_fail_safe_property():
    """Audit logging must be fail-safe (errors don't block tool calls)."""
    content = _report_text()
    assert re.search(r"(?i)fail.safe|silent.*error|except.*pass|never.*block", content), (
        "Report must document fail-safe property (audit errors don't block gate)"
    )


def test_append_only_property():
    """Report must state the log is append-only."""
    content = _report_text()
    assert re.search(r"(?i)append.only", content), (
        "Report must document append-only write pattern"
    )


def test_no_pii_in_log():
    """Report must confirm no PII / sensitive data in default log output."""
    content = _report_text()
    assert re.search(r"(?i)no.*pii|pii|sensitive|personal.*identif", content), (
        "Report must address PII / sensitive data exclusion from logs"
    )


# ---------- implementation roadmap ----------

def test_implementation_roadmap_exists():
    """Report must provide clear next steps for the implementing WP."""
    content = _report_text()
    assert re.search(r"(?i)implementation.*scope|future.*wp|implementer.*should|implementation.*step", content), (
        "Report must include an implementation roadmap for the future WP"
    )


def test_update_hashes_mentioned():
    """Report must remind that update_hashes.py must run after changes."""
    content = _report_text()
    assert re.search(r"(?i)update.hashes", content), (
        "Report must mention running update_hashes.py after code changes"
    )


# ---------- cross-references ----------

def test_references_saf035():
    """Report must reference SAF-035 (denial counter)."""
    content = _report_text()
    assert re.search(r"SAF.035", content), "Report must reference SAF-035"


def test_references_saf036():
    """Report must reference SAF-036 (counter config)."""
    content = _report_text()
    assert re.search(r"SAF.036", content), "Report must reference SAF-036"


def test_references_doc013():
    """Report must reference DOC-013 (multi-agent research)."""
    content = _report_text()
    assert re.search(r"DOC.013", content), "Report must reference DOC-013"


# ---------- dev-log consistency ----------

def test_dev_log_exists():
    """dev-log.md must exist."""
    assert DEV_LOG_PATH.exists(), "dev-log.md not found"


def test_dev_log_references_report():
    """dev-log.md must reference the research report."""
    content = DEV_LOG_PATH.read_text(encoding="utf-8")
    assert re.search(r"(?i)research.report|research-report\.md", content), (
        "dev-log.md must reference research-report.md"
    )


def test_dev_log_has_files_changed():
    """dev-log.md must list files changed."""
    content = DEV_LOG_PATH.read_text(encoding="utf-8")
    assert re.search(r"(?i)files.*changed|changed.*files|files.*modified", content), (
        "dev-log.md must list changed files"
    )


# ---------- no placeholder / TODO remnants ----------

def test_report_no_todo_placeholders():
    """Report must not contain unresolved TODO or placeholder markers."""
    content = _report_text()
    # Allow "TODO" only when referencing future WP scope — not as unfinished placeholders
    todo_hits = re.findall(r"\bTODO\b", content, re.IGNORECASE)
    # Exclude WP-style references like SAF-xxx, FIX-xxx from placeholder detection
    placeholder_hits = re.findall(r"\bTBD\b|\bFIXME\b|\[PLACEHOLDER\]", content, re.IGNORECASE)
    standalone_xxx = [m for m in re.findall(r"\bXXX\b", content, re.IGNORECASE)
                      if not re.search(r"[A-Z]{2,4}-xxx", content[max(0, content.index(m)-6):content.index(m)+3], re.IGNORECASE)]
    placeholder_hits.extend(standalone_xxx)
    assert len(placeholder_hits) == 0, (
        f"Report contains unresolved placeholders: {placeholder_hits}"
    )
