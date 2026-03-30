"""
Edge-case tests for MNT-005: Add CI validate-version job to release workflow.
Written by Tester Agent — these go beyond the Developer's tests.

Focus areas:
- YAML validity and complete structural correctness
- Exact action pin versions (checkout@v4 not v3)
- grep fault-tolerance (|| true) for all 5 version checks
- GITHUB_OUTPUT correct usage
- Step ID / step output reference consistency
- Tag-without-v-prefix edge case (${TAG#v} semantics)
- All 5 version check steps independently call exit 1 on mismatch
- release job does NOT gain validate-version dependency (transitive is sufficient)
- No secrets or credentials injected
- validate-version job has no build dependencies (it runs first, clean)
- All expected file paths actually exist in the repository
"""
import os
import re
import pytest
import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RELEASE_YML = os.path.join(REPO_ROOT, ".github", "workflows", "release.yml")


@pytest.fixture(scope="module")
def release_yml_text():
    with open(RELEASE_YML, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def release_yml_data(release_yml_text):
    return yaml.safe_load(release_yml_text)


# ---------------------------------------------------------------------------
# YAML validity
# ---------------------------------------------------------------------------

def test_yaml_parses_without_error():
    """The workflow file must be valid YAML — any syntax error raises an exception."""
    with open(RELEASE_YML, "r", encoding="utf-8") as f:
        raw = f.read()
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict), "release.yml did not parse to a dict"


def test_yaml_has_jobs_key(release_yml_data):
    """Top-level 'jobs' key must be present."""
    assert "jobs" in release_yml_data


def test_yaml_has_on_key(release_yml_data):
    """Top-level 'on' key (trigger) must be present."""
    assert "on" in release_yml_data or True in release_yml_data, (
        "No trigger (on:) found in workflow"
    )


# ---------------------------------------------------------------------------
# Exact action pin: checkout@v4 (not v3)
# ---------------------------------------------------------------------------

def test_validate_version_uses_checkout_v4_exactly(release_yml_data):
    """The validate-version job must use actions/checkout@v4 (not v3 or unversioned)."""
    job = release_yml_data["jobs"]["validate-version"]
    steps = job["steps"]
    checkout_uses = [str(s.get("uses", "")) for s in steps if "checkout" in str(s.get("uses", ""))]
    assert len(checkout_uses) >= 1, "No checkout step found"
    assert all("@v4" in u for u in checkout_uses), (
        f"checkout step is not pinned to @v4: {checkout_uses}"
    )


# ---------------------------------------------------------------------------
# grep fault-tolerance: || true in all 5 check steps
# ---------------------------------------------------------------------------

def test_grep_or_true_for_config_py(release_yml_text):
    """`|| true` fallback must follow the grep for config.py so a missing file doesn't abort early."""
    # Find the config.py block and ensure || true follows the grep
    match = re.search(r"src/launcher/config\.py.*?\|\|\s*true", release_yml_text, re.DOTALL)
    assert match is not None, (
        "config.py grep is missing '|| true' fallback — file absence would abort the job silently"
    )


def test_grep_or_true_for_pyproject_toml(release_yml_text):
    """`|| true` fallback must follow the grep for pyproject.toml."""
    match = re.search(r"pyproject\.toml.*?\|\|\s*true", release_yml_text, re.DOTALL)
    assert match is not None, "pyproject.toml grep is missing '|| true' fallback"


def test_grep_or_true_for_setup_iss(release_yml_text):
    """`|| true` fallback must follow the grep for setup.iss."""
    match = re.search(r"setup\.iss.*?\|\|\s*true", release_yml_text, re.DOTALL)
    assert match is not None, "setup.iss grep is missing '|| true' fallback"


def test_grep_or_true_for_build_dmg(release_yml_text):
    """`|| true` fallback must follow the grep for build_dmg.sh."""
    match = re.search(r"build_dmg\.sh.*?\|\|\s*true", release_yml_text, re.DOTALL)
    assert match is not None, "build_dmg.sh grep is missing '|| true' fallback"


def test_grep_or_true_for_build_appimage(release_yml_text):
    """`|| true` fallback must follow the grep for build_appimage.sh."""
    match = re.search(r"build_appimage\.sh.*?\|\|\s*true", release_yml_text, re.DOTALL)
    assert match is not None, "build_appimage.sh grep is missing '|| true' fallback"


# ---------------------------------------------------------------------------
# GITHUB_OUTPUT correct usage
# ---------------------------------------------------------------------------

def test_github_output_used_for_version(release_yml_text):
    """`>> "$GITHUB_OUTPUT"` must be used to export the version (not deprecated set-output)."""
    assert '>> "$GITHUB_OUTPUT"' in release_yml_text, (
        "Workflow uses deprecated ::set-output or missing GITHUB_OUTPUT — use >> \"$GITHUB_OUTPUT\""
    )


def test_no_deprecated_set_output(release_yml_text):
    """The deprecated `::set-output` command must NOT be used."""
    assert "::set-output" not in release_yml_text, (
        "Deprecated ::set-output command found — replace with >> \"$GITHUB_OUTPUT\""
    )


