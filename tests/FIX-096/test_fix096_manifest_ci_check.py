"""
FIX-096: Fix MANIFEST CI Check Missing File

Regression tests verifying that both .github/workflows/test.yml and
.github/workflows/staging-test.yml exit with code 1 (not 0) when
MANIFEST.json is missing, so CI fails visibly instead of passing silently.
"""

from pathlib import Path


TEST_YML = Path(".github/workflows/test.yml")
STAGING_YML = Path(".github/workflows/staging-test.yml")


def _read_workflow(path: Path) -> str:
    """Read the workflow file from the repository root."""
    repo_root = Path(__file__).parent.parent.parent
    return (repo_root / path).read_text(encoding="utf-8")


def test_test_yml_does_not_exit_0_on_missing_manifest():
    """test.yml must not call sys.exit(0) when MANIFEST.json is missing."""
    content = _read_workflow(TEST_YML)
    # Find the manifest-check block — look for the missing-path branch
    # The old (buggy) code had sys.exit(0) immediately after the not-exists check
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1, "Could not locate the manifest missing-path check in test.yml"
    # Extract a window after the check (covers the two lines of the branch body)
    window = content[missing_block_idx: missing_block_idx + 200]
    # The first sys.exit in this window must NOT be sys.exit(0)
    exit_0_pos = window.find("sys.exit(0)")
    assert exit_0_pos == -1, (
        "test.yml still contains sys.exit(0) in the MANIFEST.json missing-path branch — "
        "CI would pass silently when MANIFEST.json is absent."
    )


def test_test_yml_exits_1_on_missing_manifest():
    """test.yml must call sys.exit(1) when MANIFEST.json is missing."""
    content = _read_workflow(TEST_YML)
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1, "Could not locate the manifest missing-path check in test.yml"
    window = content[missing_block_idx: missing_block_idx + 200]
    assert "sys.exit(1)" in window, (
        "test.yml does not call sys.exit(1) in the MANIFEST.json missing-path branch — "
        "CI would not fail when MANIFEST.json is absent."
    )


def test_test_yml_has_error_message_on_missing_manifest():
    """test.yml must print an informative ERROR message (not a WARNING/SKIP) when missing."""
    content = _read_workflow(TEST_YML)
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1
    window = content[missing_block_idx: missing_block_idx + 200]
    assert "ERROR:" in window, (
        "test.yml missing-manifest branch does not print an ERROR message."
    )
    assert "generate_manifest.py" in window, (
        "test.yml missing-manifest error message does not reference generate_manifest.py."
    )


def test_staging_yml_does_not_exit_0_on_missing_manifest():
    """staging-test.yml must not call sys.exit(0) when MANIFEST.json is missing."""
    content = _read_workflow(STAGING_YML)
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1, "Could not locate the manifest missing-path check in staging-test.yml"
    window = content[missing_block_idx: missing_block_idx + 200]
    exit_0_pos = window.find("sys.exit(0)")
    assert exit_0_pos == -1, (
        "staging-test.yml still contains sys.exit(0) in the MANIFEST.json missing-path branch — "
        "CI would pass silently when MANIFEST.json is absent."
    )


def test_staging_yml_exits_1_on_missing_manifest():
    """staging-test.yml must call sys.exit(1) when MANIFEST.json is missing."""
    content = _read_workflow(STAGING_YML)
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1, "Could not locate the manifest missing-path check in staging-test.yml"
    window = content[missing_block_idx: missing_block_idx + 200]
    assert "sys.exit(1)" in window, (
        "staging-test.yml does not call sys.exit(1) in the MANIFEST.json missing-path branch — "
        "CI would not fail when MANIFEST.json is absent."
    )


def test_staging_yml_has_error_message_on_missing_manifest():
    """staging-test.yml must print an informative ERROR message when missing."""
    content = _read_workflow(STAGING_YML)
    missing_block_idx = content.find("if not manifest_path.exists():")
    assert missing_block_idx != -1
    window = content[missing_block_idx: missing_block_idx + 200]
    assert "ERROR:" in window, (
        "staging-test.yml missing-manifest branch does not print an ERROR message."
    )
    assert "generate_manifest.py" in window, (
        "staging-test.yml missing-manifest error message does not reference generate_manifest.py."
    )
