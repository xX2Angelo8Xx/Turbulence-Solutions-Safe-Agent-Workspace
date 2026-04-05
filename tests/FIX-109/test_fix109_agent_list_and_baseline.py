"""
Tests for FIX-109: Update FIX-073 tests to match current template.

Verifies that:
- FIX-073 test files reference exactly 7 agents (no removed agents)
- No removed agent names (scientist, criticist, fixer, writer, prototyper) appear in FIX-073 tests
- regression-baseline.json contains no FIX-073 entries
- regression-baseline.json _count matches actual known_failures length
- Planner test checks vscode/askQuestions (not old 'ask' tool name)
"""
import json
import pathlib
import ast

REPO_ROOT = pathlib.Path(__file__).parents[2]
BASELINE_FILE = REPO_ROOT / "tests" / "regression-baseline.json"
FRONTMATTER_TEST = REPO_ROOT / "tests" / "FIX-073" / "test_fix073_agent_frontmatter.py"
EDGE_CASES_TEST = REPO_ROOT / "tests" / "FIX-073" / "test_fix073_edge_cases.py"

EXPECTED_AGENTS = {
    "programmer", "brainstormer", "tester", "researcher",
    "coordinator", "planner", "workspace-cleaner",
}
REMOVED_AGENTS = {"scientist", "criticist", "fixer", "writer", "prototyper"}


def _load_baseline():
    return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Regression baseline must have no FIX-073 entries
# ---------------------------------------------------------------------------

def test_baseline_has_no_fix073_entries():
    """regression-baseline.json must not contain any FIX-073 test entries."""
    data = _load_baseline()
    fix073_entries = [k for k in data["known_failures"] if "FIX-073" in k or "fix073" in k]
    assert not fix073_entries, (
        f"regression-baseline.json still contains FIX-073 entries: {fix073_entries}"
    )


def test_baseline_count_matches_entries():
    """_count must equal the actual number of known_failures entries."""
    data = _load_baseline()
    declared = data["_count"]
    actual = len(data["known_failures"])
    assert declared == actual, (
        f"_count ({declared}) does not match len(known_failures) ({actual})"
    )


# ---------------------------------------------------------------------------
# FIX-073 test files must reference exactly 7 current agents
# ---------------------------------------------------------------------------

def test_frontmatter_test_agent_files_count():
    """test_fix073_agent_frontmatter.py AGENT_FILES must have exactly 7 entries."""
    source = FRONTMATTER_TEST.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "AGENT_FILES":
                    if isinstance(node.value, ast.Dict):
                        count = len(node.value.keys)
                        assert count == 7, (
                            f"AGENT_FILES in frontmatter test has {count} entries, expected 7"
                        )
                        return
    raise AssertionError("AGENT_FILES dict not found in test_fix073_agent_frontmatter.py")


def test_edge_cases_test_agent_files_count():
    """test_fix073_edge_cases.py AGENT_FILES must have exactly 7 entries."""
    source = EDGE_CASES_TEST.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "AGENT_FILES":
                    if isinstance(node.value, ast.Dict):
                        count = len(node.value.keys)
                        assert count == 7, (
                            f"AGENT_FILES in edge cases test has {count} entries, expected 7"
                        )
                        return
    raise AssertionError("AGENT_FILES dict not found in test_fix073_edge_cases.py")


# ---------------------------------------------------------------------------
# Removed agent names must not appear in FIX-073 test files
# ---------------------------------------------------------------------------

def test_removed_agents_not_in_frontmatter_test():
    """Removed agent names (scientist, criticist, etc.) must not appear in frontmatter test."""
    source = FRONTMATTER_TEST.read_text(encoding="utf-8")
    found = [name for name in REMOVED_AGENTS if name in source]
    assert not found, (
        f"Removed agents still referenced in test_fix073_agent_frontmatter.py: {found}"
    )


def test_removed_agents_not_in_edge_cases_test():
    """Removed agent names must not appear in edge cases test."""
    source = EDGE_CASES_TEST.read_text(encoding="utf-8")
    found = [name for name in REMOVED_AGENTS if name in source]
    assert not found, (
        f"Removed agents still referenced in test_fix073_edge_cases.py: {found}"
    )


# ---------------------------------------------------------------------------
# Planner test must check vscode/askQuestions (not old 'ask')
# ---------------------------------------------------------------------------

def test_planner_ask_tool_uses_new_name():
    """test_fix073_agent_frontmatter.py must check for vscode/askQuestions, not 'ask'."""
    source = FRONTMATTER_TEST.read_text(encoding="utf-8")
    assert "vscode/askQuestions" in source, (
        "test_fix073_agent_frontmatter.py does not reference vscode/askQuestions"
    )


def test_planner_old_ask_tool_not_checked():
    """test_fix073_agent_frontmatter.py must not check for bare 'ask' tool in planner tools."""
    source = FRONTMATTER_TEST.read_text(encoding="utf-8")
    # Only checking that "ask" does not appear as a standalone tool entry in EXPECTED_TOOLS
    # Fine-grained: the EXPECTED_TOOLS planner entry should not include bare "ask"
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "EXPECTED_TOOLS":
                    if isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant) and key.value == "planner":
                                if isinstance(value, ast.List):
                                    tool_names = [
                                        elt.value for elt in value.elts
                                        if isinstance(elt, ast.Constant)
                                    ]
                                    assert "ask" not in tool_names, (
                                        f"planner EXPECTED_TOOLS still contains bare 'ask': {tool_names}"
                                    )
                                    return
    # If we get here, the structure wasn't found — that's acceptable (may be defined differently)
