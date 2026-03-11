"""Tests for Default-Project/.github/hooks/scripts/zone_classifier.py

SAF-002 — Zone Enforcement Logic

Covers:
  - TST-125 to TST-132: Unit — normalize_path()
  - TST-133 to TST-140: Unit — classify() basic zone decisions
  - TST-141 to TST-142: Security — protection tests
  - TST-143 to TST-150: Security — bypass attempt tests
  - TST-151 to TST-156: Cross-platform tests
  - TST-157 to TST-164: Integration tests (security_gate delegation)
"""
from __future__ import annotations

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Make zone_classifier (and security_gate) importable from their
# non-standard location inside Default-Project/.github/hooks/scripts/
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "Default-Project",
        ".github",
        "hooks",
        "scripts",
    )
)

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import zone_classifier as zc  # noqa: E402
import security_gate as sg    # noqa: E402

# Workspace root constant used across all tests
WS = "/workspace"


# ===========================================================================
# normalize_path  (TST-125 to TST-132)
# ===========================================================================

def test_normalize_null_byte_stripped():
    # TST-125
    result = zc.normalize_path("/workspace\x00/.github/secret")
    assert "\x00" not in result
    assert ".github" in result


def test_normalize_double_backslash():
    # TST-126 — JSON double-escaped backslash → forward slash
    result = zc.normalize_path("project\\\\subdir\\file.py")
    assert "\\" not in result
    assert "project/subdir/file.py" == result


def test_normalize_single_backslash():
    # TST-127
    result = zc.normalize_path("project\\main.py")
    assert result == "project/main.py"


def test_normalize_wsl_prefix():
    # TST-128
    result = zc.normalize_path("/mnt/c/users/dev/project/x.py")
    assert result.startswith("c:/")
    assert "mnt" not in result


def test_normalize_gitbash_prefix():
    # TST-129
    result = zc.normalize_path("/c/users/dev/project/x.py")
    assert result.startswith("c:/")


def test_normalize_lowercase():
    # TST-130
    result = zc.normalize_path("Project/File.Py")
    assert result == result.lower()


def test_normalize_trailing_slash():
    # TST-131
    result = zc.normalize_path("project/")
    assert not result.endswith("/")


def test_normalize_dotdot_resolved():
    # TST-132 — '..' must be resolved before zone comparison
    result = zc.normalize_path("/workspace/project/../.github/secret")
    assert "project" not in result
    assert ".github" in result


# ===========================================================================
# classify() — basic zone decisions  (TST-133 to TST-140)
# ===========================================================================

def test_classify_allow_project_root():
    # TST-133
    assert zc.classify(f"{WS}/project", WS) == "allow"


def test_classify_allow_project_nested():
    # TST-134
    assert zc.classify(f"{WS}/project/src/main.py", WS) == "allow"


def test_classify_deny_github():
    # TST-135
    assert zc.classify(f"{WS}/.github/secret", WS) == "deny"


def test_classify_deny_vscode():
    # TST-136
    assert zc.classify(f"{WS}/.vscode/settings.json", WS) == "deny"


def test_classify_deny_noagentzone():
    # TST-137
    assert zc.classify(f"{WS}/noagentzone/private.md", WS) == "deny"


def test_classify_ask_docs():
    # TST-138
    assert zc.classify(f"{WS}/docs/readme.md", WS) == "ask"


def test_classify_ask_root_file():
    # TST-139
    assert zc.classify(f"{WS}/README.md", WS) == "ask"


def test_classify_ask_src():
    # TST-140
    assert zc.classify(f"{WS}/src/launcher/main.py", WS) == "ask"


# ===========================================================================
# Security — protection tests  (TST-141 to TST-142)
# ===========================================================================

def test_classify_deny_uses_relative_to_for_github():
    # TST-141 — Method 1: relative_to() identifies .github as deny zone
    result = zc.classify(f"{WS}/.github/hooks/security_gate.py", WS)
    assert result == "deny"


def test_classify_allow_uses_relative_to_for_project():
    # TST-142 — Method 1: relative_to() identifies project/ as allow zone
    result = zc.classify(f"{WS}/project/app.py", WS)
    assert result == "allow"


# ===========================================================================
# Security — bypass attempt tests  (TST-143 to TST-150)
# ===========================================================================

def test_bypass_path_traversal_dotdot():
    # TST-143 — "project/../.github/secret" must resolve to .github/ and be denied
    raw = f"{WS}/project/../.github/secret"
    assert zc.classify(raw, WS) == "deny"


def test_bypass_deep_traversal():
    # TST-144 — deep traversal must still resolve and be denied
    raw = f"{WS}/project/../../../../.github/x"
    assert zc.classify(raw, WS) == "deny"


def test_bypass_prefix_sibling():
    # TST-145 — "project-evil/" must NOT match "project/" (str.startswith bypass)
    # pathlib.relative_to() correctly rejects sibling prefixes
    assert zc.classify(f"{WS}/project-evil/payload.py", WS) == "ask"
    # but a nested .github under a sibling must still be denied (Method 2)
    assert zc.classify(f"{WS}/project-evil/.github/x", WS) == "deny"


