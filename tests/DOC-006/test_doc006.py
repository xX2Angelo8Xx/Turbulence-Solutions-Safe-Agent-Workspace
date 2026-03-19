"""
tests/DOC-006/test_doc006.py

Verify that section 10 ("V3.0.0 Implementation Decisions") has been correctly
added to the security audit document.
"""

import pathlib

AUDIT_FILE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "docs"
    / "Security Audits"
    / "SECURITY_ADVANCED_ATTACK_ANALYSIS-V3.0.0-18-03.26.md"
)


def _content() -> str:
    return AUDIT_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Section heading
# ---------------------------------------------------------------------------

def test_section_10_heading_exists():
    """The document must contain the section-10 heading."""
    assert "## 10. V3.0.0 Implementation Decisions" in _content()


# ---------------------------------------------------------------------------
# 2. All 11 recommendations must be mentioned (R1 through R11)
# ---------------------------------------------------------------------------

def test_r1_mentioned():
    assert "R1" in _content()

def test_r2_mentioned():
    assert "R2" in _content()

def test_r3_mentioned():
    assert "R3" in _content()

def test_r4_mentioned():
    assert "R4" in _content()

def test_r5_mentioned():
    assert "R5" in _content()

def test_r6_mentioned():
    assert "R6" in _content()

def test_r7_mentioned():
    assert "R7" in _content()

def test_r8_mentioned():
    assert "R8" in _content()

def test_r9_mentioned():
    assert "R9" in _content()

def test_r10_mentioned():
    assert "R10" in _content()

def test_r11_mentioned():
    assert "R11" in _content()


# ---------------------------------------------------------------------------
# 3. Implemented recommendations reference the correct WP IDs
# ---------------------------------------------------------------------------

def test_r2_references_saf032():
    """R2 must be linked to SAF-032 within section 10."""
    content = _content()
    # Extract section 10 only
    idx_s10 = content.find("## 10. V3.0.0 Implementation Decisions")
    assert idx_s10 != -1
    section10 = content[idx_s10:]
    assert "SAF-032" in section10
    idx_r2 = section10.find("#### R2")
    idx_saf032 = section10.find("SAF-032", idx_r2)
    assert idx_saf032 != -1 and (idx_saf032 - idx_r2) < 500


def test_r4_references_saf032():
    """R4 must be linked to SAF-032 within section 10."""
    content = _content()
    idx_s10 = content.find("## 10. V3.0.0 Implementation Decisions")
    assert idx_s10 != -1
    section10 = content[idx_s10:]
    idx_r4 = section10.find("#### R4")
    idx_saf032 = section10.find("SAF-032", idx_r4)
    assert idx_saf032 != -1 and (idx_saf032 - idx_r4) < 500


def test_r6_references_saf033():
    """R6 must be linked to SAF-033 within section 10."""
    content = _content()
    idx_s10 = content.find("## 10. V3.0.0 Implementation Decisions")
    assert idx_s10 != -1
    section10 = content[idx_s10:]
    assert "SAF-033" in section10
    idx_r6 = section10.find("#### R6")
    idx_saf033 = section10.find("SAF-033", idx_r6)
    assert idx_saf033 != -1 and (idx_saf033 - idx_r6) < 500


def test_r3_contains_icacls_instruction():
    """R3 section must contain the icacls admin instructions."""
    content = _content()
    assert "icacls" in content


# ---------------------------------------------------------------------------
# 4. Philosophy statement must be present
# ---------------------------------------------------------------------------

def test_philosophy_statement_present():
    """The overall philosophy quote must be present in the document."""
    assert (
        "The workspace is designed for maximum agent freedom inside the project folder"
        in _content()
    )
    assert (
        "we harden the boundaries, not restrict what happens inside"
        in _content()
    )


# ---------------------------------------------------------------------------
# 5. FIX-046 must be mentioned
# ---------------------------------------------------------------------------

def test_fix046_mentioned():
    """FIX-046 (Default-Project removal) must be documented in section 10."""
    assert "FIX-046" in _content()


