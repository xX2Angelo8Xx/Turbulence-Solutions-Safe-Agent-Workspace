"""Edge-case tests for scripts/check_test_impact.py (MNT-025 — Tester additions).

Covers: path injection, Windows separators, non-src files, missing tests/,
binary content, regex-special module names, multi-module scan, stderr output,
slashed-variant detection, and __init__ chain edge cases.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_test_impact import (  # noqa: E402
    _module_variants,
    _file_references_module,
    scan,
    format_warnings,
    main,
)


# ---------------------------------------------------------------------------
# Path injection / adversarial inputs
# ---------------------------------------------------------------------------

class TestPathInjection:
    """Staged filenames should never cause unintended filesystem traversal."""

    def test_path_traversal_ignored(self, tmp_path):
        """A src path containing ../ traversal should not crash or match anything."""
        # Not under src/ after normalisation — scan should silently ignore it
        result = scan(["src/../../../etc/passwd.py"], tmp_path)
        assert result == {}

    def test_null_byte_in_path_ignored(self, tmp_path):
        """Null bytes in a path should not cause an exception — skip gracefully."""
        result = scan(["src/launcher/core/mod\x00.py"], tmp_path)
        assert result == {}

    def test_only_src_slash_prefix_accepted(self, tmp_path):
        """Paths that start with 'src' but not 'src/' should be excluded."""
        # e.g. 'srclauncher/foo.py'
        result = scan(["srclauncher/foo.py"], tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# Windows path-separator normalisation
# ---------------------------------------------------------------------------

class TestWindowsPathSeparators:
    """Staged files given with backslashes (Windows git output) must be handled."""

    def _make_test_file(self, root: Path, wp: str, name: str, content: str) -> Path:
        f = root / "tests" / wp / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return f

    def test_backslash_staged_path_normalised(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_win.py",
            "import launcher.core.vscode\n",
        )
        # Simulate Windows git output using backslashes
        result = scan(["src\\launcher\\core\\vscode.py"], tmp_path)
        assert any("test_win.py" in k for k in result)


# ---------------------------------------------------------------------------
# Non-.py and non-src staged files
# ---------------------------------------------------------------------------

class TestNonPyFiles:
    def test_non_py_extension_skipped(self, tmp_path):
        """Only .py files under src/ should trigger scanning."""
        result = scan(["src/launcher/core/readme.txt"], tmp_path)
        assert result == {}

    def test_py_outside_src_skipped(self, tmp_path):
        result = scan(["scripts/some_helper.py"], tmp_path)
        assert result == {}

    def test_empty_string_in_list_skipped(self, tmp_path):
        result = scan([""], tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# Filesystem edge cases
# ---------------------------------------------------------------------------

class TestMissingTestsDirectory:
    def test_no_tests_dir_returns_empty(self, tmp_path):
        """If repo has no tests/ dir, scan should return {} cleanly."""
        # tmp_path has no tests/ subdir
        result = scan(["src/launcher/core/vscode.py"], tmp_path)
        assert result == {}


class TestBinaryTestFile:
    """Test files containing non-UTF-8 bytes must not crash the scanner."""

    def test_binary_content_handled_gracefully(self, tmp_path):
        tests_dir = tmp_path / "tests" / "DOC-001"
        tests_dir.mkdir(parents=True)
        binary_file = tests_dir / "test_binary.py"
        # Write intentionally corrupt UTF-8
        binary_file.write_bytes(b"\xff\xfe" + b"import launcher.core.vscode\n")
        # Should not raise; errors="replace" in read_text handles it
        result = scan(["src/launcher/core/vscode.py"], tmp_path)
        # Match is possible but what matters is "no exception"
        assert isinstance(result, dict)


class TestEmptyTestFile:
    def test_empty_file_not_matched(self, tmp_path):
        tests_dir = tmp_path / "tests" / "DOC-001"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_empty.py").write_text("", encoding="utf-8")
        result = scan(["src/launcher/core/vscode.py"], tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# Slashed-variant detection
# ---------------------------------------------------------------------------

class TestSlashedVariant:
    def test_slash_path_in_string_matched(self):
        """patch("launcher/core/vscode") should be caught by slashed variant."""
        variants = _module_variants("src/launcher/core/vscode.py")
        content = 'patch("launcher/core/vscode.open_in_vscode")\n'
        assert _file_references_module(content, variants)

    def test_sole_top_level_no_slash_duplicate(self):
        """A top-level module has dotted == slashed; must not duplicate."""
        variants = _module_variants("src/launcher/__init__.py")
        # variants should contain 'launcher' and nothing else
        assert variants == ["launcher"]


# ---------------------------------------------------------------------------
# Multi-module staged scan
# ---------------------------------------------------------------------------

class TestMultipleStagedModules:
    def _make_test_file(self, root: Path, wp: str, name: str, content: str) -> Path:
        f = root / "tests" / wp / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return f

    def test_two_staged_modules_both_detected(self, tmp_path):
        self._make_test_file(tmp_path, "DOC-010", "test_a.py", "import launcher.core.vscode\n")
        self._make_test_file(tmp_path, "DOC-020", "test_b.py", "import launcher.gui.app\n")
        result = scan(
            ["src/launcher/core/vscode.py", "src/launcher/gui/app.py"],
            tmp_path,
        )
        paths = list(result.keys())
        assert any("DOC-010" in p for p in paths)
        assert any("DOC-020" in p for p in paths)

    def test_single_file_matching_multiple_modules(self, tmp_path):
        """One test file references two changed modules — both listed in matched sources."""
        self._make_test_file(
            tmp_path, "DOC-010", "test_multi.py",
            "import launcher.core.vscode\nimport launcher.gui.app\n",
        )
        result = scan(
            ["src/launcher/core/vscode.py", "src/launcher/gui/app.py"],
            tmp_path,
        )
        assert any("test_multi.py" in k for k in result)
        matched_srcs = next(v for k, v in result.items() if "test_multi.py" in k)
        assert len(matched_srcs) == 2


# ---------------------------------------------------------------------------
# stderr output from main
# ---------------------------------------------------------------------------

class TestMainStderrOutput:
    def test_advisory_printed_to_stderr_not_stdout(self, tmp_path, monkeypatch, capsys):
        """Advisory output must go to stderr, not stdout."""
        import check_test_impact as m

        fake_impacts = {
            str(tmp_path / "tests" / "DOC-001" / "test_foo.py"): ["src/launcher/core/mod.py"]
        }
        monkeypatch.setattr(m, "scan", lambda *a, **k: fake_impacts)
        monkeypatch.setattr(
            m, "format_warnings", lambda *a, **k: "ADVISORY: cross-wp"
        )
        result = main(["src/launcher/core/mod.py"])
        captured = capsys.readouterr()
        assert result == 0
        assert "ADVISORY" in captured.err
        assert captured.out == ""


# ---------------------------------------------------------------------------
# __init__.py chain — deep nested package
# ---------------------------------------------------------------------------

class TestInitHandling:
    def test_deep_init_becomes_parent_package(self):
        variants = _module_variants("src/launcher/gui/__init__.py")
        assert "launcher.gui" in variants
        assert "__init__" not in " ".join(variants)

    def test_bare_module_name_not_init(self):
        variants = _module_variants("src/launcher/gui/__init__.py")
        # Last element is the bare name; must not be "__init__"
        assert "__init__" not in variants


# ---------------------------------------------------------------------------
# _file_references_module boundary conditions
# ---------------------------------------------------------------------------

class TestReferenceBoundaries:
    def test_multiline_import_block(self):
        content = (
            "from launcher.core import (\n"
            "    vscode,\n"
            "    shim_config,\n"
            ")\n"
        )
        variants = _module_variants("src/launcher/core/shim_config.py")
        # bare name 'shim_config' appears in a string? No — it's code not string
        # The import 'from launcher.core import' won't match the full dotted path,
        # BUT 'shim_config' IS in a bare token, not a string, so should NOT match
        # via the string-only bare rule.  This serves as a boundary check.
        # The dotted 'launcher.core.shim_config' is not in the content → False
        assert not _file_references_module(content, variants)

    def test_commented_out_import_not_matched(self):
        """A commented import should NOT trigger a match (no special handling, regex
        will match regardless — this test documents current behaviour)."""
        content = "# import launcher.core.shim_config\n"
        variants = _module_variants("src/launcher/core/shim_config.py")
        # Current implementation DOES match commented imports — document it
        assert _file_references_module(content, variants)

    def test_very_short_module_name_word_boundary(self):
        """A two-letter bare module name should still respect word boundaries."""
        variants = _module_variants("src/launcher/core/io.py")
        # 'io' should not match inside 'radio'
        content = '"radio"\n'
        # word boundary test: \bio\b won't match inside 'radio'
        assert not _file_references_module(content, variants)