def test_bypass_null_byte_before_github():
    # TST-146 — null byte before .github must be stripped then path denied
    raw = f"{WS}/\x00.github/secret"
    assert zc.classify(raw, WS) == "deny"


def test_bypass_unc_github():
    # TST-147 — UNC path targeting .github must be denied via Method 2
    raw = "\\\\server\\share\\.github\\secret"
    assert zc.classify(raw, WS) == "deny"


def test_bypass_relative_path_github():
    # TST-148 — relative ".github/secret" must be resolved against ws_root and denied
    assert zc.classify(".github/secret", WS) == "deny"


def test_bypass_mixed_case_github():
    # TST-149 — mixed-case ".GITHUB" must be lowercased and denied
    assert zc.classify(f"{WS}/.GITHUB/secret", WS) == "deny"


def test_bypass_mixed_case_noagentzone():
    # TST-150 — "NoAgentZone" with mixed case must be lowercased and denied
    assert zc.classify(f"{WS}/NoAgentZone/private.md", WS) == "deny"


# ===========================================================================
# Cross-platform tests  (TST-151 to TST-156)
# ===========================================================================

def test_cross_platform_windows_allow():
    # TST-151 — Windows absolute path inside Project/ must be allowed
    ws = "c:/workspace"
    assert zc.classify("C:\\workspace\\project\\main.py", ws) == "allow"


def test_cross_platform_windows_deny():
    # TST-152 — Windows absolute path inside .github must be denied
    ws = "c:/workspace"
    assert zc.classify("C:\\workspace\\.github\\secret", ws) == "deny"


def test_cross_platform_wsl_allow():
    # TST-153 — WSL /mnt/c/... path inside project/ must be allowed
    ws = "c:/workspace"
    assert zc.classify("/mnt/c/workspace/project/x.py", ws) == "allow"


def test_cross_platform_wsl_deny():
    # TST-154 — WSL /mnt/c/... path inside .vscode must be denied
    ws = "c:/workspace"
    assert zc.classify("/mnt/c/workspace/.vscode/settings.json", ws) == "deny"


def test_cross_platform_gitbash_allow():
    # TST-155 — Git Bash /c/... path inside project/ must be allowed
    ws = "c:/workspace"
    assert zc.classify("/c/workspace/project/main.py", ws) == "allow"


def test_cross_platform_gitbash_deny():
    # TST-156 — Git Bash /c/... path inside .github must be denied
    ws = "c:/workspace"
    assert zc.classify("/c/workspace/.github/secret", ws) == "deny"


# ===========================================================================
# Integration — security_gate.py delegates to zone_classifier  (TST-157-164)
# ===========================================================================

def test_security_gate_imports_zone_classifier():
    # TST-157 — zone_classifier must be importable from the scripts directory
    import importlib
    spec = importlib.util.find_spec("zone_classifier")
    assert spec is not None, "zone_classifier not found on sys.path"


def test_get_zone_backward_compat_allow():
    # TST-158 — sg.get_zone() must still return 'allow' for Project/ paths
    assert sg.get_zone(f"{WS}/project/main.py", WS) == "allow"


def test_get_zone_backward_compat_deny():
    # TST-159 — sg.get_zone() must still return 'deny' for .github/ paths
    assert sg.get_zone(f"{WS}/.github/secret", WS) == "deny"


def test_get_zone_backward_compat_ask():
    # TST-160 — sg.get_zone() must still return 'ask' for non-zone paths
    assert sg.get_zone(f"{WS}/docs/readme.md", WS) == "ask"


def test_decide_project_allow():
    # TST-161 — full decide() pipeline: read_file on Project/ → allow
    data = {"tool_name": "read_file", "filePath": f"{WS}/project/main.py"}
    assert sg.decide(data, WS) == "allow"


def test_decide_github_deny():
    # TST-162 — full decide() pipeline: read_file on .github/ → deny
    data = {"tool_name": "read_file", "filePath": f"{WS}/.github/secret"}
    assert sg.decide(data, WS) == "deny"


def test_decide_ask_zone():
    # TST-163 — full decide() pipeline: read_file on docs/ → ask
    data = {"tool_name": "read_file", "filePath": f"{WS}/docs/readme.md"}
    assert sg.decide(data, WS) == "ask"


def test_decide_path_traversal_still_denied():
    # TST-164 — decide() must deny traversal paths routed via zone_classifier
    data = {"tool_name": "read_file", "filePath": f"{WS}/project/../.github/secret"}
    assert sg.decide(data, WS) == "deny"


# ===========================================================================
# Tester edge-case and security tests  (TST-175 to TST-188)
# ===========================================================================

def test_security_multiple_null_bytes_stripped():
    # TST-175 — two consecutive null bytes before .github must both be stripped then denied
    raw = f"{WS}/\x00\x00.github/secret"
    assert zc.classify(raw, WS) == "deny"


def test_security_null_byte_mid_segment_splits_github():
    # TST-176 — null bytes interspersed inside ".github" must be stripped, yielding ".github" → deny
    # ".gi\x00t\x00hub" after null removal = ".github"
    raw = f"{WS}/.gi\x00t\x00hub/secret"
    assert zc.classify(raw, WS) == "deny"


