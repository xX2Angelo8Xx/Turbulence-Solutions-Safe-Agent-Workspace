"""
Edge-case tests for FIX-010: Fix CI/CD Release Pipeline Failures

Additional tests beyond the Developer's baseline, covering:
  1. release job 'needs' array integrity (all 4 build jobs referenced, no typos)
  2. Workflow has no hardcoded secrets or API tokens
  3. No duplicate step names within any single job
  4. config.py VERSION as the 5th version source (cross-checks against pyproject.toml)
  5. All five version sources match simultaneously
  6. Version strings are valid semver (x.y.z format)
  7. macos-intel-build has BOTH macos-15 runner AND x64 architecture (combined check)
  8. macos-arm-build does NOT accidentally specify x64 architecture
  9. Source path in setup.iss actually resolves to repo root via filesystem path walking
 10. Artifact upload paths reference the correct output file types
 11. Workflow triggers only on version tags (not branches)
"""
import pathlib
import re
import tomllib

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
SETUP_ISS = REPO_ROOT / "src" / "installer" / "windows" / "setup.iss"
BUILD_DMG = REPO_ROOT / "src" / "installer" / "macos" / "build_dmg.sh"
BUILD_APPIMAGE = REPO_ROOT / "src" / "installer" / "linux" / "build_appimage.sh"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONFIG_PY = REPO_ROOT / "src" / "launcher" / "config.py"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
EXPECTED_BUILD_JOBS = {"windows-build", "macos-intel-build", "macos-arm-build", "linux-build"}


@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def workflow_raw():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def release_job(workflow):
    return workflow["jobs"]["release"]


@pytest.fixture(scope="module")
def intel_job(workflow):
    return workflow["jobs"]["macos-intel-build"]


@pytest.fixture(scope="module")
def arm_job(workflow):
    return workflow["jobs"]["macos-arm-build"]


# ---------------------------------------------------------------------------
# release job 'needs' array integrity
# ---------------------------------------------------------------------------

def test_release_job_needs_all_four_build_jobs(release_job):
    """release job must declare all 4 build jobs in 'needs'.

    If any build job is missing, the release job will start before all
    artifacts are ready, producing an incomplete or empty release.
    """
    needs = set(release_job.get("needs", []))
    missing = EXPECTED_BUILD_JOBS - needs
    assert not missing, (
        f"release job is missing these build jobs in 'needs': {sorted(missing)}. "
        "All 4 build jobs must complete before the release job runs."
    )


def test_release_job_needs_exact_four(release_job):
    """release job 'needs' must have exactly 4 entries — no spurious extra dependencies."""
    needs = release_job.get("needs", [])
    assert len(needs) == 4, (
        f"Expected exactly 4 jobs in release.needs, got {len(needs)}: {needs}"
    )


def test_release_job_needs_no_typos(release_job, workflow):
    """Every job name in release.needs must be defined in the workflow.

    A typo in a needs entry causes a silent failure — the workflow will
    error with an unhelpful 'invalid workflow' message instead of detecting
    a missing artifact.
    """
    defined_jobs = set(workflow.get("jobs", {}).keys())
    for dep in release_job.get("needs", []):
        assert dep in defined_jobs, (
            f"release job needs '{dep}' which is not defined in the workflow. "
            f"Defined jobs: {sorted(defined_jobs)}"
        )


# ---------------------------------------------------------------------------
# No hardcoded secrets or tokens in the workflow
# ---------------------------------------------------------------------------

def test_workflow_no_hardcoded_api_tokens(workflow_raw):
    """Workflow YAML must not contain hardcoded GitHub API tokens.

    Valid references use the ${{ secrets.* }} syntax. Bare token values
    (ghp_, github_pat_, ghs_ prefixes) indicate a hardcoded credential
    and must never appear in a committed file.
    """
    hardcoded_patterns = [
        r"ghp_[A-Za-z0-9]{36}",        # classic PAT
        r"github_pat_[A-Za-z0-9_]+",    # fine-grained PAT
        r"ghs_[A-Za-z0-9]{36}",         # installation token
    ]
    for pattern in hardcoded_patterns:
        match = re.search(pattern, workflow_raw)
        assert match is None, (
            f"Found what appears to be a hardcoded secret in release.yml "
            f"(matched pattern {pattern!r}). Use ${{{{ secrets.VARIABLE }}}} instead."
        )


def test_workflow_no_hardcoded_passwords(workflow_raw):
    """Workflow must not contain a 'password:' key with a literal (non-secret) value."""
    # Match 'password:' followed by anything that is not a ${{ secrets.* }} reference
    matches = re.findall(
        r"password:\s*(?!\$\{\{)[^\n]+",
        workflow_raw,
        re.IGNORECASE,
    )
    assert not matches, (
        f"Possible hardcoded password found in release.yml: {matches}"
    )


