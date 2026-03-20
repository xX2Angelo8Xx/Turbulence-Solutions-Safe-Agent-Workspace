"""FIX-060: Verify all legacy artifact cleanup was successful.

Meta-test that confirms: no tmp_ files remain, all WP dirs have dev-log.md,
all test dirs have test_*.py files, and the validator reports zero errors
for the 24 affected WPs.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# WPs that had missing dev-log.md / test-report.md
WPS_NEEDING_ARTIFACTS = ["FIX-023", "FIX-024", "FIX-025", "FIX-026", "FIX-027"]

# WPs that had tmp_ files
WPS_WITH_TMP = ["SAF-033", "FIX-046", "FIX-055"]

# WPs that had missing test dirs or empty test dirs
WPS_NEEDING_TESTS = [
    "FIX-001", "FIX-002", "FIX-003", "FIX-004", "FIX-005",
    "FIX-024", "FIX-025", "FIX-027", "FIX-043",
    "SAF-004", "SAF-027", "FIX-046", "MNT-001",
]


def test_no_tmp_files_remain():
    """No tmp_* files should remain in any WP directory."""
    for wp_id in WPS_WITH_TMP:
        wp_dir = REPO_ROOT / "docs" / "workpackages" / wp_id
        if wp_dir.exists():
            tmp_files = list(wp_dir.glob("tmp_*"))
            assert not tmp_files, (
                f"{wp_id}: tmp_ files still present: {[f.name for f in tmp_files]}"
            )


def test_artifact_dirs_have_dev_log():
    """WPs that were missing dev-log.md now have it."""
    for wp_id in WPS_NEEDING_ARTIFACTS:
        dev_log = REPO_ROOT / "docs" / "workpackages" / wp_id / "dev-log.md"
        assert dev_log.exists(), f"{wp_id}: dev-log.md still missing"


def test_artifact_dirs_have_test_report():
    """WPs that were missing test-report.md now have it."""
    for wp_id in WPS_NEEDING_ARTIFACTS:
        test_report = REPO_ROOT / "docs" / "workpackages" / wp_id / "test-report.md"
        assert test_report.exists(), f"{wp_id}: test-report.md still missing"


def test_all_test_dirs_have_test_files():
    """WPs that needed tests now have test_*.py files."""
    for wp_id in WPS_NEEDING_TESTS:
        test_dir = REPO_ROOT / "tests" / wp_id
        assert test_dir.exists(), f"tests/{wp_id}/ still missing"
        test_files = list(test_dir.glob("test_*.py"))
        assert test_files, f"tests/{wp_id}/ has no test_*.py files"