# ---------------------------------------------------------------------------
# Tester edge-case tests
# ---------------------------------------------------------------------------

def _section10(content: str) -> str:
    """Return only the text from the start of section 10 onward."""
    idx = content.find("## 10. V3.0.0 Implementation Decisions")
    assert idx != -1, "Section 10 heading not found"
    return content[idx:]


def test_all_four_subsections_present():
    """Section 10 must contain all four numbered sub-sections."""
    s10 = _section10(_content())
    assert "### 10.1 Implemented Recommendations" in s10
    assert "### 10.2 Deferred / Not Implemented Recommendations" in s10
    assert "### 10.3 Additional V3.0.0 Change" in s10
    assert "### 10.4 Overall Philosophy" in s10


def test_section_10_comes_after_section_9():
    """Section 10 must appear AFTER section 9 in document order."""
    content = _content()
    # Accept any form of a section-9 heading (##, ###, ####, etc.)
    idx_9 = content.find("## 9.")
    idx_10 = content.find("## 10. V3.0.0 Implementation Decisions")
    assert idx_9 != -1, "No section-9 heading found"
    assert idx_10 != -1, "Section-10 heading not found"
    assert idx_10 > idx_9, "Section 10 must come after section 9"


def test_r1_in_deferred_section():
    """R1 must appear inside/after the deferred sub-section (10.2), not only in 10.1."""
    content = _content()
    idx_deferred = content.find("### 10.2 Deferred / Not Implemented Recommendations")
    assert idx_deferred != -1
    deferred_onwards = content[idx_deferred:]
    # R1 should appear in the deferred block
    assert "R1" in deferred_onwards


def test_r3_icacls_in_implemented_section():
    """R3 and the icacls command must appear in the Implemented sub-section (10.1)."""
    content = _content()
    idx_10_1 = content.find("### 10.1 Implemented Recommendations")
    idx_10_2 = content.find("### 10.2 Deferred / Not Implemented Recommendations")
    assert idx_10_1 != -1
    assert idx_10_2 != -1
    implemented_block = content[idx_10_1:idx_10_2]
    assert "R3" in implemented_block
    assert "icacls" in implemented_block


def test_fix046_in_section_10_3():
    """FIX-046 must appear inside sub-section 10.3, not just anywhere in the file."""
    content = _content()
    idx_10_3 = content.find("### 10.3 Additional V3.0.0 Change")
    assert idx_10_3 != -1
    section_10_3_onwards = content[idx_10_3:]
    assert "FIX-046" in section_10_3_onwards


def test_philosophy_in_section_10_4():
    """The philosophy statement must reside in the 10.4 sub-section."""
    content = _content()
    idx_10_4 = content.find("### 10.4 Overall Philosophy")
    assert idx_10_4 != -1
    section_10_4 = content[idx_10_4:]
    assert "we harden the boundaries, not restrict what happens inside" in section_10_4


def test_section_10_has_date_metadata():
    """Section 10 must contain a date metadata line."""
    s10 = _section10(_content())
    assert "2026" in s10, "Section 10 should contain a year reference (date metadata)"


def test_r2_and_r4_both_reference_saf032_in_implemented():
    """Both R2 and R4 must be linked to SAF-032 inside the Implemented block."""
    content = _content()
    idx_10_1 = content.find("### 10.1 Implemented Recommendations")
    idx_10_2 = content.find("### 10.2 Deferred / Not Implemented Recommendations")
    assert idx_10_1 != -1 and idx_10_2 != -1
    block = content[idx_10_1:idx_10_2]
    # Both must appear and SAF-032 must appear at least twice (once near R2, once near R4)
    assert block.count("SAF-032") >= 2


def test_audit_file_exists_and_is_readable():
    """The audit file itself must exist on disk and be non-empty."""
    assert AUDIT_FILE.exists(), f"Audit file not found: {AUDIT_FILE}"
    assert AUDIT_FILE.stat().st_size > 0, "Audit file is empty"
    text = AUDIT_FILE.read_text(encoding="utf-8")
    assert len(text) > 1000, "Audit file suspiciously small"
