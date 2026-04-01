"""
DOC-048 — Tester edge-case tests: SAE prefix rename verification.

These tests verify that all test files updated by DOC-048 have had the
old `TS-SAE` prefix fully replaced with `SAE` and that no stale references
remain.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]

UPDATED_FILES = [
    REPO_ROOT / "tests" / "DOC-001" / "test_doc001_placeholder.py",
    REPO_ROOT / "tests" / "DOC-001" / "test_doc001_edge_cases.py",
    REPO_ROOT / "tests" / "DOC-009" / "test_doc009_placeholder_replacement.py",
    REPO_ROOT / "tests" / "DOC-009" / "test_doc009_tester_edge_cases.py",
    REPO_ROOT / "tests" / "DOC-040" / "test_doc040_version_file.py",
    REPO_ROOT / "tests" / "FIX-044" / "test_fix044_readonly_placeholder.py",
    REPO_ROOT / "tests" / "GUI-017" / "test_gui017_ui_labels.py",
    REPO_ROOT / "tests" / "GUI-017" / "test_gui017_edge_cases.py",
    REPO_ROOT / "tests" / "INS-004" / "test_ins004_template_bundling.py",
]

# Pattern that must not appear in any updated file
STALE_PATTERN = re.compile(r"TS-SAE")

# Pattern that must appear in at least one assertion per file
REPLACEMENT_PATTERN = re.compile(r"SAE-")


# ---------------------------------------------------------------------------
# Tests: no stale TS-SAE references remain
# ---------------------------------------------------------------------------

class TestNoStaleReferences:
    """Every updated test file must be free of the old TS-SAE prefix."""

    def _check_file(self, filepath: Path) -> None:
        assert filepath.exists(), f"Expected test file not found: {filepath}"
        content = filepath.read_text(encoding="utf-8")
        matches = STALE_PATTERN.findall(content)
        assert len(matches) == 0, (
            f"Found {len(matches)} stale 'TS-SAE' reference(s) in {filepath.name}:\n"
            + "\n".join(
                f"  line {i+1}: {line.strip()}"
                for i, line in enumerate(content.splitlines())
                if STALE_PATTERN.search(line)
            )
        )

    def test_doc001_placeholder_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-001" / "test_doc001_placeholder.py")

    def test_doc001_edge_cases_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-001" / "test_doc001_edge_cases.py")

    def test_doc009_placeholder_replacement_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-009" / "test_doc009_placeholder_replacement.py")

    def test_doc009_tester_edge_cases_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-009" / "test_doc009_tester_edge_cases.py")

    def test_doc040_version_file_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-040" / "test_doc040_version_file.py")

    def test_fix044_readonly_placeholder_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "FIX-044" / "test_fix044_readonly_placeholder.py")

    def test_gui017_ui_labels_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "GUI-017" / "test_gui017_ui_labels.py")

    def test_gui017_edge_cases_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "GUI-017" / "test_gui017_edge_cases.py")

    def test_ins004_template_bundling_no_ts_sae(self):
        self._check_file(REPO_ROOT / "tests" / "INS-004" / "test_ins004_template_bundling.py")


# ---------------------------------------------------------------------------
# Tests: SAE- prefix is present in updated assertion strings
# ---------------------------------------------------------------------------

class TestSaePrefixUsed:
    """Every updated test file must reference the new SAE- prefix in assertions."""

    def _check_file(self, filepath: Path) -> None:
        assert filepath.exists(), f"Expected test file not found: {filepath}"
        content = filepath.read_text(encoding="utf-8")
        assert REPLACEMENT_PATTERN.search(content), (
            f"No 'SAE-' reference found in {filepath.name} — replacement may not have been applied."
        )

    def test_doc001_placeholder_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-001" / "test_doc001_placeholder.py")

    def test_doc001_edge_cases_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-001" / "test_doc001_edge_cases.py")

    def test_doc009_placeholder_replacement_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-009" / "test_doc009_placeholder_replacement.py")

    def test_doc009_tester_edge_cases_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-009" / "test_doc009_tester_edge_cases.py")

    def test_doc040_version_file_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "DOC-040" / "test_doc040_version_file.py")

    def test_fix044_readonly_placeholder_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "FIX-044" / "test_fix044_readonly_placeholder.py")

    def test_gui017_ui_labels_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "GUI-017" / "test_gui017_ui_labels.py")

    def test_gui017_edge_cases_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "GUI-017" / "test_gui017_edge_cases.py")

    def test_ins004_template_bundling_uses_sae(self):
        self._check_file(REPO_ROOT / "tests" / "INS-004" / "test_ins004_template_bundling.py")


# ---------------------------------------------------------------------------
# Tests: all updated files exist (guard against accidental deletion)
# ---------------------------------------------------------------------------

class TestUpdatedFilesExist:
    """All files that DOC-048 updated must still exist on disk."""

    def test_all_updated_files_exist(self):
        missing = [str(f) for f in UPDATED_FILES if not f.exists()]
        assert not missing, f"Missing updated test files:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# Edge case: no double-prefix (TS-SAE-SAE- or SAE-SAE-) introduced
# ---------------------------------------------------------------------------

class TestNoDoublePrefix:
    """Ensure no double-prefix artefacts were introduced during replacement."""

    def test_no_double_sae_prefix_any_file(self):
        """Check for unintentional SAE-SAE- double-prefix artefacts.

        test_gui017_edge_cases.py is excluded because it deliberately tests the
        app behaviour when a user types a name that already starts with 'SAE-'
        (the code adds the prefix unconditionally, so 'SAE-Foo' → 'SAE-SAE-Foo').
        That specific class is named TestNoPrefixDoubling and documents the
        intentional behaviour; it is not an artefact of the rename.
        """
        double_prefix = re.compile(r"SAE-SAE-")
        # Files where SAE-SAE- is intentionally documented as expected app behaviour
        intentional_exceptions = {"test_gui017_edge_cases.py"}
        offenders = []
        for filepath in UPDATED_FILES:
            if filepath.name in intentional_exceptions:
                continue
            if not filepath.exists():
                continue
            content = filepath.read_text(encoding="utf-8")
            if double_prefix.search(content):
                offenders.append(filepath.name)
        assert not offenders, (
            f"Unintentional double SAE-SAE- prefix found in: {offenders}"
        )

    def test_no_ts_sae_sae_hybrid(self):
        """No partial replacement left a TS-SAE-SAE- hybrid string."""
        hybrid = re.compile(r"TS-SAE-SAE-")
        offenders = []
        for filepath in UPDATED_FILES:
            if not filepath.exists():
                continue
            content = filepath.read_text(encoding="utf-8")
            if hybrid.search(content):
                offenders.append(filepath.name)
        assert not offenders, (
            f"Hybrid TS-SAE-SAE- prefix found in: {offenders}"
        )

    def test_gui017_edge_cases_double_prefix_is_documented(self):
        """The SAE-SAE- occurrence in gui017_edge_cases is intentional and documented.

        The original test had TS-SAE-TS-SAE-Foo to document that the app always
        adds the prefix even if the user types it. After the rename it becomes
        SAE-SAE-Foo.  Verify the test class is explicitly named to communicate intent.
        """
        filepath = REPO_ROOT / "tests" / "GUI-017" / "test_gui017_edge_cases.py"
        assert filepath.exists()
        content = filepath.read_text(encoding="utf-8")
        # The intentional double-prefix must live inside a class that makes the
        # intent clear — either TestNoPrefixDoubling or similar.
        assert "TestNoPrefixDoubling" in content, (
            "Expected 'TestNoPrefixDoubling' class to document the intentional double-prefix test."
        )
