"""FIX-106: Fix CI, codesign, and security test assertions.

Regression tests that confirm:
1. build_dmg.sh uses single-line signing for dylib/so/Python.framework
   (previously multi-line, causing FIX-028/FIX-031/FIX-038/FIX-039 failures)
2. release.yml Verify Code Signing step uses pre-bundle binary path
   (previously used Contents/MacOS/launcher, causing FIX-029/FIX-039 failures)
3. release.yml has 6 jobs (previously tests expected 4, causing INS-013 failure)
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"


def _build_dmg_text():
    return BUILD_DMG.read_text(encoding="utf-8")


def _release_yml_text():
    return RELEASE_YML.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# build_dmg.sh regressions                                                     #
# --------------------------------------------------------------------------- #

def test_dylib_signing_is_single_line():
    """Dylib signing must appear as a single find -exec codesign line (not multi-line)."""
    text = _build_dmg_text()
    match = re.search(
        r'find[^\n]*\*\.dylib[^\n]*codesign[^\n]*--force[^\n]*--sign\s+-[^\n]*\\;',
        text,
    )
    assert match, (
        "build_dmg.sh: expected single-line dylib signing "
        "(find ... -name '*.dylib' -exec codesign --force ... --sign - {} ;)"
    )


def test_so_signing_is_single_line():
    """SO signing must appear as a single find -exec codesign line (not multi-line)."""
    text = _build_dmg_text()
    match = re.search(
        r'find[^\n]*\*\.so[^\n]*codesign[^\n]*--force[^\n]*--sign\s+-[^\n]*\\;',
        text,
    )
    assert match, (
        "build_dmg.sh: expected single-line .so signing "
        "(find ... -name '*.so' -exec codesign --force ... --sign - {} ;)"
    )


def test_python_framework_signing_is_single_line():
    """Python.framework signing must be a single codesign call (not multi-line)."""
    text = _build_dmg_text()
    # Find line(s) that sign Python.framework
    fw_lines = [l for l in text.splitlines() if 'Python.framework' in l and 'codesign' in l and '--sign' in l]
    assert len(fw_lines) == 1, (
        f"Expected exactly 1 line signing Python.framework with codesign, got {len(fw_lines)}: {fw_lines}"
    )


def test_pre_bundle_binary_verify_present():
    """build_dmg.sh must verify the pre-bundle binary before creating DMG."""
    text = _build_dmg_text()
    assert 'codesign --verify' in text and 'launcher/launcher' in text, (
        "build_dmg.sh: expected 'codesign --verify ... launcher/launcher' "
        "(pre-bundle binary verification)"
    )


def test_no_verify_launcher_inside_bundle():
    """Launcher inside APP bundle must NOT be verified separately (CFBundleExecutable handles it)."""
    text = _build_dmg_text()
    # codesign --verify on the launcher inside .app is the old pattern we removed
    assert not re.search(r'codesign --verify[^\n]*Contents/MacOS/launcher', text), (
        "build_dmg.sh still has codesign --verify on Contents/MacOS/launcher – "
        "this was removed in FIX-106 (CFBundleExecutable handles it)"
    )


def test_explanatory_comment_bundle_skip():
    """build_dmg.sh must contain the explanatory comment about skipping bundle-level deep sign."""
    text = _build_dmg_text()
    assert 'Bundle-level signing is intentionally skipped' in text, (
        "Missing explanatory comment 'Bundle-level signing is intentionally skipped' in build_dmg.sh"
    )


# --------------------------------------------------------------------------- #
# release.yml regressions                                                      #
# --------------------------------------------------------------------------- #

def test_release_yml_verify_uses_pre_bundle_path():
    """Verify Code Signing step must verify dist/launcher/launcher (pre-bundle path)."""
    text = _release_yml_text()
    assert 'dist/launcher/launcher' in text, (
        "release.yml: Verify Code Signing step must reference 'dist/launcher/launcher'"
    )


def test_release_yml_verify_no_contents_macos_launcher():
    """Verify Code Signing step must NOT verify Contents/MacOS/launcher (old wrong path)."""
    text = _release_yml_text()
    # Check only the verify step context - search for the pattern in the whole file
    # The old pattern was checking Contents/MacOS/launcher in the verify step
    verify_section_match = re.search(
        r'- name: Verify Code Signing.*?(?=\n  - name:|\Z)',
        text,
        re.DOTALL,
    )
    if verify_section_match:
        section = verify_section_match.group(0)
        assert 'Contents/MacOS/launcher' not in section, (
            "release.yml: Verify Code Signing step still checks 'Contents/MacOS/launcher' – "
            "should use 'dist/launcher/launcher' (pre-bundle path)"
        )


def test_release_yml_has_six_jobs():
    """release.yml must define exactly 6 jobs (validate-version, run-tests, windows-build,
    macos-arm-build, linux-build, release)."""
    import yaml  # type: ignore
    with open(RELEASE_YML, encoding="utf-8") as f:
        workflow = yaml.safe_load(f)
    jobs = workflow.get("jobs", {})
    assert len(jobs) == 6, (
        f"release.yml: expected 6 jobs, got {len(jobs)}: {list(jobs.keys())}"
    )


def test_release_yml_verify_step_echo_confirmation():
    """Verify Code Signing step must echo 'Code signing verification passed'."""
    text = _release_yml_text()
    assert 'Code signing verification passed' in text, (
        "release.yml: missing 'Code signing verification passed' echo in Verify Code Signing step"
    )
