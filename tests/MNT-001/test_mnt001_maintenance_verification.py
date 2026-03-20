"""MNT-001: Verify maintenance sweep results are clean."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_no_stale_pytest_output_in_root():
    """No pytest_*.txt files should remain in the repo root."""
    stale_files = list(REPO_ROOT.glob("pytest_*.txt"))
    assert not stale_files, (
        f"Stale pytest output files found in repo root: {[f.name for f in stale_files]}"
    )

def test_maintenance_log_exists():
    """A maintenance log should exist in docs/maintenance/."""
    maint_dir = REPO_ROOT / "docs" / "maintenance"
    assert maint_dir.exists(), "docs/maintenance/ must exist"
    
    logs = list(maint_dir.glob("*.md"))
    assert logs, "docs/maintenance/ must contain at least one maintenance log"
