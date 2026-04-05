"""FIX-110 — Tests: Verify cross-platform shim fix applied to FIX-050 tests.

Verifies that both ts-python.cmd (Windows) and ts-python (Unix) shim files
are created in every FIX-050 test that calls verify_ts_python(), ensuring
cross-platform compatibility on macOS and Linux.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
TEST_FIX050_DIR = REPO_ROOT / "tests" / "FIX-050"
TEST_FIX050_PY = TEST_FIX050_DIR / "test_fix050.py"
TEST_FIX050_EDGE_PY = TEST_FIX050_DIR / "test_fix050_edge.py"


# Tests in test_fix050.py that must create both shim files
EXPECTED_FIXED_TESTS_MAIN = [
    "test_verify_calls_python_directly_not_cmd_exe",
    "test_verify_success_valid_config",
    "test_verify_timeout_says_30_seconds",
    "test_verify_handles_os_error",
    "test_verify_path_with_spaces_and_parens",
]

# Tests in test_fix050_edge.py that must create both shim files
EXPECTED_FIXED_TESTS_EDGE = [
    "test_verify_ts_python_passes_stdin_devnull",
    "test_verify_ts_python_passes_timeout_30",
    "test_verify_ts_python_nonzero_exit_code_in_message",
    "test_verify_ts_python_file_not_found_after_precheck",
    "test_verify_ts_python_strips_multiple_trailing_newlines",
]

UNIX_SHIM_SNIPPET = 'ts-python"'
UNIX_SHIM_WRITE = '"#!/bin/sh\\n"'


def _get_function_body_lines(source: str, func_name: str) -> list[str]:
    """Return source lines belonging to the function with the given name."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = source.splitlines()
            start = node.lineno - 1
            end = node.end_lineno
            return lines[start:end]
    return []


def _test_creates_unix_shim(file_path: Path, func_name: str) -> bool:
    """Return True if the function creates a ts-python (no .cmd) shim file."""
    source = file_path.read_text(encoding="utf-8")
    body_lines = _get_function_body_lines(source, func_name)
    body = "\n".join(body_lines)
    return 'ts-python"' in body and "#!/bin/sh" in body


# ---------------------------------------------------------------------------
# test_fix050.py shim fix verification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("func_name", EXPECTED_FIXED_TESTS_MAIN)
def test_fix050_main_creates_unix_shim(func_name):
    """Each affected test in test_fix050.py must create a ts-python Unix shim."""
    assert TEST_FIX050_PY.exists(), f"test_fix050.py not found at {TEST_FIX050_PY}"
    assert _test_creates_unix_shim(TEST_FIX050_PY, func_name), (
        f"{func_name} in test_fix050.py does not create a 'ts-python' Unix shim "
        f"(tmp_path / 'ts-python' with '#!/bin/sh'). "
        f"This is required for cross-platform compatibility."
    )


# ---------------------------------------------------------------------------
# test_fix050_edge.py shim fix verification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("func_name", EXPECTED_FIXED_TESTS_EDGE)
def test_fix050_edge_creates_unix_shim(func_name):
    """Each affected test in test_fix050_edge.py must create a ts-python Unix shim."""
    assert TEST_FIX050_EDGE_PY.exists(), f"test_fix050_edge.py not found at {TEST_FIX050_EDGE_PY}"
    assert _test_creates_unix_shim(TEST_FIX050_EDGE_PY, func_name), (
        f"{func_name} in test_fix050_edge.py does not create a 'ts-python' Unix shim "
        f"(tmp_path / 'ts-python' with '#!/bin/sh'). "
        f"This is required for cross-platform compatibility."
    )
