"""FIX-002: Verify require-approval.json references security_gate.py."""
from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_require_approval_references_security_gate():
    """require-approval.json must reference security_gate.py, not legacy bash."""
    config_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "require-approval.json"
    assert config_path.exists(), f"{config_path.relative_to(REPO_ROOT)} must exist"
    
    content = config_path.read_text(encoding="utf-8")
    data = json.loads(content)
    
    # The config should reference security_gate.py somewhere
    config_str = json.dumps(data)
    assert "security_gate" in config_str.lower(), (
        "require-approval.json should reference security_gate.py"
    )

def test_no_legacy_bash_reference():
    """require-approval.json must not reference legacy bash hooks."""
    config_path = REPO_ROOT / "templates" / "agent-workbench" / ".github" / "hooks" / "require-approval.json"
    content = config_path.read_text(encoding="utf-8")
    
    # Should not have legacy bash script references
    assert "pre-commit.sh" not in content, "Should not reference legacy pre-commit.sh"
    assert "pre-push.sh" not in content, "Should not reference legacy pre-push.sh"
