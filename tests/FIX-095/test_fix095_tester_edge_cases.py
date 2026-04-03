"""Tester-added edge cases for FIX-095: update_architecture.py exit code fix.

These tests go beyond the Developer's test suite to verify boundary conditions,
regression sentinels, and direct function-level behavior.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import update_architecture as ua


# --- Fixtures ---

ARCH_WITH_SECTION = """\
# Architecture

Some intro text.

## Repository Structure

```
├── scripts/
└── src/
```

Trailing prose.
"""

ARCH_WITHOUT_CODE_BLOCK = """\
# Architecture

## Repository Structure

No code block here — just text.
"""


# --- Regression Sentinel ---

class TestRegressionSentinel:
    """Sentinel test: documents the pre-fix bug and verifies it cannot recur."""

    def test_main_returns_nonzero_on_missing_file(self, tmp_path):
        """REGRESSION: main() returned 0 even when architecture.md was absent.
        It must now return 1.
        """
        missing = tmp_path / "does_not_exist.md"
        with patch.object(ua, "ARCH_PATH", missing), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
        assert rc != 0, (
            "REGRESSION: main() returned 0 when architecture.md is missing. "
            "Pre-fix behavior has returned."
        )
        assert rc == 1, f"Expected exit code 1 for missing file, got {rc}"

    def test_main_returns_nonzero_on_missing_section(self, tmp_path):
        """REGRESSION: main() returned 0 even when the section header was absent.
        It must now return 1.
        """
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITHOUT_CODE_BLOCK, encoding="utf-8")
        with patch.object(ua, "ARCH_PATH", arch), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
        assert rc != 0, (
            "REGRESSION: main() returned 0 when ## Repository Structure block "
            "is absent. Pre-fix behavior has returned."
        )
        assert rc == 1, f"Expected exit code 1 for missing section, got {rc}"


# --- Direct function-level tests ---

class TestUpdateArchitectureDirect:
    """Test update_architecture() return values directly (not via main())."""

    def test_returns_false_when_file_missing(self, tmp_path):
        """update_architecture() returns False when architecture.md doesn't exist."""
        missing = tmp_path / "architecture.md"
        with patch.object(ua, "ARCH_PATH", missing):
            result = ua.update_architecture()
        assert result is False

    def test_returns_false_when_pattern_missing(self, tmp_path):
        """update_architecture() returns False when section header is absent."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITHOUT_CODE_BLOCK, encoding="utf-8")
        with patch.object(ua, "ARCH_PATH", arch):
            result = ua.update_architecture()
        assert result is False

    def test_returns_true_after_successful_write(self, tmp_path):
        """update_architecture() returns True after writing a new tree."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "├── scripts/\n├── src/\n└── tests/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree):
            result = ua.update_architecture()
        assert result is True

    def test_returns_true_when_already_up_to_date(self, tmp_path):
        """update_architecture() returns True (not False) when no change needed."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        current_tree = "├── scripts/\n└── src/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=current_tree):
            result = ua.update_architecture()
        assert result is True, (
            "update_architecture() must return True (not False) when already "
            "up to date — False is reserved for error conditions."
        )

    def test_returns_true_in_dry_run(self, tmp_path):
        """update_architecture() returns True (not False) in dry-run mode."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "├── scripts/\n├── src/\n└── tests/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree):
            result = ua.update_architecture(dry_run=True)
        assert result is True, (
            "update_architecture() must return True (not False) in dry-run "
            "mode — dry-run is a success, not an error."
        )


# --- Content-integrity tests ---

class TestContentIntegrity:
    """Verify surrounding content is preserved on update."""

    def test_prose_before_section_preserved(self, tmp_path):
        """Text before ## Repository Structure is not modified on update."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "└── tests/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree):
            ua.update_architecture()
        content = arch.read_text(encoding="utf-8")
        assert "Some intro text." in content

    def test_prose_after_section_preserved(self, tmp_path):
        """Text after the code block is not modified on update."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "└── tests/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree):
            ua.update_architecture()
        content = arch.read_text(encoding="utf-8")
        assert "Trailing prose." in content

    def test_dry_run_does_not_write(self, tmp_path):
        """dry_run=True must not modify the file on disk."""
        arch = tmp_path / "architecture.md"
        arch.write_text(ARCH_WITH_SECTION, encoding="utf-8")
        original = arch.read_text(encoding="utf-8")
        new_tree = "└── something_new/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree):
            ua.update_architecture(dry_run=True)
        assert arch.read_text(encoding="utf-8") == original, (
            "dry_run=True must not write the file to disk."
        )
