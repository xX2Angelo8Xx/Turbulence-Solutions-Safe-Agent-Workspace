"""Tests for INS-002: pyproject.toml Python packaging configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def pyproject() -> dict:
    with PYPROJECT_PATH.open("rb") as f:
        return tomllib.load(f)


def test_pyproject_exists() -> None:
    assert PYPROJECT_PATH.is_file(), "pyproject.toml not found at repository root"


def test_pyproject_is_valid_toml() -> None:
    with PYPROJECT_PATH.open("rb") as f:
        data = tomllib.load(f)
    assert isinstance(data, dict)


def test_pyproject_project_name(pyproject: dict) -> None:
    assert pyproject["project"]["name"] == "agent-environment-launcher"


def test_pyproject_version_matches_config(pyproject: dict) -> None:
    import sys
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from launcher.config import VERSION
    assert pyproject["project"]["version"] == VERSION


def test_pyproject_requires_python(pyproject: dict) -> None:
    assert "requires-python" in pyproject["project"]
    assert pyproject["project"]["requires-python"].startswith(">=3.")


def test_pyproject_customtkinter_dependency(pyproject: dict) -> None:
    deps = pyproject["project"]["dependencies"]
    assert any("customtkinter" in dep for dep in deps), (
        "customtkinter not found in project.dependencies"
    )


def test_pyproject_dev_dependencies(pyproject: dict) -> None:
    dev_deps = pyproject["project"]["optional-dependencies"]["dev"]
    dep_names = [d.split(">=")[0].split("~=")[0].split("==")[0].strip() for d in dev_deps]
    assert "pyinstaller" in dep_names, "pyinstaller missing from dev optional-dependencies"
    assert "pytest" in dep_names, "pytest missing from dev optional-dependencies"


def test_pyproject_entry_point(pyproject: dict) -> None:
    scripts = pyproject["project"]["scripts"]
    assert "agent-launcher" in scripts
    assert scripts["agent-launcher"] == "launcher.main:main"


def test_pyproject_build_system(pyproject: dict) -> None:
    build = pyproject["build-system"]
    assert "build-backend" in build
    assert build["build-backend"] == "setuptools.build_meta", (
        f"build-backend is '{build['build-backend']}' but must be 'setuptools.build_meta'"
    )


def test_pyproject_src_layout(pyproject: dict) -> None:
    where = pyproject["tool"]["setuptools"]["packages"]["find"]["where"]
    assert "src" in where, "setuptools packages.find.where must include 'src'"


# --- Tester edge-case tests (INS-002 re-review) ---

def test_pyproject_build_system_requires(pyproject: dict) -> None:
    """[build-system] requires must contain a setuptools entry with version bounds."""
    requires = pyproject["build-system"]["requires"]
    assert any("setuptools" in r for r in requires), (
        "setuptools not found in [build-system] requires"
    )
    setuptools_req = next(r for r in requires if "setuptools" in r)
    assert ">=" in setuptools_req, (
        f"setuptools requirement '{setuptools_req}' has no lower bound"
    )


def test_pyproject_requires_python_exact(pyproject: dict) -> None:
    """requires-python must be at least Python 3.11, not a looser bound."""
    requires_python = pyproject["project"]["requires-python"]
    # Must specify 3.11 or higher, not merely 3.0 or 3.9 etc.
    assert "3.11" in requires_python or "3.12" in requires_python or "3.13" in requires_python, (
        f"requires-python '{requires_python}' is too broad; expected >=3.11"
    )


def test_pyproject_customtkinter_upper_bound(pyproject: dict) -> None:
    """customtkinter dependency must have an upper bound to prevent silent breaking upgrades."""
    deps = pyproject["project"]["dependencies"]
    ctk_dep = next((d for d in deps if "customtkinter" in d), None)
    assert ctk_dep is not None, "customtkinter dependency not found"
    assert "<" in ctk_dep, (
        f"customtkinter dep '{ctk_dep}' has no upper bound; major-version pin required"
    )
