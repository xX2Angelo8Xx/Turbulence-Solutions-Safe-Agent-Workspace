"""Tests for scripts/check_test_impact.py (MNT-025)."""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

# Make scripts/ importable
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_test_impact import (  # noqa: E402
    _module_variants,
    _wp_id_from_test_path,
    _file_references_module,
    scan,
    format_warnings,
    main,
)


# ---------------------------------------------------------------------------
# _module_variants
# ---------------------------------------------------------------------------

class TestModuleVariants:
    def test_standard_src_path(self):
        variants = _module_variants("src/launcher/core/shim_config.py")
        assert "launcher.core.shim_config" in variants
        assert "launcher/core/shim_config" in variants
        assert "shim_config" in variants

    def test_top_level_module(self):
        variants = _module_variants("src/launcher/__init__.py")
        assert "launcher" in variants

    def test_no_src_prefix(self):
        # Files not under src/ return empty or minimal
        variants = _module_variants("scripts/some_tool.py")
        # should include bare name at minimum
        assert "some_tool" in variants

    def test_deep_path(self):
        variants = _module_variants("src/launcher/gui/app.py")
        assert "launcher.gui.app" in variants
        assert "app" in variants


# ---------------------------------------------------------------------------
# _wp_id_from_test_path
# ---------------------------------------------------------------------------

class TestWpIdFromTestPath:
    def test_known_wp(self, tmp_path):
        tests_root = tmp_path / "tests"
        test_file = tests_root / "DOC-042" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        assert _wp_id_from_test_path(test_file, tests_root) == "DOC-042"

    def test_direct_child(self, tmp_path):
        tests_root = tmp_path / "tests"
        test_file = tests_root / "test_root.py"
        tests_root.mkdir()
        test_file.touch()
        assert _wp_id_from_test_path(test_file, tests_root) == "test_root.py"

    def test_outside_tests(self, tmp_path):
        tests_root = tmp_path / "tests"
        tests_root.mkdir()
        other = tmp_path / "scripts" / "test_foo.py"
        other.parent.mkdir()
        other.touch()
        # relative_to raises, returns ''
        assert _wp_id_from_test_path(other, tests_root) == ""


# ---------------------------------------------------------------------------
# _file_references_module
# ---------------------------------------------------------------------------

class TestFileReferencesModule:
    def _variants(self, src_path: str) -> list[str]:
        return _module_variants(src_path)

    def test_import_statement(self):
        content = "import launcher.core.shim_config\n"
        assert _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))

    def test_from_import(self):
        content = "from launcher.core.shim_config import ShimConfig\n"
        assert _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))

    def test_patch_string(self):
        content = 'patch("launcher.core.shim_config.subprocess.run")\n'
        assert _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))

    def test_bare_name_in_string(self):
        content = 'some_func("shim_config")\n'
        assert _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))

    def test_no_reference(self):
        content = "import os\nimport sys\nprint('hello')\n"
        assert not _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))

    def test_partial_name_no_false_positive(self):
        # "my_shim_config_extra" should not match bare "shim_config" due to word boundary
        content = '"my_shim_config_extra"\n'
        # word boundary (\b) is used so this should NOT match
        assert not _file_references_module(content, self._variants("src/launcher/core/shim_config.py"))


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

class TestScan:
    def _make_test_file(self, root: Path, wp: str, name: str, content: str) -> Path:
        f = root / "tests" / wp / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return f

    def test_finds_import_reference(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_foo.py",
            "import launcher.core.shim_config\n"
        )
        results = scan(["src/launcher/core/shim_config.py"], tmp_path)
        assert any("test_foo.py" in k for k in results)

    def test_no_staged_files_yields_empty(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_bar.py",
            "import launcher.core.shim_config\n"
        )
        results = scan([], tmp_path)
        assert results == {}

    def test_non_src_files_are_ignored(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_baz.py",
            "import launcher.core.shim_config\n"
        )
        # Pass a scripts/ file — not under src/
        results = scan(["scripts/some_tool.py"], tmp_path)
        assert results == {}

    def test_no_matching_test_yields_empty(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_unrelated.py",
            "import os\nimport sys\n"
        )
        results = scan(["src/launcher/core/shim_config.py"], tmp_path)
        assert results == {}

    def test_multiple_wps(self, tmp_path):
        self._make_test_file(
            tmp_path, "DOC-001", "test_a.py",
            "from launcher.core.shim_config import X\n"
        )
        self._make_test_file(
            tmp_path, "FIX-042", "test_b.py",
            'patch("launcher.core.shim_config.subprocess")\n'
        )
        results = scan(["src/launcher/core/shim_config.py"], tmp_path)
        paths = list(results.keys())
        assert any("DOC-001" in p for p in paths)
        assert any("FIX-042" in p for p in paths)


# ---------------------------------------------------------------------------
# format_warnings
# ---------------------------------------------------------------------------

class TestFormatWarnings:
    def _make_impacts(self, tmp_path: Path) -> dict[str, list[str]]:
        test_file = tmp_path / "tests" / "DOC-001" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        return {str(test_file): ["src/launcher/core/shim_config.py"]}

    def test_contains_advisory_header(self, tmp_path):
        impacts = self._make_impacts(tmp_path)
        out = format_warnings(impacts, ["src/launcher/core/shim_config.py"], tmp_path)
        assert "ADVISORY" in out
        assert "ADR-008" in out

    def test_contains_wp_label(self, tmp_path):
        impacts = self._make_impacts(tmp_path)
        out = format_warnings(impacts, ["src/launcher/core/shim_config.py"], tmp_path)
        assert "DOC-001" in out

    def test_empty_impacts_returns_empty_string(self, tmp_path):
        out = format_warnings({}, [], tmp_path)
        assert out == ""


# ---------------------------------------------------------------------------
# main (exit code)
# ---------------------------------------------------------------------------

class TestMainExitCode:
    def test_exits_zero_with_no_args(self):
        assert main([]) == 0

    def test_exits_zero_even_with_impacts(self, tmp_path, monkeypatch):
        """Exit code must be 0 even when impacts are found (advisory only)."""
        # Patch repo_root resolution inside main by monkey-patching scan
        import check_test_impact as m
        fake_impacts = {str(tmp_path / "tests" / "DOC-001" / "test_foo.py"): ["src/launcher/core/mod.py"]}
        monkeypatch.setattr(m, "scan", lambda *a, **k: fake_impacts)
        monkeypatch.setattr(m, "format_warnings", lambda *a, **k: "ADVISORY: something")
        result = main(["src/launcher/core/mod.py"])
        assert result == 0

    def test_exits_zero_with_non_src_args(self):
        assert main(["scripts/some_tool.py"]) == 0
