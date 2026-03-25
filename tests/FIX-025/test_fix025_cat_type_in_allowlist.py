"""FIX-025: Verify 'cat' and 'type' are in security_gate.py allowlist."""
from __future__ import annotations
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_cat_in_allowlist():
    """'cat' must be in security_gate.py allowlist."""
    sg_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
    assert sg_path.exists(), "security_gate.py must exist"
    
    content = sg_path.read_text(encoding="utf-8")
    # cat should appear as a quoted string in the allowlist
    assert re.search(r'["\']cat["\']', content), (
        "'cat' must be in security_gate.py allowlist"
    )

def test_type_in_allowlist():
    """'type' must be in security_gate.py allowlist."""
    sg_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
    content = sg_path.read_text(encoding="utf-8")
    
    assert re.search(r'["\']type["\']', content), (
        "'type' must be in security_gate.py allowlist"
    )

def test_cat_type_in_project_fallback_verbs():
    """'cat' and 'type' should be in _PROJECT_FALLBACK_VERBS."""
    sg_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts" / "security_gate.py"
    content = sg_path.read_text(encoding="utf-8")
    
    assert "_PROJECT_FALLBACK_VERBS" in content, (
        "security_gate.py must define _PROJECT_FALLBACK_VERBS"
    )
