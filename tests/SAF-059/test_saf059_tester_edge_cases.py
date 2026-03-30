"""SAF-059 — Tester edge-case tests.

Additional tests added by the Tester Agent beyond the Developer's test suite.
Focuses on:
- Combined BUG-140 + BUG-142: paren-wrapped delete with obfuscation-triggering path
- Paren expressions with no property access (zero .property quantifier)
- Remove-Item specifically targeting security_gate.py (deny-zone path)
- Nested parens (double-wrapped) — fails closed, correctly denied
- Paren + pipe combos — fails closed, correctly denied
- (Test-Path deny-zone) — paren-wrapped deny-zone access
- iex variations: quoted args, allowlisted path arg (still denied because iex is blocked)
- Chained segments where one segment is a paren expression with blocked inner verb
- $(cmd) subshell syntax in various positions
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = str(
    Path(__file__).parents[2]
    / "templates"
    / "agent-workbench"
    / ".github"
    / "hooks"
    / "scripts"
)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(scope="module")
def sg():
    import security_gate as _sg
    return _sg


@pytest.fixture(autouse=True)
def mock_project_folder():
    with patch("zone_classifier.detect_project_folder", return_value="project"):
        yield


WS = "c:/workspace"


def allow(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "allow"


def deny(sg, command: str) -> bool:
    decision, _ = sg.sanitize_terminal_command(command, WS)
    return decision == "deny"


# ---------------------------------------------------------------------------
# Paren + deny-zone: (Remove-Item ...) with deny-zone path
# ---------------------------------------------------------------------------

class TestParenRemoveItemDenyZone:
    """(Remove-Item deny-zone-path).Count must be denied — BUG-142 fix must not
    allow paren expressions to bypass deny-zone enforcement."""

    def test_paren_remove_item_github_denied(self, sg):
        """(Remove-Item .github/file).Count is denied (deny zone)."""
        assert deny(sg, "(Remove-Item .github/file).Count")

    def test_paren_remove_item_security_gate_denied(self, sg):
        """(Remove-Item .github/hooks/scripts/security_gate.py).Count denied."""
        assert deny(sg, "(Remove-Item .github/hooks/scripts/security_gate.py).Count")

    def test_paren_remove_item_vscode_denied(self, sg):
        """(Remove-Item .vscode/settings.json).Count denied (deny zone)."""
        assert deny(sg, "(Remove-Item .vscode/settings.json).Count")

    def test_paren_remove_item_noagentzone_denied(self, sg):
        """(Remove-Item NoAgentZone/secret).Count denied."""
        assert deny(sg, "(Remove-Item NoAgentZone/secret).Count")

    def test_paren_remove_item_project_allowed(self, sg):
        """(Remove-Item project/file.txt).Count is allowed (project path, BUG-142)."""
        assert allow(sg, "(Remove-Item project/file.txt).Count")

    def test_paren_remove_item_exec_path_allowed(self, sg):
        """Combined BUG-140+142: (Remove-Item project/exec-scripts/file.txt).Count allowed."""
        assert allow(sg, "(Remove-Item project/exec-scripts/file.txt).Count")


# ---------------------------------------------------------------------------
# Paren with no property access — zero quantifier in _PAREN_SUBEXPR_RE
# ---------------------------------------------------------------------------

class TestParenNoPropertyAccess:
    """_PAREN_SUBEXPR_RE allows zero property accesses.
    (remove-item project/file) with no .Property suffix is also unwrapped.
    Security guarantee: deny-zone paths still denied; blocked verbs still denied.
    """

    def test_paren_no_property_project_remove_allowed(self, sg):
        """(Remove-Item project/file.txt) with no property access is allowed."""
        assert allow(sg, "(Remove-Item project/file.txt)")

    def test_paren_no_property_iex_denied(self, sg):
        """(iex exploit) with no property is denied — iex is not allowlisted."""
        assert deny(sg, "(iex exploit)")

    def test_paren_no_property_iex_project_path_denied(self, sg):
        """(iex project/file.txt) — iex is blocked even with allowed path."""
        assert deny(sg, "(iex project/file.txt)")

    def test_paren_no_property_remove_github_denied(self, sg):
        """(Remove-Item .github/secret) with no property is denied (deny zone)."""
        assert deny(sg, "(Remove-Item .github/secret)")


# ---------------------------------------------------------------------------
# Test-Path deny-zone — with and without paren wrapping
# ---------------------------------------------------------------------------

class TestTestPathDenyZoneVariants:
    """Test-Path targeting deny-zone paths must be denied in all syntactic forms."""

    def test_test_path_github_trailing_slash_denied(self, sg):
        """Test-Path .github/hooks/ (trailing slash) is denied."""
        assert deny(sg, "Test-Path .github/hooks/")

    def test_paren_test_path_github_denied(self, sg):
        """(Test-Path .github/hooks/) paren-wrapped is denied."""
        assert deny(sg, "(Test-Path .github/hooks/)")

    def test_paren_test_path_github_dot_bool(self, sg):
        """(Test-Path .github/).ToString is denied (property access form)."""
        assert deny(sg, "(Test-Path .github/).ToString")

    def test_test_path_security_gate_denied(self, sg):
        """Test-Path .github/hooks/scripts/security_gate.py is denied."""
        assert deny(sg, "Test-Path .github/hooks/scripts/security_gate.py")


# ---------------------------------------------------------------------------
# Nested parens — fails closed (correctly denied)
# ---------------------------------------------------------------------------

class TestNestedParens:
    """Double-wrapped paren expressions like ((cmd).Method()).Count.
    _PAREN_SUBEXPR_RE only unwraps one level; after the first unwrap the
    remaining inner text may not re-match.  The system fails closed (deny).
    This is the correct security behaviour — it is not a bug.
    """

    def test_double_paren_get_content_denied(self, sg):
        """((Get-Content project/file.txt).Split(',\")).Count denied (nested paren)."""
        assert deny(sg, "((Get-Content project/file.txt).Split(\",\")).Count")

    def test_double_paren_echo_denied(self, sg):
        """((echo hello).Length).ToString is denied (nested paren fails closed)."""
        assert deny(sg, "((echo hello).Length).ToString")


# ---------------------------------------------------------------------------
# Paren + pipe combos — fails closed (correctly denied)
# ---------------------------------------------------------------------------

class TestParenPipeCombos:
    """Paren expressions followed by pipe-to-command.
    When the full segment is '(cmd).Count | other', _PAREN_SUBEXPR_RE does
    NOT match (the segment doesn't end with a property qualifier).  The verb
    extracted is '(Get-Content' which is unknown → deny.  Failing closed.
    """

    def test_paren_count_pipe_out_file_denied(self, sg):
        """(Get-Content project/f.txt).Count | Out-File project/result.txt denied."""
        assert deny(sg, "(Get-Content project/file.txt).Count | Out-File project/result.txt")

    def test_paren_prop_pipe_iex_denied(self, sg):
        """(Get-Content project/f.txt).Count | iex denied (pipe to iex)."""
        assert deny(sg, "(Get-Content project/file.txt).Count | iex")

    def test_paren_get_content_pipe_iex_denied(self, sg):
        """(Get-Content project/file.txt) | iex denied (critical pipe pattern)."""
        assert deny(sg, "(Get-Content project/file.txt) | iex")


# ---------------------------------------------------------------------------
# Subshell syntax safety — $(cmd)
# ---------------------------------------------------------------------------

class TestSubshellSyntax:
    """$(cmd) subshell syntax must still be blocked by Stage 3 critical P-19."""

    def test_dollar_paren_iex_denied(self, sg):
        """$(iex cmd) is denied by Stage 3 critical subshell pattern."""
        assert deny(sg, "$(iex cmd)")

    def test_dollar_paren_in_allowlisted_segment_denied(self, sg):
        """remove-item project/$(malicious) is denied ($ subshell in arg)."""
        assert deny(sg, "remove-item project/$(malicious)")

    def test_dollar_paren_after_semicolon_denied(self, sg):
        """cat project/f.txt; $(malicious) denied even after a safe segment."""
        assert deny(sg, "cat project/f.txt; $(malicious)")


# ---------------------------------------------------------------------------
# Chained segments with blocked paren expression
# ---------------------------------------------------------------------------

class TestChainedSegments:
    """Chained `;`-separated segments where one is dangerous must be denied."""

    def test_safe_then_paren_iex_denied(self, sg):
        """cat project/a.txt; (iex malicious).Count — second segment is denied."""
        assert deny(sg, "cat project/a.txt; (iex malicious).Count")

    def test_paren_iex_then_safe_denied(self, sg):
        """(iex malicious).Count; echo done — first segment is denied."""
        assert deny(sg, "(iex malicious).Count; echo done")

    def test_remove_item_github_alone_denied(self, sg):
        """Bare Remove-Item .github/security_gate.py is denied (no paren needed)."""
        assert deny(sg, "Remove-Item .github/security_gate.py")
