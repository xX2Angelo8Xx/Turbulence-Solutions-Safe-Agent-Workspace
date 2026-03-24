"""FIX-064 — Edge-case tests: no hardcoded version strings in FIX-050 test file.

Covers:
1. test_fix050.py contains no hardcoded "3.0.2" version string
2. test_fix050.py imports CURRENT_VERSION from tests.shared.version_utils
3. All 5 version assertion functions in test_fix050.py use CURRENT_VERSION
4. CURRENT_VERSION can be imported without error from version_utils
5. version_utils.py uses regex to extract version (not hardcoded)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
TEST_FILE = REPO_ROOT / "tests" / "FIX-050" / "test_fix050.py"
VERSION_UTILS = REPO_ROOT / "tests" / "shared" / "version_utils.py"


# ---------------------------------------------------------------------------
# 1. No hardcoded "3.0.2" in test_fix050.py
# ---------------------------------------------------------------------------

def test_no_hardcoded_302_version_string():
    """test_fix050.py must not contain the hardcoded string '3.0.2'."""
    content = TEST_FILE.read_text(encoding="utf-8")
    assert "3.0.2" not in content, (
        "test_fix050.py still contains the hardcoded version '3.0.2'. "
        "FIX-064 should have replaced it with CURRENT_VERSION."
    )


# ---------------------------------------------------------------------------
# 2. CURRENT_VERSION import is present in test_fix050.py
# ---------------------------------------------------------------------------

def test_current_version_imported_in_test_fix050():
    """test_fix050.py must import CURRENT_VERSION from tests.shared.version_utils."""
    content = TEST_FILE.read_text(encoding="utf-8")
    assert "from tests.shared.version_utils import CURRENT_VERSION" in content, (
        "test_fix050.py does not import CURRENT_VERSION. "
        "The dynamic version pattern requires this import."
    )


# ---------------------------------------------------------------------------
# 3. All 5 version functions use CURRENT_VERSION (not hardcoded string)
# ---------------------------------------------------------------------------

VERSION_TESTS = [
    "test_config_py_version",
    "test_pyproject_toml_version",
    "test_setup_iss_version",
    "test_build_dmg_sh_version",
    "test_build_appimage_sh_version",
]


@pytest.mark.parametrize("fn_name", VERSION_TESTS)
def test_version_function_uses_current_version(fn_name: str):
    """Each of the 5 version assertion functions must reference CURRENT_VERSION."""
    content = TEST_FILE.read_text(encoding="utf-8")

    # Find the function body
    pattern = rf"def {fn_name}\(.*?\):.*?(?=\ndef |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    assert match, f"Function {fn_name!r} not found in test_fix050.py."

    func_body = match.group(0)
    assert "CURRENT_VERSION" in func_body, (
        f"{fn_name} does not reference CURRENT_VERSION. "
        "It may still use a hardcoded version string."
    )
    # Ensure no hardcoded version strings that look like semver remain
    hardcoded = re.findall(r'"(\d+\.\d+\.\d+)"', func_body)
    assert not hardcoded, (
        f"{fn_name} contains hardcoded version string(s): {hardcoded}. "
        "Use CURRENT_VERSION instead."
    )


# ---------------------------------------------------------------------------
# 4. CURRENT_VERSION can be imported cleanly
# ---------------------------------------------------------------------------

def test_current_version_importable():
    """CURRENT_VERSION from version_utils must be importable and non-empty."""
    from tests.shared.version_utils import CURRENT_VERSION  # noqa: PLC0415
    assert isinstance(CURRENT_VERSION, str), "CURRENT_VERSION must be a string."
    assert len(CURRENT_VERSION) > 0, "CURRENT_VERSION must not be empty."
    # Must look like semver: digits.digits.digits (optionally more)
    assert re.match(r"^\d+\.\d+\.\d+", CURRENT_VERSION), (
        f"CURRENT_VERSION {CURRENT_VERSION!r} does not look like a valid semver string."
    )


# ---------------------------------------------------------------------------
# 5. version_utils.py uses regex extraction, not hardcoded value
# ---------------------------------------------------------------------------

def test_version_utils_uses_regex_not_hardcoded():
    """version_utils.py must extract the version via regex, not hardcode it."""
    content = VERSION_UTILS.read_text(encoding="utf-8")
    # Must contain a regex search call
    assert "re.search" in content, (
        "version_utils.py must use re.search() to extract the version dynamically."
    )
    # Must NOT contain any hardcoded semver literal like "3.0.2"
    semver_literals = re.findall(r'["\'](\d+\.\d+\.\d+)["\']', content)
    assert not semver_literals, (
        f"version_utils.py contains hardcoded version literal(s): {semver_literals}. "
        "All versions must be read dynamically from config.py."
    )
