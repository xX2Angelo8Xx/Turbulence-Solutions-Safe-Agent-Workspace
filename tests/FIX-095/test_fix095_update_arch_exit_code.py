"""Tests for FIX-095: update_architecture.py exit code fix.

Verifies that main() returns:
  - 1 when docs/architecture.md does not exist
  - 1 when the ## Repository Structure section is not found
  - 0 when the file is already up to date (no change needed)
  - 0 when the file is successfully updated
  - 0 in --dry-run mode
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import update_architecture as ua


MINIMAL_ARCH_WITH_SECTION = """\
# Architecture

## Repository Structure

```
├── scripts/
└── src/
```

Some trailing prose.
"""

MINIMAL_ARCH_WITHOUT_SECTION = """\
# Architecture

No repository structure section here.
"""


class TestUpdateArchExitCode:
    def test_exit_code_file_not_found(self, tmp_path):
        """main() returns 1 when architecture.md does not exist."""
        missing = tmp_path / "architecture.md"
        with patch.object(ua, "ARCH_PATH", missing), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
            assert rc == 1, "Expected exit code 1 when architecture.md is absent"

    def test_exit_code_pattern_not_found(self, tmp_path):
        """main() returns 1 when ## Repository Structure section is missing."""
        arch = tmp_path / "architecture.md"
        arch.write_text(MINIMAL_ARCH_WITHOUT_SECTION, encoding="utf-8")
        with patch.object(ua, "ARCH_PATH", arch), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
            assert rc == 1, "Expected exit code 1 when section header is absent"

    def test_exit_code_success_no_change(self, tmp_path):
        """main() returns 0 when architecture.md is already up to date."""
        arch = tmp_path / "architecture.md"
        arch.write_text(MINIMAL_ARCH_WITH_SECTION, encoding="utf-8")
        # Make build_repo_tree() return the current tree so nothing changes
        current_tree = "├── scripts/\n└── src/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=current_tree), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
            assert rc == 0, "Expected exit code 0 when file is already up to date"

    def test_exit_code_success_updated(self, tmp_path):
        """main() returns 0 when the file is successfully updated."""
        arch = tmp_path / "architecture.md"
        arch.write_text(MINIMAL_ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "├── scripts/\n├── src/\n└── tests/"
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree), \
             patch("sys.argv", ["update_architecture.py"]):
            rc = ua.main()
            assert rc == 0, "Expected exit code 0 after successful update"
            # Verify the file was actually written
            content = arch.read_text(encoding="utf-8")
            assert "tests/" in content

    def test_exit_code_dry_run(self, tmp_path):
        """main() returns 0 in --dry-run mode (no write, but not an error)."""
        arch = tmp_path / "architecture.md"
        arch.write_text(MINIMAL_ARCH_WITH_SECTION, encoding="utf-8")
        new_tree = "├── scripts/\n├── src/\n└── tests/"
        original_content = arch.read_text(encoding="utf-8")
        with patch.object(ua, "ARCH_PATH", arch), \
             patch.object(ua, "build_repo_tree", return_value=new_tree), \
             patch("sys.argv", ["update_architecture.py", "--dry-run"]):
            rc = ua.main()
            assert rc == 0, "Expected exit code 0 in dry-run mode"
            # File must not have been modified
            assert arch.read_text(encoding="utf-8") == original_content