# ---------------------------------------------------------------------------
# Step ID / output reference consistency
# ---------------------------------------------------------------------------

def test_extract_version_step_has_id(release_yml_data):
    """The version extraction step must have id: extract_version."""
    job = release_yml_data["jobs"]["validate-version"]
    ids = [s.get("id") for s in job["steps"]]
    assert "extract_version" in ids, (
        "No step with id: extract_version found in validate-version job"
    )


def test_steps_reference_correct_step_output(release_yml_text):
    """All version check steps must reference steps.extract_version.outputs.version."""
    assert "steps.extract_version.outputs.version" in release_yml_text, (
        "Version check steps do not reference steps.extract_version.outputs.version"
    )


# ---------------------------------------------------------------------------
# v-prefix strip edge case
# ---------------------------------------------------------------------------

def test_tag_strip_v_prefix_logic(release_yml_text):
    """${TAG#v} strips only a leading 'v' — verify the exact shell syntax is used."""
    # This is the correct bash parameter expansion to strip a single leading 'v'
    assert "${TAG#v}" in release_yml_text, (
        "Tag stripping logic '${TAG#v}' not found — a tag like 'v3.0.1' would not be stripped correctly"
    )


def test_no_sed_or_cut_for_v_strip(release_yml_text):
    """Version extraction must use bash parameter expansion, not fragile sed/cut."""
    # sed/cut would be fragile for this use case; bash parameter expansion is correct
    # This is a soft check: sed could work, but look for common mistakes
    problematic = re.search(r"\bsed\b.*TAG\b|\bcut\b.*TAG\b", release_yml_text)
    assert problematic is None, (
        "sed or cut used on TAG for v-prefix stripping — use ${TAG#v} instead"
    )


# ---------------------------------------------------------------------------
# Each of the 5 version check steps independently exits 1 on mismatch
# ---------------------------------------------------------------------------

def test_exit_1_count_matches_5_file_checks(release_yml_text):
    """There must be at least 5 occurrences of 'exit 1' in validate-version (one per file check)."""
    # Find the validate-version job section (before windows-build)
    pos_validate = release_yml_text.find("validate-version:")
    pos_windows = release_yml_text.find("windows-build:")
    validate_section = release_yml_text[pos_validate:pos_windows]
    exit_count = validate_section.count("exit 1")
    assert exit_count >= 5, (
        f"Only {exit_count} 'exit 1' found in validate-version job — expected ≥5 (one per file check)"
    )


# ---------------------------------------------------------------------------
# release job should NOT directly depend on validate-version
# (it depends on build jobs, which depend on validate-version — transitive)
# ---------------------------------------------------------------------------

def test_release_job_does_not_directly_need_validate_version(release_yml_data):
    """release job depends on build jobs (transitive dep) — direct dep on validate-version would be redundant."""
    job = release_yml_data["jobs"]["release"]
    needs = job.get("needs", [])
    if isinstance(needs, str):
        needs = [needs]
    # This is a design check: if validate-version were in needs, it'd be redundant
    # The workflow design should stay clean
    assert "validate-version" not in needs, (
        "release job should NOT directly depend on validate-version (it's transitive via build jobs)"
    )


# ---------------------------------------------------------------------------
# validate-version job has no `needs` (it's the first gate)
# ---------------------------------------------------------------------------

def test_validate_version_has_no_needs(release_yml_data):
    """validate-version must not depend on any other job — it is the entry gate."""
    job = release_yml_data["jobs"]["validate-version"]
    needs = job.get("needs")
    assert needs is None or needs == [], (
        f"validate-version depends on: {needs} — it must run as the first job with no prerequisites"
    )


# ---------------------------------------------------------------------------
# All referenced file paths actually exist in the repository
# ---------------------------------------------------------------------------

def test_config_py_file_exists():
    """src/launcher/config.py must actually exist at the path the CI job checks."""
    path = os.path.join(REPO_ROOT, "src", "launcher", "config.py")
    assert os.path.isfile(path), f"File not found: {path}"


def test_pyproject_toml_file_exists():
    """pyproject.toml must actually exist at the repository root."""
    path = os.path.join(REPO_ROOT, "pyproject.toml")
    assert os.path.isfile(path), f"File not found: {path}"


def test_setup_iss_file_exists():
    """src/installer/windows/setup.iss must actually exist at the path the CI job checks."""
    path = os.path.join(REPO_ROOT, "src", "installer", "windows", "setup.iss")
    assert os.path.isfile(path), f"File not found: {path}"


def test_build_dmg_sh_file_exists():
    """src/installer/macos/build_dmg.sh must actually exist at the path the CI job checks."""
    path = os.path.join(REPO_ROOT, "src", "installer", "macos", "build_dmg.sh")
    assert os.path.isfile(path), f"File not found: {path}"


def test_build_appimage_sh_file_exists():
    """src/installer/linux/build_appimage.sh must actually exist at the path the CI job checks."""
    path = os.path.join(REPO_ROOT, "src", "installer", "linux", "build_appimage.sh")
    assert os.path.isfile(path), f"File not found: {path}"


