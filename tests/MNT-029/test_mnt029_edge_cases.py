"""
MNT-029 edge-case tests (Tester-added).

Verifies:
- MANIFEST.json file_count field matches the actual files dict length
- regression-baseline.json has no stale entries (entries whose test files no
  longer exist on disk — detected via static analysis, not by running pytest)
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "tests" / "regression-baseline.json"
MANIFEST_PATH = REPO_ROOT / "templates" / "agent-workbench" / "MANIFEST.json"

# Dotted-path format for a baseline key: tests.<WP-ID>.test_module.<test_name>
# The module portion maps to tests/<WP-ID>/test_module.py on disk.
_KEY_RE = re.compile(r"^(tests\.[^.]+\.[^.]+)\..+$")


def test_manifest_file_count_matches_files_dict():
    """MANIFEST.json file_count must equal len(files)."""
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        data = json.load(f)
    declared = data["file_count"]
    actual = len(data["files"])
    assert declared == actual, (
        f"MANIFEST.json file_count={declared} does not match "
        f"actual files dict length={actual}"
    )


def test_baseline_no_stale_entries():
    """Every key in regression-baseline.json must follow the dotted-path format
    AND map to a .py test file that actually exists on disk.

    This catches entries where test files were deleted or renamed without
    updating the baseline. It does NOT run pytest — running pytest inside pytest
    causes infinite recursion (see FIX-113).
    """
    with open(BASELINE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    stale = []
    malformed = []
    for key in data["known_failures"]:
        m = _KEY_RE.match(key)
        if not m:
            malformed.append(key)
            continue
        # Convert dotted module path to file path: tests.WP-ID.test_mod -> tests/WP-ID/test_mod.py
        module_dotted = m.group(1)  # e.g. "tests.FIX-001.test_fix001"
        parts = module_dotted.split(".")
        file_path = REPO_ROOT.joinpath(*parts).with_suffix(".py")
        if not file_path.exists():
            stale.append(f"{key}  (missing: {file_path.relative_to(REPO_ROOT)})")

    messages = []
    if malformed:
        messages.append(
            f"Malformed baseline keys (not dotted-path format):\n"
            + "\n".join(f"  {k}" for k in sorted(malformed))
        )
    if stale:
        messages.append(
            f"Stale baseline entries (test file no longer exists):\n"
            + "\n".join(f"  {s}" for s in sorted(stale))
        )
    assert not messages, "\n\n".join(messages)
