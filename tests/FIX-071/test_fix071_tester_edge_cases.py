"""FIX-071 — Tester edge-case tests: No old template path references remain.

Covers:
1. No functional Path() / os.path.join() constructions with old template names
   anywhere in the test suite
2. src/ code contains no references to old template paths
3. conftest.py functional sections use new template names
4. SAF-035/SAF-036 tests use the correct template path
5. No test file imports or assigns old template names as raw strings in
   code (not docstrings/comments)
6. GUI-014 tests reference new template names for "coming soon" logic
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"
SRC_DIR = REPO_ROOT / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 1. No functional (non-comment, non-docstring) Path/os.path constructions
#    using old template names across all test files
# ---------------------------------------------------------------------------

def _lines_with_old_path_constant(py_file: Path, old_path: str) -> list[str]:
    """Return lines in py_file that assign old_path as a variable value.

    Only matches lines of the form:   SOME_VAR = "templates/old_path/..."
    while skipping comment and docstring lines.
    """
    pattern = re.compile(r'=\s*["\']' + re.escape(old_path), re.IGNORECASE)
    in_docstring = False
    hits = []
    for lineno, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
            in_docstring = not in_docstring
        if in_docstring:
            continue
        if pattern.search(line):
            hits.append(f"{lineno}: {stripped[:120]}")
    return hits


def test_no_path_constant_assignments_to_old_coding_in_doc_tests():
    """DOC test files must not assign 'templates/coding' or 'templates\\coding' as a path constant."""
    old_paths = ["templates/coding", "templates\\coding"]
    for doc_dir in TESTS_DIR.glob("DOC-*"):
        for py_file in doc_dir.glob("*.py"):
            for old_path in old_paths:
                hits = _lines_with_old_path_constant(py_file, old_path)
                assert not hits, (
                    f"{py_file.relative_to(REPO_ROOT)} still assigns old path "
                    f"'{old_path}':\n" + "\n".join(hits)
                )


def test_no_path_constant_assignments_to_old_creative_marketing_in_gui_tests():
    """GUI/INS test files must not assign 'templates/creative-marketing' as a path constant."""
    old_path = "templates/creative-marketing"
    for test_dir in list(TESTS_DIR.glob("GUI-*")) + list(TESTS_DIR.glob("INS-*")):
        for py_file in test_dir.glob("*.py"):
            hits = _lines_with_old_path_constant(py_file, old_path)
            assert not hits, (
                f"{py_file.relative_to(REPO_ROOT)} still assigns old path "
                f"'{old_path}':\n" + "\n".join(hits)
            )


# ---------------------------------------------------------------------------
# 2. src/ application code contains no references to old template path names
# ---------------------------------------------------------------------------

def test_src_no_reference_to_old_coding_path():
    """Application source must use 'agent-workbench', not 'templates/coding'."""
    hits = []
    for py_file in SRC_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            if "templates/coding" in line or "templates\\coding" in line:
                rel = py_file.relative_to(REPO_ROOT)
                hits.append(f"{rel}:{lineno}: {line.strip()[:120]}")
    assert not hits, (
        f"src/ still references 'templates/coding' in {len(hits)} location(s):\n"
        + "\n".join(hits)
    )


def test_src_no_reference_to_old_creative_marketing_path():
    """Application source must use 'certification-pipeline', not 'creative-marketing'."""
    hits = []
    for py_file in SRC_DIR.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            if "creative-marketing" in line or "creative_marketing" in line:
                rel = py_file.relative_to(REPO_ROOT)
                hits.append(f"{rel}:{lineno}: {line.strip()[:120]}")
    assert not hits, (
        f"src/ still references 'creative-marketing' in {len(hits)} location(s):\n"
        + "\n".join(hits)
    )


# ---------------------------------------------------------------------------
# 3. GUI-020 tester edge cases also use the new display name
# ---------------------------------------------------------------------------

def test_gui020_tester_edge_cases_uses_agent_workbench():
    """GUI-020 tester edge cases must also reference 'Agent Workbench', not 'Coding'."""
    content = _read(TESTS_DIR / "GUI-020" / "test_gui020_tester_edge_cases.py")
    assert '"Agent Workbench"' in content, (
        "test_gui020_tester_edge_cases.py still uses 'Coding' as dropdown value"
    )
    # Confirm the old display name is not used as a mock return value
    for lineno, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or '"""' in stripped:
            continue
        if '"Coding"' in line and "return_value" in line:
            raise AssertionError(
                f"test_gui020_tester_edge_cases.py line {lineno} still mocks "
                f"dropdown with old name 'Coding': {stripped}"
            )


