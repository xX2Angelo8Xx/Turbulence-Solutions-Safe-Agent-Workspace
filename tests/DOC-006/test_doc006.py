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
