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
    assert "setuptools" in build["build-backend"]


def test_pyproject_src_layout(pyproject: dict) -> None:
    where = pyproject["tool"]["setuptools"]["packages"]["find"]["where"]
    assert "src" in where, "setuptools packages.find.where must include 'src'"
