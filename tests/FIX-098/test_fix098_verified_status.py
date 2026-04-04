"""FIX-098: Add Verified Bug Status

Verifies that update_bug_status.VALID_STATUSES contains 'Verified' and
matches the VALID_BUG_STATUS set from validate_workspace.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure scripts/ is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import update_bug_status  # noqa: E402
import validate_workspace  # noqa: E402


def test_valid_statuses_contains_verified() -> None:
    """VALID_STATUSES in update_bug_status must include 'Verified'."""
    assert "Verified" in update_bug_status.VALID_STATUSES


def test_valid_statuses_matches_validate_workspace() -> None:
    """VALID_STATUSES must equal VALID_BUG_STATUSES from validate_workspace."""
    assert update_bug_status.VALID_STATUSES == validate_workspace.VALID_BUG_STATUSES


def test_verified_accepted_as_cli_argument() -> None:
    """Argparse must accept --status Verified without raising SystemExit."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(update_bug_status.VALID_STATUSES),
    )
    args = parser.parse_args(["--status", "Verified"])
    assert args.status == "Verified"


def test_verified_status_updates_csv(tmp_path: Path) -> None:
    """main() must succeed (return 0) when setting a bug to Verified."""
    bugs_csv = tmp_path / "bugs.csv"
    bugs_csv.write_text(
        "ID,Title,Status,Severity,Component,Description,Steps,Expected,Actual,"
        "Fixed In WP,Reporter\n"
        "BUG-001,Test bug,Fixed,Low,Scripts,desc,steps,exp,act,,tester\n",
        encoding="utf-8",
    )

    with (
        patch.object(update_bug_status, "CSV_PATH", bugs_csv),
        patch("sys.argv", ["update_bug_status.py", "BUG-001", "--status", "Verified"]),
    ):
        result = update_bug_status.main()

    assert result == 0
    content = bugs_csv.read_text(encoding="utf-8")
    assert "Verified" in content


def test_all_valid_statuses_accepted_by_argparse() -> None:
    """Every status in VALID_STATUSES must parse successfully as --status value."""
    for status in update_bug_status.VALID_STATUSES:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--status",
            required=True,
            choices=sorted(update_bug_status.VALID_STATUSES),
        )
        args = parser.parse_args(["--status", status])
        assert args.status == status


def test_invalid_status_rejected() -> None:
    """Argparse must reject statuses not in VALID_STATUSES."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(update_bug_status.VALID_STATUSES),
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["--status", "Pending"])
