"""SAF-023 — Tests for get_errors Tool Recognition and Zone Blocking.

Covers:
- TST-1439 to TST-1452: Unit — validate_get_errors() direct calls (14 tests)
- TST-1453 to TST-1458: Security — tool recognized and zone-checked via decide() (6 tests)
- TST-1459 to TST-1464: Bypass — adversarial payloads and malformed inputs (6 tests)
- TST-1465 to TST-1468: Cross-platform — Windows/POSIX/WSL path variants (4 tests)
- TST-1469 to TST-1472: Integration — full decide() pipeline with VS Code hook format (4 tests)
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make security_gate (and zone_classifier) importable
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "Default-Project"
    / ".github"
    / "hooks"
    / "scripts"
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WS = "/workspace"
WS_WIN = "c:/workspace"

# Paths — project folder (allow zone)
PROJECT_FILE_1 = f"{WS}/project/src/main.py"
PROJECT_FILE_2 = f"{WS}/project/utils.py"
PROJECT_FILE_WIN = f"{WS_WIN}/project/src/main.py"

# Paths — restricted zones (deny)
GITHUB_FILE = f"{WS}/.github/hooks/scripts/security_gate.py"
NOAGENT_FILE = f"{WS}/NoAgentZone/secret.txt"
VSCODE_FILE = f"{WS}/.vscode/settings.json"

# Paths — ask zone (not explicitly in Project/)
DOCS_FILE = f"{WS}/docs/readme.md"


# ---------------------------------------------------------------------------
# conftest-style zone_classifier patch for fake workspace
# ---------------------------------------------------------------------------
# zone_classifier.detect_project_folder() scans real disk; fake paths fail.
# Patch it to return "project" (the standard subfolder name in all tests).

@pytest.fixture(autouse=True)
def _patch_detect_project_folder():
    """Patch zone_classifier.detect_project_folder for fake workspace roots."""
    import zone_classifier as zc
    original = zc.detect_project_folder

    def _detect_with_fallback(workspace_root: Path) -> str:
        try:
            return original(workspace_root)
        except (RuntimeError, OSError):
            return "project"

    with patch.object(zc, "detect_project_folder", side_effect=_detect_with_fallback):
        yield


# ===========================================================================
# Unit — validate_get_errors()  (TST-1439 to TST-1452)
# ===========================================================================

class TestValidateGetErrors:
    """Direct unit tests for validate_get_errors()."""

    # --- No filePaths → allow

    def test_no_file_paths_key_allow(self):
        # TST-1439 — absent filePaths → allow
        data = {}
        assert sg.validate_get_errors(data, WS) == "allow"

    def test_empty_file_paths_allow(self):
        # TST-1440 — filePaths=[] → allow
        data = {"filePaths": []}
        assert sg.validate_get_errors(data, WS) == "allow"

    def test_none_file_paths_allow(self):
        # TST-1441 — filePaths=None → allow
        data = {"filePaths": None}
        assert sg.validate_get_errors(data, WS) == "allow"

    def test_nested_tool_input_no_paths_allow(self):
        # TST-1442 — tool_input present but no filePaths → allow
        data = {"tool_input": {}}
        assert sg.validate_get_errors(data, WS) == "allow"

    def test_nested_tool_input_empty_paths_allow(self):
        # TST-1443 — tool_input.filePaths=[] → allow
        data = {"tool_input": {"filePaths": []}}
        assert sg.validate_get_errors(data, WS) == "allow"

    # --- Single project path → allow

    def test_single_project_path_allow(self):
        # TST-1444 — one path in Project/ → allow
        data = {"filePaths": [PROJECT_FILE_1]}
        assert sg.validate_get_errors(data, WS) == "allow"

    def test_multiple_project_paths_allow(self):
        # TST-1445 — multiple paths all in Project/ → allow
        data = {"filePaths": [PROJECT_FILE_1, PROJECT_FILE_2]}
        assert sg.validate_get_errors(data, WS) == "allow"

    # --- Restricted zone paths → deny

    def test_github_path_deny(self):
        # TST-1446 — .github/ path → deny
        data = {"filePaths": [GITHUB_FILE]}
        assert sg.validate_get_errors(data, WS) == "deny"

    def test_noagentzone_path_deny(self):
        # TST-1447 — NoAgentZone/ path → deny
        data = {"filePaths": [NOAGENT_FILE]}
        assert sg.validate_get_errors(data, WS) == "deny"

    def test_vscode_path_deny(self):
        # TST-1448 — .vscode/ path → deny
        data = {"filePaths": [VSCODE_FILE]}
        assert sg.validate_get_errors(data, WS) == "deny"

    def test_mixed_project_and_restricted_deny(self):
        # TST-1449 — one project path + one restricted path → deny
        data = {"filePaths": [PROJECT_FILE_1, GITHUB_FILE]}
        assert sg.validate_get_errors(data, WS) == "deny"

    # --- Non-list filePaths → deny (fail closed)

    def test_string_file_paths_deny(self):
        # TST-1450 — filePaths as string (malformed) → deny
        data = {"filePaths": PROJECT_FILE_1}
        assert sg.validate_get_errors(data, WS) == "deny"

    def test_integer_file_paths_deny(self):
        # TST-1451 — filePaths as integer → deny
        data = {"filePaths": 42}
        assert sg.validate_get_errors(data, WS) == "deny"

    def test_nested_format_project_path_allow(self):
        # TST-1452 — VS Code hook nested format: tool_input.filePaths=[project] → allow
        data = {"tool_input": {"filePaths": [PROJECT_FILE_1]}}
        assert sg.validate_get_errors(data, WS) == "allow"


# ===========================================================================
# Security — decide() dispatches get_errors correctly (TST-1453 to TST-1458)
# ===========================================================================

class TestDecideGetErrors:
    """Security tests: decide() intercepts get_errors before exempt-tool fallback."""

    def _payload(self, file_paths=None, use_nested=True):
        """Build a realistic get_errors hook payload."""
        if use_nested:
            tool_input = {}
            if file_paths is not None:
                tool_input["filePaths"] = file_paths
            return {"tool_name": "get_errors", "tool_input": tool_input}
        payload = {"tool_name": "get_errors"}
        if file_paths is not None:
            payload["filePaths"] = file_paths
        return payload

    def test_decide_no_paths_allow(self):
        # TST-1453 — decide() allows get_errors with no filePaths
        assert sg.decide(self._payload(), WS) == "allow"

    def test_decide_project_path_allow(self):
        # TST-1454 — decide() allows get_errors targeting Project/
        assert sg.decide(self._payload([PROJECT_FILE_1]), WS) == "allow"

    def test_decide_github_path_deny(self):
        # TST-1455 — decide() denies get_errors targeting .github/
        assert sg.decide(self._payload([GITHUB_FILE]), WS) == "deny"

    def test_decide_noagentzone_path_deny(self):
        # TST-1456 — decide() denies get_errors targeting NoAgentZone/
        assert sg.decide(self._payload([NOAGENT_FILE]), WS) == "deny"

    def test_decide_vscode_path_deny(self):
        # TST-1457 — decide() denies get_errors targeting .vscode/
        assert sg.decide(self._payload([VSCODE_FILE]), WS) == "deny"

    def test_decide_flat_format_no_paths_allow(self):
        # TST-1458 — flat (non-nested) format, no filePaths → allow
        assert sg.decide(self._payload(use_nested=False), WS) == "allow"


# ===========================================================================
# Bypass attempts  (TST-1459 to TST-1464)
# ===========================================================================

class TestBypassAttempts:
    """Adversarial inputs that should all be denied."""

    def test_path_traversal_to_github(self):
        # TST-1459 — path traversal into .github/ via ..
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [f"{WS}/project/../.github/hooks/pre_tool_use"]},
        }
        assert sg.decide(data, WS) == "deny"

    def test_path_traversal_to_noagentzone(self):
        # TST-1460 — path traversal into NoAgentZone/
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [f"{WS}/project/../../NoAgentZone/secret.txt"]},
        }
        assert sg.decide(data, WS) == "deny"

    def test_empty_string_in_paths_deny(self):
        # TST-1461 — empty string inside filePaths → deny (fail closed)
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [""]},
        }
        assert sg.decide(data, WS) == "deny"

    def test_null_element_in_paths_deny(self):
        # TST-1462 — None element inside filePaths → deny (fail closed)
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [None]},
        }
        assert sg.decide(data, WS) == "deny"

    def test_mixed_project_and_noagentzone_deny(self):
        # TST-1463 — mixed array: one good path + one NoAgentZone path → deny
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [PROJECT_FILE_1, NOAGENT_FILE]},
        }
        assert sg.decide(data, WS) == "deny"

    def test_malformed_tool_input_not_dict(self):
        # TST-1464 — tool_input is a string, not dict → allow (no paths → empty)
        # NB: validate_get_errors falls back to data-level filePaths which is also absent
        data = {"tool_name": "get_errors", "tool_input": "not a dict"}
        assert sg.decide(data, WS) == "allow"


# ===========================================================================
# Cross-platform (TST-1465 to TST-1468)
# ===========================================================================

class TestCrossPlatform:
    """Verifies zone checks work for Windows, POSIX, and WSL path formats."""

    def test_windows_project_path_allow(self):
        # TST-1465 — Windows-style project path → allow
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [PROJECT_FILE_WIN]},
        }
        assert sg.decide(data, WS_WIN) == "allow"

    def test_windows_github_path_deny(self):
        # TST-1466 — Windows-style .github/ path → deny
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [f"{WS_WIN}/.github/hooks/security_gate.py"]},
        }
        assert sg.decide(data, WS_WIN) == "deny"

    def test_backslash_path_in_project_allow(self):
        # TST-1467 — backslash-separated project path → allow (normalized by gate)
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [r"c:\workspace\project\src\main.py"]},
        }
        assert sg.decide(data, WS_WIN) == "allow"

    def test_backslash_path_to_github_deny(self):
        # TST-1468 — backslash path targeting .github/ → deny
        data = {
            "tool_name": "get_errors",
            "tool_input": {"filePaths": [r"c:\workspace\.github\hooks\security_gate.py"]},
        }
        assert sg.decide(data, WS_WIN) == "deny"


# ===========================================================================
# Integration — full decide() pipeline with VS Code hook format (TST-1469–1472)
# ===========================================================================

class TestIntegration:
    """End-to-end decide() pipeline with realistic hook payloads."""

    def test_realworld_no_paths_payload_allow(self):
        # TST-1469 — realistic hook payload without filePaths → allow
        payload = {
            "tool_name": "get_errors",
            "tool_input": {},
        }
        assert sg.decide(payload, WS) == "allow"

    def test_realworld_project_files_payload_allow(self):
        # TST-1470 — realistic hook payload with multiple project files → allow
        payload = {
            "tool_name": "get_errors",
            "tool_input": {
                "filePaths": [
                    f"{WS}/project/src/app.py",
                    f"{WS}/project/src/utils.py",
                    f"{WS}/project/tests/test_app.py",
                ],
            },
        }
        assert sg.decide(payload, WS) == "allow"

    def test_realworld_github_file_in_list_deny(self):
        # TST-1471 — realistic hook payload with .github/ file in list → deny
        payload = {
            "tool_name": "get_errors",
            "tool_input": {
                "filePaths": [
                    f"{WS}/project/src/app.py",
                    f"{WS}/.github/hooks/scripts/security_gate.py",
                ],
            },
        }
        assert sg.decide(payload, WS) == "deny"

    def test_get_errors_in_exempt_tools(self):
        # TST-1472 — get_errors must be present in _EXEMPT_TOOLS
        assert "get_errors" in sg._EXEMPT_TOOLS
