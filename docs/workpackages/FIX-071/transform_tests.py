"""
FIX-071: Transform test files to use new template directory names.

Applies targeted replacements to update all test references from:
  - templates/coding -> templates/agent-workbench
  - templates/creative-marketing -> templates/certification-pipeline
  - Display name "Coding" -> "Agent Workbench"
  - Display name "Creative Marketing" -> "Certification Pipeline"

Skips GUI-023 test files (they verify the OLD names are gone - leave those intact).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
TESTS_DIR = REPO_ROOT / "tests"

# GUI-023 tests verify that the old directories DON'T exist - preserve them.
SKIP_FILES: set[str] = {
    "tests/GUI-023/test_gui023_template_rename.py",
    "tests/GUI-023/test_gui023_tester_edge_cases.py",
}


def transform(text: str, filepath: str) -> str:
    """Apply all replacements to `text`. Return the modified text."""

    # -----------------------------------------------------------------------
    # 1. _SCRIPTS_DIR os.path.join style: "templates", "coding", -> "templates", "agent-workbench",
    # -----------------------------------------------------------------------
    text = text.replace('"templates", "coding",', '"templates", "agent-workbench",')

    # -----------------------------------------------------------------------
    # 2. Pathlib path fragment " / "coding"  (string-token / "coding")
    #    This matches TEMPLATES_DIR / "coding", "templates" / "coding", etc.
    #    It does NOT match  tmp_path / "coding"  because tmp_path is not quoted.
    # -----------------------------------------------------------------------
    text = text.replace('" / "coding"', '" / "agent-workbench"')

    # -----------------------------------------------------------------------
    # 3. String literals with forward-slash template path
    # -----------------------------------------------------------------------
    text = text.replace('"templates/coding"', '"templates/agent-workbench"')
    text = text.replace("'templates/coding'", "'templates/agent-workbench'")
    text = text.replace('"templates/coding/', '"templates/agent-workbench/')
    text = text.replace("'templates/coding/", "'templates/agent-workbench/")
    text = text.replace('"templates\\\\coding"', '"templates\\\\agent-workbench"')
    text = text.replace('"templates\\coding"', '"templates\\agent-workbench"')

    # -----------------------------------------------------------------------
    # 4. "creative-marketing" string literal -> "certification-pipeline"
    #    The string literal `"creative-marketing"` or `'creative-marketing'`
    #    appears in test assertions and mock lists.  It does NOT appear in
    #    tmp_path construction (which uses  / "creative-marketing"  without an
    #    immediately preceding closing quote).
    #
    #    EXCEPTION: leave `/ "creative-marketing"` alone when preceded by `tmp`
    #    context — handled below by NOT applying this rule to lines containing
    #    tmp_path / "creative-marketing" (they won't match the pattern anyway
    #    since those paths start with a variable not a quoted string).
    # -----------------------------------------------------------------------
    text = text.replace('"creative-marketing"', '"certification-pipeline"')
    text = text.replace("'creative-marketing'", "'certification-pipeline'")
    # path fragments starting with a quote:
    text = text.replace('" / "creative-marketing"', '" / "certification-pipeline"')

    # -----------------------------------------------------------------------
    # 5. Mock list_templates return values that simulate actual templates
    #    e.g. return_value=["coding"] / _mock_list_templates(["coding"])
    #    These fail because is_template_ready checks the real TEMPLATES_DIR.
    # -----------------------------------------------------------------------
    # Two-element mocks:
    text = text.replace(
        '_mock_list_templates(["coding", "creative-marketing"])',
        '_mock_list_templates(["agent-workbench", "certification-pipeline"])'
    )
    text = text.replace(
        'return_value=["coding", "creative-marketing"]',
        'return_value=["agent-workbench", "certification-pipeline"]'
    )
    # Single-element mocks of "coding":
    text = text.replace(
        '_mock_list_templates(["coding"])',
        '_mock_list_templates(["agent-workbench"])'
    )
    text = text.replace(
        'return_value=["coding"]',
        'return_value=["agent-workbench"]'
    )
    # Two-element mocks where coding comes second:
    text = text.replace(
        '_mock_list_templates(["coding", "data-science"])',
        '_mock_list_templates(["agent-workbench", "data-science"])'
    )

    # -----------------------------------------------------------------------
    # 6. Display names in test assertions — only where they check the actual
    #    results of _format_template_name(actual_template_name).
    #
    #    Rule: replace "Coding" only when it appears inside assert/result
    #    checking contexts or as a literal equality check, NOT inside
    #    test method names, docstrings, or inside class definitions.
    #
    #    Safe replacements (the exact strings that would appear in assertions):
    # -----------------------------------------------------------------------
    # result / options / values_arg containment checks:
    text = text.replace('"Coding" in result', '"Agent Workbench" in result')
    text = text.replace('"Coding" in options', '"Agent Workbench" in options')
    text = text.replace('"Coding" in values_arg', '"Agent Workbench" in values_arg')
    text = text.replace('"Coding" in v', '"Agent Workbench" in v')
    text = text.replace('"Coding" in coming_soon', '"Agent Workbench" in coming_soon')
    text = text.replace('"Coding" not in coming_soon', '"Agent Workbench" not in coming_soon')
    # Equality checks for lists:
    text = text.replace('== ["Coding"]', '== ["Agent Workbench"]')
    text = text.replace('assert before == ["Coding"]', 'assert before == ["Agent Workbench"]')
    # Creative Marketing containment:
    text = text.replace('"Creative Marketing" in result', '"Certification Pipeline" in result')
    text = text.replace('"Creative Marketing" in option', '"Certification Pipeline" in option')
    text = text.replace('"Creative Marketing" in entry', '"Certification Pipeline" in entry')
    text = text.replace('"Creative Marketing" in v', '"Certification Pipeline" in v')
    text = text.replace('"Creative Marketing" in values_arg', '"Certification Pipeline" in values_arg')
    # Coming-soon containing the display name:
    text = text.replace('"Creative Marketing ...coming soon" in coming_soon', '"Certification Pipeline ...coming soon" in coming_soon')
    text = text.replace('"Creative Marketing ...coming soon" in options', '"Certification Pipeline ...coming soon" in options')

    # -----------------------------------------------------------------------
    # 7. Hardcoded display name string literals used as expected values:
    #    "Creative Marketing ...coming soon"  →  "Certification Pipeline ...coming soon"
    # -----------------------------------------------------------------------
    text = text.replace('"Creative Marketing ...coming soon"', '"Certification Pipeline ...coming soon"')
    text = text.replace("'Creative Marketing ...coming soon'", "'Certification Pipeline ...coming soon'")

    # -----------------------------------------------------------------------
    # 8. Positive is_template_ready checks on real TEMPLATES_DIR
    # -----------------------------------------------------------------------
    text = text.replace(
        'assert is_template_ready(REAL_TEMPLATES_DIR, "coding") is True',
        'assert is_template_ready(REAL_TEMPLATES_DIR, "agent-workbench") is True'
    )
    text = text.replace(
        'assert is_template_ready(REAL_TEMPLATES_DIR, "creative-marketing") is False',
        'assert is_template_ready(REAL_TEMPLATES_DIR, "certification-pipeline") is False'
    )

    # -----------------------------------------------------------------------
    # 9. pytest.skip messages and error messages
    # -----------------------------------------------------------------------
    text = text.replace('pytest.skip("templates/coding/ not found")', 'pytest.skip("templates/agent-workbench/ not found")')

    # -----------------------------------------------------------------------
    # 10. assert "coding" in <var> or assert "creative-marketing" in <var>
    #     where <var> holds actual template results
    # -----------------------------------------------------------------------
    text = text.replace('assert "coding" in result', 'assert "agent-workbench" in result')
    text = text.replace('assert "coding" in templates', 'assert "agent-workbench" in templates')
    text = text.replace('assert "coding" in names', 'assert "agent-workbench" in names')
    text = text.replace('assert "creative-marketing" in result', 'assert "certification-pipeline" in result')
    text = text.replace('assert "creative-marketing" in templates', 'assert "certification-pipeline" in templates')
    text = text.replace('assert "creative-marketing" in names', 'assert "certification-pipeline" in names')

    # f-string error messages:
    text = text.replace("f\"'coding' missing from", "f\"'agent-workbench' missing from")
    text = text.replace("f\"'coding' not found", "f\"'agent-workbench' not found")
    text = text.replace("f\"'creative-marketing' missing from", "f\"'certification-pipeline' missing from")
    text = text.replace("f\"'creative-marketing' not found", "f\"'certification-pipeline' not found")

    # -----------------------------------------------------------------------
    # 11. Real templates dir existence tests (TestTemplateDirPresence in GUI-002)
    #     tests that check templates/creative-marketing and templates/coding exist
    # -----------------------------------------------------------------------
    # Path construction:  templates_dir / "coding"  (variable)
    # Already caught via " / "coding" pattern? Let's check:
    # `templates_dir / "coding"` - the context is: `creative = templates_dir / "creative-marketing"`
    # "creative-marketing" is caught by rule 4.
    # `coding = templates_dir / "coding"`:  "coding" here follows `/ ` but not a `"` before it.
    # So this pattern  templates_dir / "coding"  is NOT caught by rule 2.
    # Need explicit replacement:
    text = re.sub(
        r'(templates_dir\s*/\s*)"coding"',
        r'\1"agent-workbench"',
        text,
    )

    # -----------------------------------------------------------------------
    # 12. GUI-005: template_display parameter default and return_value
    # -----------------------------------------------------------------------
    # template_display: str = "Coding" in _make_app signature
    text = text.replace('template_display: str = "Coding"', 'template_display: str = "Agent Workbench"')
    # test call: _make_app(..., template_display="Coding", ...)
    text = text.replace('template_display="Coding"', 'template_display="Agent Workbench"')
    # expected_template = TEMPLATES_DIR / "coding"  <- caught by rule 2 (TEMPLATES_DIR / preceded by ")
    # But actually: `TEMPLATES_DIR / "coding"` -> the " before / is from TEMPLATES_DIR? No.
    # The exact text is: `expected_template = TEMPLATES_DIR / "coding"`
    # My rule 2 replaces `" / "coding"` - there's no quote before / in this exact case.
    # Need: TEMPLATES_DIR / "coding" → TEMPLATES_DIR / "agent-workbench"
    text = re.sub(
        r'(TEMPLATES_DIR\s*/\s*)"coding"',
        r'\1"agent-workbench"',
        text,
    )

    return text


def process_file(path: Path) -> tuple[bool, int]:
    """Read, transform, write a test file. Returns (changed, lines_changed)."""
    # Compute relative path for skip check
    try:
        rel = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        rel = str(path)

    if rel in SKIP_FILES:
        print(f"  SKIP (GUI-023 preserve): {rel}")
        return False, 0

    original = path.read_text(encoding="utf-8")
    transformed = transform(original, rel)

    if transformed == original:
        return False, 0

    path.write_text(transformed, encoding="utf-8")
    # Count changed lines
    orig_lines = original.splitlines()
    new_lines = transformed.splitlines()
    changed = sum(1 for a, b in zip(orig_lines, new_lines) if a != b)
    changed += abs(len(orig_lines) - len(new_lines))
    return True, changed


def main() -> int:
    changed_files: list[tuple[Path, int]] = []

    for py_file in sorted(TESTS_DIR.rglob("*.py")):
        changed, lines = process_file(py_file)
        if changed:
            changed_files.append((py_file, lines))

    print(f"\nModified {len(changed_files)} files:")
    for f, n in changed_files:
        rel = f.relative_to(REPO_ROOT)
        print(f"  {rel}  ({n} lines changed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
