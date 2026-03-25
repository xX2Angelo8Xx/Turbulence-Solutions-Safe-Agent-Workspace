"""GUI-023: Tests for template directory rename and launcher code updates.

Verifies:
- templates/agent-workbench/ exists (renamed from templates/coding/)
- templates/coding/ does NOT exist
- templates/certification-pipeline/ exists (renamed from templates/creative-marketing/)
- templates/creative-marketing/ does NOT exist
- _format_template_name() produces correct display names for new template names
- list_templates() returns the new template names
- is_template_ready() correctly identifies agent-workbench as ready
- is_template_ready() correctly identifies certification-pipeline as not ready
- TEMPLATES_DIR resolves to a valid directory
"""

import sys
from pathlib import Path

import pytest

# Locate the repository root (3 levels up from tests/GUI-023/)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"

sys.path.insert(0, str(REPO_ROOT / "src"))

from launcher.gui.app import _format_template_name
from launcher.core.project_creator import list_templates, is_template_ready


# ---------------------------------------------------------------------------
# Directory existence checks
# ---------------------------------------------------------------------------

def test_agent_workbench_directory_exists():
    assert (TEMPLATES_DIR / "agent-workbench").is_dir(), \
        "templates/agent-workbench/ must exist after rename"


def test_coding_directory_does_not_exist():
    assert not (TEMPLATES_DIR / "coding").exists(), \
        "templates/coding/ must NOT exist after rename to agent-workbench"


def test_certification_pipeline_directory_exists():
    assert (TEMPLATES_DIR / "certification-pipeline").is_dir(), \
        "templates/certification-pipeline/ must exist after rename"


def test_creative_marketing_directory_does_not_exist():
    assert not (TEMPLATES_DIR / "creative-marketing").exists(), \
        "templates/creative-marketing/ must NOT exist after rename to certification-pipeline"


# ---------------------------------------------------------------------------
# _format_template_name()
# ---------------------------------------------------------------------------

def test_format_agent_workbench():
    assert _format_template_name("agent-workbench") == "Agent Workbench"


def test_format_certification_pipeline():
    assert _format_template_name("certification-pipeline") == "Certification Pipeline"


# ---------------------------------------------------------------------------
# list_templates()
# ---------------------------------------------------------------------------

def test_list_templates_contains_agent_workbench():
    names = list_templates(TEMPLATES_DIR)
    assert "agent-workbench" in names


def test_list_templates_contains_certification_pipeline():
    names = list_templates(TEMPLATES_DIR)
    assert "certification-pipeline" in names


def test_list_templates_does_not_contain_coding():
    names = list_templates(TEMPLATES_DIR)
    assert "coding" not in names


def test_list_templates_does_not_contain_creative_marketing():
    names = list_templates(TEMPLATES_DIR)
    assert "creative-marketing" not in names


def test_list_templates_returns_sorted():
    names = list_templates(TEMPLATES_DIR)
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# is_template_ready()
# ---------------------------------------------------------------------------

def test_agent_workbench_is_ready():
    assert is_template_ready(TEMPLATES_DIR, "agent-workbench") is True, \
        "agent-workbench template has more than just README.md"


def test_certification_pipeline_is_not_ready():
    assert is_template_ready(TEMPLATES_DIR, "certification-pipeline") is False, \
        "certification-pipeline only has README.md — not ready yet"


def test_is_template_ready_nonexistent_returns_false():
    assert is_template_ready(TEMPLATES_DIR, "coding") is False
    assert is_template_ready(TEMPLATES_DIR, "creative-marketing") is False


# ---------------------------------------------------------------------------
# TEMPLATES_DIR sanity
# ---------------------------------------------------------------------------

def test_templates_dir_is_valid_directory():
    assert TEMPLATES_DIR.is_dir(), "TEMPLATES_DIR must resolve to an existing directory"


def test_templates_dir_from_config():
    from launcher.config import TEMPLATES_DIR as CONFIG_TEMPLATES_DIR
    assert CONFIG_TEMPLATES_DIR.is_dir()
    names = list_templates(CONFIG_TEMPLATES_DIR)
    assert "agent-workbench" in names
    assert "certification-pipeline" in names
