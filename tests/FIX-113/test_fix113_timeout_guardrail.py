"""
FIX-113 regression tests -- Prevent infinite-recursion and hanging tests.

Verifies:
1. pyproject.toml contains [tool.pytest.ini_options] with timeout = 30
2. pytest-timeout is listed in dev dependencies
3. testing-protocol.md contains the subprocess recursion safety rule
4. testing-protocol.md contains the subprocess timeout requirement
5. test_mnt029_edge_cases.py does NOT spawn subprocess pytest on full suite
6. No test file in tests/ spawns pytest on the entire tests/ directory
   (which causes infinite recursion when that file is itself discovered)
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PROTOCOL = REPO_ROOT / "docs" / "work-rules" / "testing-protocol.md"
MNT029_TEST = REPO_ROOT / "tests" / "MNT-029" / "test_mnt029_edge_cases.py"


def _has_full_suite_subprocess(text):
    """Return True if text contains subprocess.run targeting the root tests/ directory."""
    if "subprocess.run" not in text:
        return False
    # Dangerous pattern: "tests/" or 'tests/' as a bare path argument
    # (NOT "tests/FIX-047/" or similar sub-folder paths that are safe)
    return '"tests/"' in text or "'tests/'" in text


def test_pyproject_has_timeout_ini_option():
    """pyproject.toml must declare timeout = 30 in [tool.pytest.ini_options]."""
    content = PYPROJECT.read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in content, (
        "pyproject.toml missing [tool.pytest.ini_options] section"
    )
    in_section = False
    for line in content.splitlines():
        if line.strip() == "[tool.pytest.ini_options]":
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("["):
                break
            m = re.match(r"^\s*timeout\s*=\s*(\d+)", line)
            if m:
                assert int(m.group(1)) == 30, (
                    f"Expected timeout = 30, got timeout = {m.group(1)}"
                )
                return
    raise AssertionError(
        "pyproject.toml [tool.pytest.ini_options] does not contain 'timeout = 30'"
    )


def test_pyproject_has_pytest_timeout_dependency():
    """pytest-timeout must be listed in [project.optional-dependencies] dev."""
    content = PYPROJECT.read_text(encoding="utf-8")
    assert "pytest-timeout" in content, (
        "pyproject.toml dev dependencies do not include pytest-timeout"
    )


def test_protocol_has_subprocess_recursion_rule():
    """testing-protocol.md must prohibit spawning a full pytest run via subprocess."""
    content = PROTOCOL.read_text(encoding="utf-8")
    assert "MUST NOT spawn a full `pytest` run" in content, (
        "testing-protocol.md missing rule 8 text about subprocess pytest recursion"
    )


def test_protocol_has_subprocess_timeout_requirement():
    """testing-protocol.md must require timeout= on all subprocess.run() calls."""
    content = PROTOCOL.read_text(encoding="utf-8")
    # Check key phrases from rule 8 are all present
    assert "subprocess.run()" in content
    assert "MUST include a" in content
    assert "`timeout=`" in content


def test_mnt029_test_does_not_spawn_full_suite_subprocess():
    """test_mnt029_edge_cases.py must not spawn subprocess pytest on the full suite."""
    content = MNT029_TEST.read_text(encoding="utf-8")
    assert not _has_full_suite_subprocess(content), (
        "test_mnt029_edge_cases.py still invokes subprocess pytest on full tests/ directory"
    )


def test_no_test_file_runs_full_suite_via_subprocess():
    """No test file may run full-suite pytest via subprocess (causes infinite recursion).

    Targeted sub-folder runs (e.g. tests/FIX-047/) are allowed.
    This file itself is excluded from the scan (it contains the pattern as code,
    not as an active subprocess call).
    """
    tests_dir = REPO_ROOT / "tests"
    this_file = Path(__file__).resolve()
    offenders = [
        str(f.relative_to(REPO_ROOT))
        for f in tests_dir.rglob("test_*.py")
        if f.resolve() != this_file
        and _has_full_suite_subprocess(f.read_text(encoding="utf-8"))
    ]
    assert not offenders, (
        "Test files invoking full-suite subprocess pytest (infinite recursion risk):\n"
        + "\n".join(f"  {o}" for o in sorted(offenders))
    )