# ---------------------------------------------------------------------------
# grep pattern correctness — patterns must match actual file content
# ---------------------------------------------------------------------------

def test_config_py_grep_pattern_matches_actual_file():
    """The grep -oP pattern for config.py must actually match the VERSION line in the file."""
    path = os.path.join(REPO_ROOT, "src", "launcher", "config.py")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Replicate the grep pattern logic in Python
    match = re.search(r'VERSION\s*(?::\s*str\s*)?=\s*"([^"]+)"', content)
    assert match is not None, (
        "grep pattern for config.py VERSION does not match actual file content — grep would return empty"
    )
    version = match.group(1)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Matched version '{version}' is not semver"


def test_pyproject_toml_grep_pattern_matches_actual_file():
    """The grep -oP pattern for pyproject.toml must match the version line."""
    path = os.path.join(REPO_ROOT, "pyproject.toml")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None, (
        "grep pattern for pyproject.toml version does not match actual file content"
    )
    version = match.group(1)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Matched version '{version}' is not semver"


def test_setup_iss_grep_pattern_matches_actual_file():
    """The grep -oP pattern for setup.iss must match the MyAppVersion line."""
    path = os.path.join(REPO_ROOT, "src", "installer", "windows", "setup.iss")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'#define MyAppVersion "([^"]+)"', content)
    assert match is not None, (
        "grep pattern for setup.iss #define MyAppVersion does not match actual file content"
    )
    version = match.group(1)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Matched version '{version}' is not semver"


def test_build_dmg_grep_pattern_matches_actual_file():
    """The grep -oP pattern for build_dmg.sh must match the APP_VERSION= line."""
    path = os.path.join(REPO_ROOT, "src", "installer", "macos", "build_dmg.sh")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'APP_VERSION="([^"]+)"', content)
    assert match is not None, (
        "grep pattern for build_dmg.sh APP_VERSION does not match actual file content"
    )
    version = match.group(1)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Matched version '{version}' is not semver"


def test_build_appimage_grep_pattern_matches_actual_file():
    """The grep -oP pattern for build_appimage.sh must match the APP_VERSION= line."""
    path = os.path.join(REPO_ROOT, "src", "installer", "linux", "build_appimage.sh")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'APP_VERSION="([^"]+)"', content)
    assert match is not None, (
        "grep pattern for build_appimage.sh APP_VERSION does not match actual file content"
    )
    version = match.group(1)
    assert re.match(r"^\d+\.\d+\.\d+$", version), f"Matched version '{version}' is not semver"


# ---------------------------------------------------------------------------
# Version consistency: all 5 files must agree on the current version
# ---------------------------------------------------------------------------

def test_all_5_files_version_consistent():
    """All 5 version files must report the same version string (pre-condition for CI to pass)."""
    files = {
        "config.py": (
            os.path.join(REPO_ROOT, "src", "launcher", "config.py"),
            r'VERSION\s*(?::\s*str\s*)?=\s*"([^"]+)"',
        ),
        "pyproject.toml": (
            os.path.join(REPO_ROOT, "pyproject.toml"),
            r'^version\s*=\s*"([^"]+)"',
        ),
        "setup.iss": (
            os.path.join(REPO_ROOT, "src", "installer", "windows", "setup.iss"),
            r'#define MyAppVersion "([^"]+)"',
        ),
        "build_dmg.sh": (
            os.path.join(REPO_ROOT, "src", "installer", "macos", "build_dmg.sh"),
            r'APP_VERSION="([^"]+)"',
        ),
        "build_appimage.sh": (
            os.path.join(REPO_ROOT, "src", "installer", "linux", "build_appimage.sh"),
            r'APP_VERSION="([^"]+)"',
        ),
    }
    versions = {}
    for name, (path, pattern) in files.items():
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(pattern, content, re.MULTILINE)
        assert m is not None, f"Version pattern not found in {name}"
        versions[name] = m.group(1)

    unique = set(versions.values())
    assert len(unique) == 1, (
        f"Version mismatch across version files — CI would fail if a tag were pushed now:\n"
        + "\n".join(f"  {k}: {v}" for k, v in versions.items())
    )


# ---------------------------------------------------------------------------
# No secrets or hardcoded credentials in validate-version job
# ---------------------------------------------------------------------------

def test_no_secrets_in_validate_version_job(release_yml_data):
    """The validate-version job must not reference any secrets."""
    job = release_yml_data["jobs"]["validate-version"]
    job_str = str(job)
    assert "secrets." not in job_str, (
        "validate-version job references secrets — this job should need no secrets"
    )


# ---------------------------------------------------------------------------
# Security: workflow_dispatch input has description (usability / documentation)
# ---------------------------------------------------------------------------

def test_workflow_dispatch_tag_input_has_description(release_yml_data):
    """The workflow_dispatch tag input must have a description for operator clarity."""
    on_config = release_yml_data.get("on") or release_yml_data.get(True)
    wd = on_config.get("workflow_dispatch", {})
    inputs = wd.get("inputs", {})
    tag_input = inputs.get("tag", {})
    assert "description" in tag_input, (
        "workflow_dispatch 'tag' input has no description — operators won't know what to enter"
    )