def test_edge_empty_path_fails_closed():
    # TST-177 — empty path string must fail closed (ask, not allow)
    result = zc.classify("", WS)
    assert result in ("ask", "deny"), f"empty path returned allow — must fail closed, got {result!r}"


def test_edge_exact_deny_dir_no_subpath():
    # TST-178 — path exactly equal to deny root dir (no trailing slash, no subpath) must be denied
    assert zc.classify(f"{WS}/.github", WS) == "deny"
    assert zc.classify(f"{WS}/.vscode", WS) == "deny"
    assert zc.classify(f"{WS}/noagentzone", WS) == "deny"


def test_edge_exact_allow_dir_no_subpath():
    # TST-179 — path exactly equal to allow root dir (no trailing slash, no subpath) must be allowed
    assert zc.classify(f"{WS}/project", WS) == "allow"


def test_edge_consecutive_interior_slashes_in_deny_path():
    # TST-180 — posixpath.normpath must collapse consecutive slashes; .github still denied
    assert zc.classify(f"{WS}///.github/secret", WS) == "deny"
    assert zc.classify(f"{WS}///project/main.py", WS) == "allow"


def test_edge_very_long_path_no_exception():
    # TST-181 — extremely long paths must not raise an exception and must fail closed (ask)
    long_path = f"{WS}/" + "a/" * 500 + "file.py"
    result = zc.classify(long_path, WS)
    assert result == "ask"


def test_security_traversal_arriving_at_deny_dir_root():
    # TST-182 — traversal resolving exactly to a deny dir (no subpath) must be denied
    assert zc.classify(f"{WS}/project/../.github", WS) == "deny"
    assert zc.classify(f"{WS}/project/../.vscode", WS) == "deny"
    assert zc.classify(f"{WS}/project/../noagentzone", WS) == "deny"


def test_edge_ws_root_with_multiple_trailing_slashes():
    # TST-183 — ws_root with multiple trailing slashes must not affect classification correctness
    ws_trailing = WS + "///"
    assert zc.classify(f"{WS}/project/app.py", ws_trailing) == "allow"
    assert zc.classify(f"{WS}/.github/secret", ws_trailing) == "deny"
    assert zc.classify(f"{WS}/docs/readme.md", ws_trailing) == "ask"


def test_security_tab_before_deny_dir():
    # TST-184 — SECURITY BUG: tab character immediately before ".github" must be denied
    # normalize_path() strips null bytes but NOT other C0 control characters.
    # A path segment "\t.github" passes Method 1 (not in _DENY_DIRS) and Method 2
    # (regex /(\.github) requires "/" then "." with no intervening chars).
    # Expected: "deny"  Actual (buggy): "ask"
    raw = f"{WS}/\t.github/secret"
    assert zc.classify(raw, WS) == "deny", (
        "SECURITY: tab before .github bypasses deny classification — "
        "normalize_path must strip all C0 control characters, not only null bytes"
    )


def test_security_newline_before_deny_dir():
    # TST-185 — SECURITY BUG: newline character before ".github" must be denied (same root cause as TST-184)
    raw = f"{WS}/\n.github/secret"
    assert zc.classify(raw, WS) == "deny", (
        "SECURITY: newline before .github bypasses deny classification — "
        "normalize_path must strip all C0 control characters"
    )


def test_security_unc_path_project_outside_workspace_not_allow():
    # TST-186 — SECURITY BUG: UNC path to a directory named "project" on an external server
    # must NOT return "allow".  Method 2 _ALLOW_PATTERN matches "/project/" anywhere in the
    # normalised path, including on a different network host.  The correct response is "ask"
    # (or "deny") because the path is outside the workspace root.
    # Expected: "ask"  Actual (buggy): "allow"
    raw = "\\\\server\\share\\project\\sensitive.py"
    result = zc.classify(raw, WS)
    assert result != "allow", (
        "SECURITY: UNC path to /project/ on an external server returned 'allow' — "
        "out-of-workspace paths must never receive 'allow'; Method 2 allow pattern "
        "must not match paths outside ws_root"
    )


def test_edge_project_deeply_nested_file():
    # TST-187 — deeply nested file inside project/ must still be allowed (Method 1 regression)
    deep = f"{WS}/project/a/b/c/d/e/f/g/main.py"
    assert zc.classify(deep, WS) == "allow"


def test_edge_no_exception_on_unusual_input():
    # TST-188 — unusual but non-malicious inputs must never raise an unhandled exception
    unusual_inputs = [
        ".",
        "..",
        "/",
        WS,
        f"{WS}/",
        "project",            # relative allow
        ".github",            # relative deny
        "C:",                 # Windows drive root only
        "\\\\",              # bare UNC prefix
    ]
    for path in unusual_inputs:
        try:
            result = zc.classify(path, WS)
            assert result in ("allow", "deny", "ask"), (
                f"classify({path!r}) returned unexpected value {result!r}"
            )
        except Exception as exc:
            raise AssertionError(
                f"classify({path!r}) raised an unhandled exception: {exc!r}"
            ) from exc