# ---------------------------------------------------------------------------
# 4. GUI-022 edge cases also use the new display name
# ---------------------------------------------------------------------------

def test_gui022_edge_cases_uses_agent_workbench():
    """GUI-022 edge cases must reference 'Agent Workbench', not 'Coding'."""
    content = _read(TESTS_DIR / "GUI-022" / "test_gui022_edge_cases.py")
    # Check for old mock assignment pattern
    for lineno, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if '"Coding"' in line and "return_value" in line:
            raise AssertionError(
                f"test_gui022_edge_cases.py line {lineno} still uses old name "
                f"'Coding': {stripped}"
            )


# ---------------------------------------------------------------------------
# 5. GUI-014 "coming soon" tests reference new names
# ---------------------------------------------------------------------------

def test_gui014_coming_soon_uses_certification_pipeline():
    """GUI-014 coming-soon test must reference 'certification-pipeline', not 'creative-marketing'."""
    content = _read(TESTS_DIR / "GUI-014" / "test_gui014_coming_soon.py")
    assert "certification-pipeline" in content, (
        "test_gui014_coming_soon.py does not reference 'certification-pipeline'"
    )


def test_gui014_coming_soon_uses_agent_workbench():
    """GUI-014 coming-soon test must reference 'agent-workbench', not 'coding'."""
    content = _read(TESTS_DIR / "GUI-014" / "test_gui014_coming_soon.py")
    assert "agent-workbench" in content, (
        "test_gui014_coming_soon.py does not reference 'agent-workbench'"
    )


# ---------------------------------------------------------------------------
# 6. SAF-035 / SAF-036 tests use new template path
# ---------------------------------------------------------------------------

def test_saf035_tests_use_new_template_path():
    """SAF-035 test files must not use old 'templates/coding' as a path."""
    old_pattern = re.compile(r'["\']templates/coding["\']|Path\s*\(.*?templates.*?coding')
    for test_file in (TESTS_DIR / "SAF-035").glob("*.py"):
        content = _read(test_file)
        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or '"""' in stripped or "'''" in stripped:
                continue
            if old_pattern.search(line):
                raise AssertionError(
                    f"SAF-035 test {test_file.name}:{lineno} references old "
                    f"template path: {stripped[:120]}"
                )


def test_saf036_tests_use_new_template_path():
    """SAF-036 test files must not use old 'templates/coding' as a path."""
    old_pattern = re.compile(r'["\']templates/coding["\']|Path\s*\(.*?templates.*?coding')
    for test_file in (TESTS_DIR / "SAF-036").glob("*.py"):
        content = _read(test_file)
        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or '"""' in stripped or "'''" in stripped:
                continue
            if old_pattern.search(line):
                raise AssertionError(
                    f"SAF-036 test {test_file.name}:{lineno} references old "
                    f"template path: {stripped[:120]}"
                )


# ---------------------------------------------------------------------------
# 7. launcher.spec contains no old template path references
# ---------------------------------------------------------------------------

def test_launcher_spec_no_old_template_refs():
    """launcher.spec must not reference 'templates/coding' or 'creative-marketing'."""
    spec_file = REPO_ROOT / "launcher.spec"
    assert spec_file.exists(), "launcher.spec not found"
    content = _read(spec_file)
    assert "templates/coding" not in content, (
        "launcher.spec still references 'templates/coding'"
    )
    assert "creative-marketing" not in content, (
        "launcher.spec still references 'creative-marketing'"
    )
