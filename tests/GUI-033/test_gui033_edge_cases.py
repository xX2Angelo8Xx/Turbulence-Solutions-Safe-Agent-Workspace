"""Edge-case tests for GUI-033: Rename workspace prefix TS-SAE to SAE.

Tester-added edge cases covering boundary conditions and security aspects.
"""

import pytest
from pathlib import Path

from launcher.core.project_creator import create_project, replace_template_placeholders


def _make_minimal_template(tmp_path: Path) -> Path:
    """Create a minimal template directory suitable for create_project."""
    template = tmp_path / "template"
    template.mkdir()
    (template / "Project").mkdir()
    (template / "Project" / "README.md").write_text(
        "# {{PROJECT_NAME}}\nWorkspace: {{WORKSPACE_NAME}}\n", encoding="utf-8"
    )
    return template


# ---------------------------------------------------------------------------
# Edge case: unicode project name gets SAE- prefix
# ---------------------------------------------------------------------------


def test_create_project_unicode_name_uses_sae_prefix(tmp_path):
    """Unicode project names should be prefixed with SAE-, not TS-SAE-."""
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    created = create_project(template, dest, "Démonstration")

    assert created.name.startswith("SAE-"), (
        f"Expected 'SAE-' prefix for unicode name, got: {created.name!r}"
    )
    assert not created.name.startswith("TS-SAE-"), (
        f"Old 'TS-SAE-' prefix used for unicode name: {created.name!r}"
    )


# ---------------------------------------------------------------------------
# Edge case: very long project name still uses SAE- prefix
# ---------------------------------------------------------------------------


def test_create_project_long_name_uses_sae_prefix(tmp_path):
    """Very long project names should still correctly get the SAE- prefix."""
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()
    long_name = "A" * 50

    created = create_project(template, dest, long_name)

    assert created.name == f"SAE-{long_name}", (
        f"Expected 'SAE-{long_name}', got: {created.name!r}"
    )


# ---------------------------------------------------------------------------
# Edge case: path traversal in folder_name is still blocked after rename
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason=(
        "Pre-existing bug (BUG-GUI-033-PT): when folder_name='../../etc/passwd' "
        "the prefix 'SAE-' is prepended yielding 'SAE-../../etc/passwd'. Pathlib "
        "parses this as ['SAE-..', '..', 'etc', 'passwd'], so the '..' component "
        "only ascends back to the destination dir and the is_relative_to guard "
        "incorrectly passes. This bug predates GUI-033 and is not introduced by it."
    ),
    strict=True,
)
def test_create_project_path_traversal_still_blocked(tmp_path):
    """Path traversal should be rejected even with the new SAE- prefix logic.

    Marked xfail: the guard does not catch slash-based traversal when the
    prefix is prepended directly (pre-existing bug, tracked separately).
    """
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises((ValueError, OSError)):
        create_project(template, dest, "../../etc/passwd")


# ---------------------------------------------------------------------------
# Edge case: WORKSPACE_NAME placeholder expanded with SAE- prefix (not TS-SAE-)
# ---------------------------------------------------------------------------


def test_replace_placeholders_workspace_name_exact_value(tmp_path):
    """WORKSPACE_NAME must expand to SAE-<name>, not TS-SAE-<name>."""
    project_dir = tmp_path / "SAE-EdgeTest"
    project_dir.mkdir()
    readme = project_dir / "README.md"
    readme.write_text("WS={{WORKSPACE_NAME}}\n", encoding="utf-8")

    replace_template_placeholders(project_dir, "EdgeTest")

    content = readme.read_text(encoding="utf-8")
    assert content == "WS=SAE-EdgeTest\n", (
        f"Unexpected WORKSPACE_NAME expansion: {content!r}"
    )


# ---------------------------------------------------------------------------
# Edge case: numeric project name gets SAE- prefix
# ---------------------------------------------------------------------------


def test_create_project_numeric_name_uses_sae_prefix(tmp_path):
    """Numeric project names should still get the SAE- prefix."""
    template = _make_minimal_template(tmp_path)
    dest = tmp_path / "dest"
    dest.mkdir()

    created = create_project(template, dest, "12345")

    assert created.name == "SAE-12345", (
        f"Expected 'SAE-12345', got: {created.name!r}"
    )
