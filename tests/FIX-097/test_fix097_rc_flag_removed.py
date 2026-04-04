"""Regression tests for FIX-097 — --rc flag removed from release.py.

Verifies that:
  1. --rc is no longer a recognised argument in release.py
  2. args.rc is not referenced anywhere in the source
  3. The help text documents that all releases are drafts
  4. --dry-run still works correctly (no regression)
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
RELEASE_PY = REPO_ROOT / "scripts" / "release.py"
PYTHON = sys.executable


def _run_release(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(RELEASE_PY)] + list(args),
        capture_output=capture,
        text=True,
    )


def test_rc_flag_not_in_argparse():
    """Passing --rc to release.py must produce a non-zero exit (unrecognised argument)."""
    result = _run_release("1.0.0", "--rc")
    assert result.returncode != 0, (
        "--rc was accepted by release.py but should have been removed (FIX-097)"
    )
    combined = result.stdout + result.stderr
    assert "unrecognized" in combined.lower() or "error" in combined.lower(), (
        "Expected an argument-error message when --rc is passed, got: " + combined
    )


def test_args_rc_not_referenced_in_source():
    """The source code of release.py must not reference args.rc."""
    source = RELEASE_PY.read_text(encoding="utf-8")
    assert "args.rc" not in source, (
        "release.py still references args.rc — the --rc flag was not fully removed (FIX-097)"
    )


def test_help_text_mentions_draft():
    """The --help output of release.py must mention that releases are drafts."""
    result = _run_release("--help")
    # argparse --help exits with code 0
    assert result.returncode == 0, f"--help exited with non-zero code: {result.returncode}"
    combined = result.stdout + result.stderr
    assert "draft" in combined.lower(), (
        "--help output does not mention 'draft' — the draft nature of releases is undocumented"
    )


def test_dry_run_still_works():
    """--dry-run must still be a recognised argument after removing --rc."""
    result = _run_release("1.2.3", "--dry-run")
    # dry-run exits 0 and prints DRY-RUN output
    assert result.returncode == 0, (
        f"--dry-run failed after FIX-097 changes (exit {result.returncode}):\n"
        + result.stdout
        + result.stderr
    )
    assert "DRY-RUN" in result.stdout or "dry" in result.stdout.lower(), (
        "--dry-run did not produce expected dry-run output after FIX-097 changes"
    )
