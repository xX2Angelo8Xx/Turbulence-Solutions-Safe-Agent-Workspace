"""
FIX-087: Tester edge-case tests for the pytest install step in macos-source-test.yml.

These supplement the Developer's tests and cover:
- Step name quality
- Distinguishability from the pytest run step (INS-028 regression)
- Single-responsibility of the install step
- No inadvertent duplication
- Ordering precision
"""
import os
import yaml

WORKFLOW_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", ".github", "workflows", "macos-source-test.yml"
))

VENV_PIP = "~/.local/share/TurbulenceSolutions/venv/bin/pip"


def _load_workflow():
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_steps():
    wf = _load_workflow()
    steps = []
    for job in wf.get("jobs", {}).values():
        steps.extend(job.get("steps", []))
    return steps


def test_install_step_has_descriptive_name():
    """The 'pip install pytest' step must have a non-empty, descriptive name."""
    steps = _get_steps()
    for step in steps:
        run = step.get("run", "")
        if "pip install pytest" in run:
            name = step.get("name", "")
            assert name, "The pip install pytest step must have a 'name' field"
            name_lower = name.lower()
            assert any(kw in name_lower for kw in ("install", "test", "dep", "pytest")), (
                f"Step name '{name}' does not describe what it does — "
                "should contain 'install', 'test', 'dep', or 'pytest'"
            )
            return
    raise AssertionError("No 'pip install pytest' step found in workflow")


def test_install_step_is_pip_not_pytest_invocation():
    """
    The step installing pytest must use 'pip install', NOT 'python -m pytest'.
    This ensures the step is purely an install step, not accidentally a test run.
    """
    steps = _get_steps()
    for step in steps:
        run = step.get("run", "")
        if "pip install pytest" in run:
            assert "python -m pytest" not in run, (
                "The install step must NOT invoke pytest — it should only install it"
            )
            return
    raise AssertionError("No 'pip install pytest' step found in workflow")


def test_pip_install_step_does_not_contain_pytest_run_flags():
    """
    REGRESSION GUARD (INS-028 compatibility): Any step whose 'run' field contains
    'pytest' but does NOT use 'python -m pytest' must not contain pytest run flags
    (-x, --tb=short). This catches the exact failure mode where INS-028 tests
    check 'if pytest in run: assert -x in run'.

    The pip install step must NOT contain -x or --tb=short.
    """
    steps = _get_steps()
    for step in steps:
        run = step.get("run", "")
        # Identify non-invocation steps: contain 'pytest' but aren't running it
        if "pytest" in run and "python -m pytest" not in run:
            assert "-x" not in run, (
                f"Step '{step.get('name', '?')}' run='{run}' has 'pytest' in its "
                "command but is not a pytest invocation — it must NOT contain the "
                "pytest flag '-x'. This breaks INS-028 tests that check all "
                "steps containing 'pytest'."
            )
            assert "--tb=" not in run, (
                f"Step '{step.get('name', '?')}' run='{run}' has 'pytest' in its "
                "command but is not a pytest invocation — it must NOT contain the "
                "pytest flag '--tb='. This breaks INS-028 tests that check all "
                "steps containing 'pytest'."
            )


def test_pip_install_pytest_appears_exactly_once():
    """The 'pip install pytest' command must appear exactly once — no duplication."""
    steps = _get_steps()
    install_steps = [s for s in steps if "pip install pytest" in s.get("run", "")]
    assert len(install_steps) == 1, (
        f"Expected exactly 1 'pip install pytest' step, found {len(install_steps)}"
    )


def test_install_step_installs_only_pytest():
    """
    The install step should only install 'pytest', not a mixture of packages that
    could accidentally add production dependencies to the venv.
    """
    steps = _get_steps()
    for step in steps:
        run = step.get("run", "").strip()
        if "pip install pytest" in run:
            # Should be a simple: <pip> install pytest [options]
            # Must not install unrelated packages
            parts = run.split()
            try:
                install_idx = parts.index("install")
            except ValueError:
                continue
            packages = [p for p in parts[install_idx + 1:] if not p.startswith("-")]
            assert packages == ["pytest"], (
                f"Install step should only install 'pytest', found: {packages!r}"
            )
            return
    raise AssertionError("No 'pip install pytest' step found in workflow")


def test_install_step_immediately_before_test_step():
    """
    The 'pip install pytest' step must be immediately before the
    'Run test suite with venv Python' step — no other steps between them.
    """
    steps = _get_steps()
    install_pos = None
    test_pos = None
    for i, step in enumerate(steps):
        run = step.get("run", "")
        if "pip install pytest" in run:
            install_pos = i
        if "python -m pytest tests/" in run:
            test_pos = i
    assert install_pos is not None, "No 'pip install pytest' step found"
    assert test_pos is not None, "No 'python -m pytest tests/' step found"
    assert test_pos == install_pos + 1, (
        f"'pip install pytest' is at step {install_pos + 1} but "
        f"'python -m pytest' is at step {test_pos + 1}. "
        "They must be adjacent (no steps between them)."
    )


def test_install_step_uses_venv_pip_not_system_pip():
    """
    The install step must use the venv pip, NOT bare 'pip install pytest'.
    Using the system pip would install into the wrong environment.
    """
    steps = _get_steps()
    for step in steps:
        run = step.get("run", "").strip()
        if "pip install pytest" in run:
            assert run.startswith(VENV_PIP), (
                f"Install step must use venv pip '{VENV_PIP}', not: {run!r}"
            )
            return
    raise AssertionError("No 'pip install pytest' step found in workflow")