# ---------------------------------------------------------------------------
# No duplicate step names within any single job
# ---------------------------------------------------------------------------

def test_no_job_has_duplicate_step_names(workflow):
    """Every job must have unique step names within that job.

    Duplicate step names cause confusion in the Actions UI and can silently
    mask bugs where one step's output is attributed to a different step.
    """
    for job_name, job in workflow.get("jobs", {}).items():
        steps = job.get("steps", [])
        named_steps = [s.get("name") for s in steps if s.get("name")]
        seen: set = set()
        for name in named_steps:
            assert name not in seen, (
                f"Job '{job_name}' has duplicate step name: {name!r}. "
                "All step names within a job must be unique."
            )
            seen.add(name)


# ---------------------------------------------------------------------------
# config.py VERSION as the 5th version source
# ---------------------------------------------------------------------------

def _extract_config_py_version() -> str:
    content = CONFIG_PY.read_text(encoding="utf-8")
    match = re.search(r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match, "Could not parse VERSION from src/launcher/config.py"
    return match.group(1)


def _extract_pyproject_version() -> str:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def _extract_iss_version() -> str:
    match = re.search(
        r'#define MyAppVersion\s+"([^"]+)"',
        SETUP_ISS.read_text(encoding="utf-8"),
    )
    assert match, "Could not parse MyAppVersion from setup.iss"
    return match.group(1)


def _extract_dmg_version() -> str:
    match = re.search(
        r'^APP_VERSION="([^"]+)"',
        BUILD_DMG.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, "Could not parse APP_VERSION from build_dmg.sh"
    return match.group(1)


def _extract_appimage_version() -> str:
    match = re.search(
        r'^APP_VERSION="([^"]+)"',
        BUILD_APPIMAGE.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, "Could not parse APP_VERSION from build_appimage.sh"
    return match.group(1)


def test_config_py_version_matches_pyproject():
    """src/launcher/config.py VERSION must match pyproject.toml project version.

    config.py is the runtime version constant shown in the GUI. It must stay
    in sync with pyproject.toml or the 'About' display will show a stale version.
    """
    pyproject_ver = _extract_pyproject_version()
    config_ver = _extract_config_py_version()
    assert config_ver == pyproject_ver, (
        f"config.py VERSION {config_ver!r} does not match "
        f"pyproject.toml version {pyproject_ver!r}"
    )


def test_all_five_version_sources_match():
    """All 5 version sources must agree simultaneously.

    Sources: config.py, pyproject.toml, setup.iss, build_dmg.sh, build_appimage.sh.
    A single mismatch anywhere causes the installer to report the wrong version
    while the binary itself may report a different one — breaking the update flow.
    """
    versions = {
        "config.py": _extract_config_py_version(),
        "pyproject.toml": _extract_pyproject_version(),
        "setup.iss": _extract_iss_version(),
        "build_dmg.sh": _extract_dmg_version(),
        "build_appimage.sh": _extract_appimage_version(),
    }
    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across all 5 sources: {versions}"
    )


# ---------------------------------------------------------------------------
# Valid semver format
# ---------------------------------------------------------------------------

def test_pyproject_version_is_valid_semver():
    """pyproject.toml version must be valid semver (MAJOR.MINOR.PATCH)."""
    ver = _extract_pyproject_version()
    assert SEMVER_RE.match(ver), (
        f"pyproject.toml version {ver!r} is not valid semver (expected x.y.z format)."
    )


def test_setup_iss_version_is_valid_semver():
    """setup.iss MyAppVersion must be valid semver (MAJOR.MINOR.PATCH)."""
    ver = _extract_iss_version()
    assert SEMVER_RE.match(ver), (
        f"setup.iss version {ver!r} is not valid semver (expected x.y.z format)."
    )


# ---------------------------------------------------------------------------
# macos-intel-build: BOTH macos-15 AND x64 architecture (combined check)
# ---------------------------------------------------------------------------

def test_macos_intel_build_has_both_macos15_runner_and_x64_arch(intel_job):
    """macos-intel-build must have BOTH macos-15 runner AND x64 architecture.

    Either alone is insufficient:
      - macos-15 without x64 may install ARM Python silently on the Intel runner.
      - x64 without macos-15 references a deprecated (unavailable) runner.
    Both conditions must be true simultaneously.
    """
    runner = intel_job.get("runs-on")
    assert runner == "macos-15", f"Expected runner 'macos-15', got {runner!r}"

    arch = None
    for step in intel_job.get("steps", []):
        if step.get("uses", "").startswith("actions/setup-python"):
            arch = step.get("with", {}).get("architecture")
            break
    assert arch == "x64", (
        f"macos-intel-build has runner=macos-15 but setup-python architecture={arch!r}. "
        "Both 'runs-on: macos-15' AND 'architecture: x64' are required together."
    )


def test_macos_arm_does_not_have_x64_architecture(arm_job):
    """macos-arm-build setup-python must NOT specify architecture: x64.

    The ARM build relies on Apple Silicon (arm64) natively. Forcing x64 would
    produce an Intel binary on the ARM runner — a silent architecture mismatch.
    """
    for step in arm_job.get("steps", []):
        if step.get("uses", "").startswith("actions/setup-python"):
            arch = step.get("with", {}).get("architecture")
            assert arch != "x64", (
                "macos-arm-build setup-python has architecture: x64 which would "
                "produce the wrong binary. ARM builds must use the host arm64 Python."
            )
            return


# ---------------------------------------------------------------------------
# Filesystem path resolution: setup.iss Source path walks to repo root
# ---------------------------------------------------------------------------

def test_setup_iss_source_path_resolves_to_repo_root_on_filesystem():
    """The ..\\..\\..\\  prefix in setup.iss Source must resolve to the repo root.

    This verifies the path navigation actually works on the filesystem —
    not just that the correct number of '..' segments is present.
    Walking three parent steps from src/installer/windows/ must land at the
    repo root where PyInstaller places its dist/ output.
    """
    iss_dir = SETUP_ISS.parent  # src/installer/windows/
    content = SETUP_ISS.read_text(encoding="utf-8")
    source_match = re.search(r'Source:\s*"([^"]+)"', content)
    assert source_match, "No Source: path found in setup.iss"
    source_val = source_match.group(1)

    # Count parent-traversal segments at the start of the path
    parts = [p for p in source_val.replace("/", "\\").split("\\") if p]
    prefix_parts = [p for p in parts if p == ".."]

    resolved = iss_dir
    for _ in prefix_parts:
        resolved = resolved.parent

    assert resolved.resolve() == REPO_ROOT.resolve(), (
        f"Source path prefix {source_val!r} resolved from {iss_dir} gives "
        f"{resolved.resolve()}, but expected repo root {REPO_ROOT.resolve()}."
    )


# ---------------------------------------------------------------------------
# Artifact upload paths reference correct output file types
# ---------------------------------------------------------------------------

def test_windows_artifact_upload_path_contains_exe(workflow):
    """windows-build artifact upload path must reference the .exe installer."""
    job = workflow["jobs"]["windows-build"]
    for step in job.get("steps", []):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert ".exe" in path, (
                f"Windows artifact upload path {path!r} does not reference an .exe file. "
                "Expected AgentEnvironmentLauncher-Setup.exe."
            )
            return
    pytest.fail("No upload-artifact step found in windows-build")


def test_macos_intel_artifact_upload_path_is_dmg(workflow):
    """macos-intel-build artifact upload path must reference .dmg files."""
    job = workflow["jobs"]["macos-intel-build"]
    for step in job.get("steps", []):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert ".dmg" in path, (
                f"macOS Intel artifact upload path {path!r} does not reference a .dmg file."
            )
            return
    pytest.fail("No upload-artifact step found in macos-intel-build")


def test_linux_artifact_upload_path_is_appimage(workflow):
    """linux-build artifact upload path must reference .AppImage files."""
    job = workflow["jobs"]["linux-build"]
    for step in job.get("steps", []):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            path = step.get("with", {}).get("path", "")
            assert ".AppImage" in path, (
                f"Linux artifact upload path {path!r} does not reference an .AppImage file."
            )
            return
    pytest.fail("No upload-artifact step found in linux-build")


# ---------------------------------------------------------------------------
# Workflow triggers only on version tags (not branches)
# ---------------------------------------------------------------------------

def test_workflow_triggers_only_on_version_tags(workflow):
    """Workflow must trigger on version-pattern tags and not on branch pushes.

    PyYAML parses 'on:' as the boolean True key. The release workflow must
    only run on tags to prevent accidental release builds from branch pushes.
    """
    # PyYAML safe_load parses bare 'on' as True (YAML boolean)
    on_config = workflow.get(True, workflow.get("on", {}))
    push_config = on_config.get("push", {})
    tag_patterns = push_config.get("tags", [])

    assert tag_patterns, (
        "Workflow has no tag trigger — release cannot be triggered by pushing a version tag."
    )
    assert any("v" in p for p in tag_patterns), (
        f"Tag patterns {tag_patterns!r} don't include a version tag pattern (e.g. 'v*.*.*'). "
        "Release builds require a version-prefixed tag trigger."
    )

    # Branch pushes must not trigger the release workflow
    branches = push_config.get("branches", [])
    assert not branches, (
        f"Workflow has branch triggers {branches!r} in addition to tag triggers. "
        "Release workflows must only trigger on version tags, not branch pushes."
    )
