"""Edge-case tests for FIX-052 — Additional regression guards.

Covers scenarios beyond the developer's tests:
  1. No ANY quoted version literal (X.Y.Z) hardcoded in FIX-047 test source.
  2. version_utils.py itself reads dynamically from config.py (no hardcoded fallback).
  3. CURRENT_VERSION is a valid SemVer string (X.Y.Z format).
  4. CURRENT_VERSION matches what config.py declares (integration).
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIX047_TEST_FILE = REPO_ROOT / "tests" / "FIX-047" / "test_fix047_version.py"
VERSION_UTILS_FILE = REPO_ROOT / "tests" / "shared" / "version_utils.py"
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"

# Add shared path so we can import version_utils directly
sys.path.insert(0, str(REPO_ROOT / "tests" / "shared"))
from version_utils import CURRENT_VERSION


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Edge case 1: No quoted version literals of ANY X.Y.Z form in FIX-047 test
# ---------------------------------------------------------------------------

def test_no_any_hardcoded_version_literal_in_fix047_test():
    """FIX-047 test must not contain ANY quoted version literal like '3.0.4' or similar."""
    source = _read(FIX047_TEST_FILE)
    # Find all quoted X.Y.Z patterns
    matches = re.findall(r'["\'](\d+\.\d+\.\d+)["\']', source)
    assert matches == [], (
        f"FIX-047 test contains hardcoded version literal(s): {matches}. "
        "All version strings must come from CURRENT_VERSION (version_utils.py)."
    )


# ---------------------------------------------------------------------------
# Edge case 2: version_utils.py itself is not hardcoded
# ---------------------------------------------------------------------------

def test_version_utils_has_no_hardcoded_version_constant():
    """version_utils.py must not contain a hardcoded X.Y.Z version string."""
    source = _read(VERSION_UTILS_FILE)
    # Only the regex pattern r"..." should contain \d+ sequences — not a literal version
    quoted_versions = re.findall(r'["\'](\d+\.\d+\.\d+)["\']', source)
    assert quoted_versions == [], (
        f"version_utils.py contains hardcoded version literal(s): {quoted_versions}. "
        "It must derive the version dynamically via regex from config.py."
    )


# ---------------------------------------------------------------------------
# Edge case 3: CURRENT_VERSION has valid SemVer format
# ---------------------------------------------------------------------------

def test_current_version_is_valid_semver():
    """CURRENT_VERSION must match the X.Y.Z SemVer format."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", CURRENT_VERSION), (
        f"CURRENT_VERSION {CURRENT_VERSION!r} is not a valid SemVer (X.Y.Z) string."
    )


# ---------------------------------------------------------------------------
# Edge case 4: CURRENT_VERSION matches config.py directly
# ---------------------------------------------------------------------------

def test_current_version_matches_config_py():
    """version_utils.CURRENT_VERSION must equal VERSION declared in config.py."""
    config_source = _read(CONFIG_PY)
    match = re.search(
        r'^VERSION\s*:\s*str\s*=\s*["\']([^"\']+)["\']',
        config_source,
        re.MULTILINE,
    )
    assert match is not None, "Could not find VERSION constant in config.py"
    config_version = match.group(1)
    assert CURRENT_VERSION == config_version, (
        f"version_utils.CURRENT_VERSION ({CURRENT_VERSION!r}) does not match "
        f"config.py VERSION ({config_version!r})."
    )
