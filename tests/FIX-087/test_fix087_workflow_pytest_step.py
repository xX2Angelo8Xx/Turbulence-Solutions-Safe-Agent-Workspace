"""
FIX-087: Tests verifying that macos-source-test.yml has a pytest install step
before the test suite step.
"""
import os
import pytest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", ".github", "workflows", "macos-source-test.yml"
)
INSTALL_MACOS_SH_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "scripts", "install-macos.sh"
)

VENV_PIP = "~/.local/share/TurbulenceSolutions/venv/bin/pip"
VENV_PYTHON = "~/.local/share/TurbulenceSolutions/venv/bin/python"


def _read_workflow():
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return f.read()


def _read_install_sh():
    with open(INSTALL_MACOS_SH_PATH, encoding="utf-8") as f:
        return f.read()


def test_workflow_file_exists():
    """The workflow YAML file exists at the expected path."""
    assert os.path.isfile(WORKFLOW_PATH), f"Workflow file not found: {WORKFLOW_PATH}"


def test_install_pytest_step_present():
    """A step that installs pytest via the venv pip is present in the workflow."""
    content = _read_workflow()
    assert "pip install pytest" in content, (
        "No 'pip install pytest' found in macos-source-test.yml"
    )


def test_install_step_before_test_step():
    """The pytest install step appears before the 'Run test suite' step."""
    content = _read_workflow()
    install_idx = content.find("pip install pytest")
    test_idx = content.find("python -m pytest tests/")
    assert install_idx != -1, "pytest install step not found"
    assert test_idx != -1, "test suite run step not found"
    assert install_idx < test_idx, (
        "pytest install step must appear before the test suite step"
    )


def test_install_step_uses_venv_pip():
    """The install step uses the correct venv pip path."""
    content = _read_workflow()
    assert VENV_PIP in content, (
        f"Expected venv pip path '{VENV_PIP}' not found in workflow"
    )


def test_test_step_unchanged():
    """The original 'Run test suite with venv Python' step is still present."""
    content = _read_workflow()
    assert "Run test suite with venv Python" in content, (
        "The 'Run test suite with venv Python' step name is missing"
    )
    assert f"{VENV_PYTHON} -m pytest tests/ -x --tb=short" in content, (
        "The original pytest command is missing or changed"
    )


def test_install_macos_sh_unchanged():
    """install-macos.sh does NOT install pytest (production deps only)."""
    content = _read_install_sh()
    assert "pytest" not in content, (
        "install-macos.sh must NOT install pytest — production install must stay clean"
    )
