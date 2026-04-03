# Testing Protocol

Comprehensive testing standards for all workpackages. This protocol defines the **minimum** testing requirements — agents and humans are expected to exceed it where applicable.

---

## Test Structure

- Tests live in `tests/<WP-ID>/`, one subfolder per workpackage.
  - Example: `tests/INS-001/test_ins001_structure.py`, `tests/SAF-001/test_saf001_security_gate.py`
- Naming convention: `test_<module>.py` or `test_<module>_<function>.py`.
- Use `pytest` as the test framework.
- Each test function should test **one specific behaviour**.
- Run tests using the workspace virtual environment: `.venv\Scripts\python -m pytest tests/`

## Test Categories

Every workpackage with code changes must include tests from the applicable categories:

| Category | When Required | Description |
|----------|---------------|-------------|
| **Unit** | All WPs with code changes | Test every public function/method in isolation |
| **Integration** | WPs involving cross-component interaction | Test how components work together |
| **Security** | All security-critical WPs (SAF-xxx) | One test validates the protection works, one test attempts to bypass it |
| **Regression** | Every bug fix | Test that reproduces the original bug and confirms the fix |
| **Cross-platform** | All safety features | Must pass on Windows, macOS, and Linux |

## Safe Testing of Launch-Capable Code

Rules that apply to all tests in this project. The launcher can open VS Code
instances, spawn subprocesses, show dialog boxes, and make HTTP calls — any of
these firing during an automated test run can destabilise or crash the system.

1. **All test runs must be headless.** No real GUI windows, dialog boxes, or
   external program launches may occur during testing. Tests are always run in a
   non-interactive terminal. Spawning a visible window or process is a test
   failure, not a passing side effect.

2. **`tests/conftest.py` autouse fixtures are the safety net.** Three defense
   layers are active for the duration of every test function — no opt-in required:

   **Layer 1 — function mock:** `launcher.core.vscode.open_in_vscode` and
   `launcher.gui.app.open_in_vscode` are both patched to return False. VS Code
   is never reached via the normal call path.

   **Layer 2 — detection mock:** `shutil.which("code")` returns None globally.
   Even if `open_in_vscode` is bypassed (e.g. via module reimport), `find_vscode()`
   cannot locate a VS Code binary and returns None without reaching `subprocess.Popen`.

   **Layer 3 — subprocess sentinel:** `subprocess.Popen` is wrapped with a
   sentinel that raises `RuntimeError` immediately if the first argument is a VS
   Code executable (`"code"`, a path ending in `\code`, or a string containing
   `"visual studio code"`). Non-VS-Code `Popen` calls pass through to the real
   implementation unmodified.

   Additional blocks always active:
   - GUI popups: `tkinter.messagebox` (showinfo, showerror, showwarning, askyesno)
     and `tkinter.filedialog` (askdirectory, askopenfilename)
   - Background HTTP calls: `launcher.gui.app.check_for_update` returns
     `(False, "0.0.0")` (only the app.py binding — NOT the source module, so
     INS-009 tests can call the real function with their own HTTP mocks)

2.5. **Emergency procedure — VS Code instance appeared during testing.** If a VS
   Code window is visible after or during a test run, the agent MUST:
   1. **Immediately terminate the test run** (Ctrl-C or kill the pytest process).
   2. **Kill all spawned VS Code processes:**
      - Windows: `taskkill /F /IM Code.exe`
      - Unix/macOS: `pkill -f "Visual Studio Code"`
   3. **Identify the root cause** — which guard failed and why.
   4. **File a critical FIX workpackage** before resuming any other work.
   Prevention via conftest fixtures is always preferred. This rule is the
   emergency fallback when prevention has already failed.

3. **Tests for launch behaviour must use explicit local mocks.** If a test needs
   to assert that `open_in_vscode()` calls `subprocess.Popen`, it must create its
   own `with patch("launcher.core.vscode.subprocess.Popen") as mock_popen:` block
   inside the test function. The conftest autouse fixture's mock is what the
   production code will hit unless overridden locally.

4. **Never call real functions that spawn processes.** Always mock at the system
   boundary. For subprocess calls use `patch("...subprocess.Popen")`. For network
   calls use `patch("...urllib.request.urlopen")`. For sockets use
   `patch("...socket.create_connection")`. Never allow a real I/O call to reach
   the OS during tests.

5. **Module reimport safety.** Several GUI test files loop over `sys.modules` and
   delete launcher module entries (`del sys.modules[k]`) so that the module is
   reimported with fresh mocks. This is safe: conftest autouse fixtures re-apply
   their patches before EACH test function invocation. The fixtures will wrap the
   reimported module transparently as long as the test function does not bypass
   them by calling the patched targets before the fixture context is entered.

6. **Standard pytest command:**
   ```
   .venv\Scripts\python -m pytest tests/ --tb=short -q
   ```
   - Never use `--timeout` (requires `pytest-timeout` which is not installed).
   - Never redirect pytest output to files in the repository root
     (use `docs/workpackages/<WP-ID>/` if a log file is needed).
   - Never run pytest with `-s` or `--capture=no` in shared CI environments —
     this disables output capture and can expose sensitive paths.

7. **Process responsibility.** If a test or agent accidentally spawns an external
   process (e.g. a VS Code window appears), the agent MUST detect and terminate
   it before proceeding with any other action. Prevention via conftest fixtures is
   always preferred over cleanup. If prevention failed, treat it as a critical bug
   and open a new FIX workpackage before continuing.

## Testing Workflow

### For Developers (during implementation)

1. Create `tests/<WP-ID>/` folder at the start of every workpackage.
2. Write tests **alongside** implementation, not after.
3. All new tests must pass before setting the WP to `Review`.
4. All **existing** tests must still pass (no regressions).
5. **Run tests via `scripts/run_tests.py`** (mandatory). This executes pytest and atomically logs the result. Direct `pytest` invocation is allowed for development iteration, but the final pre-handoff run **must** use this script:
   ```powershell
   .venv\Scripts\python scripts/run_tests.py --wp <WP-ID> --type Unit --env "Windows 11 + Python 3.13"
   ```
6. Document test approach and results in the WP's `dev-log.md`.
7. **Never use interactive constructs** — no `input()`, no commands that await stdin, no `[y/n]` prompts.

### For Testers (during review)

1. Read the Developer's `dev-log.md` in the WP folder.
2. Run the full test suite via `scripts/run_tests.py` (mandatory):
   ```powershell
   .venv\Scripts\python scripts/run_tests.py --wp <WP-ID> --type Regression --env "Windows 11 + Python 3.13" --full-suite
   ```
3. Add edge-case tests the Developer may have missed — place them in `tests/<WP-ID>/`.
4. **Think beyond the protocol**: consider attack vectors, boundary conditions, race conditions, concurrency issues, invalid inputs, and platform-specific quirks.
5. Run `scripts/run_tests.py` again for the WP-specific suite after adding edge-case tests.
6. Write findings in the WP's `test-report.md` (see format below).
7. **Never run commands that require user input** — all test execution must be non-interactive.

### Bug-Fix Workpackages (FIX-xxx)

Bug-fix workpackages follow the same testing requirements as feature WPs with these clarifications:

1. Every FIX WP **must** have a dedicated `tests/FIX-xxx/` directory with at least one regression test that reproduces the original bug and confirms the fix.
2. If the fix is validated primarily through an existing WP's test suite (e.g., FIX-004 fixes a bug in INS-006), the FIX WP's test directory should contain at minimum a test that specifically targets the fixed behavior.
3. All FIX WP tests **must** be logged as individual entries in `test-results.csv` with the FIX WP's ID in the `WP Reference` column.
4. The Tester **must** write a `test-report.md` for FIX WPs, just as for any other WP.

## Test Result CSV

All test runs are logged in `docs/test-results/test-results.csv`.

| Column | Description |
|--------|-------------|
| ID | Test identifier (`TST-NNN`) |
| Test Name | Descriptive name of the test |
| Test Type | `Unit` / `Integration` / `Security` / `Regression` / `Cross-platform` |
| WP Reference | Workpackage ID this test relates to |
| Status | `Pass` / `Fail` / `Blocked` / `Skipped` |
| Run Date | ISO 8601 date (YYYY-MM-DD) |
| Environment | OS + Python version (e.g., "Windows 11 + Python 3.11") |
| Result | Brief outcome description |
| Notes | Additional context, failure details |

## TST-ID Uniqueness

Test result IDs (`TST-NNN`) must be globally unique. To prevent duplicates:

- **Never manually add rows** to `docs/test-results/test-results.csv`. Manual edits risk ID collisions and corrupt the sequential numbering.
- **Always use `scripts/run_tests.py`** (primary) for test result logging — it runs pytest and atomically logs results. Use `scripts/add_test_result.py` only as a fallback when `run_tests.py` cannot be used (e.g. manual verification). Both scripts use atomic ID assignment via `locked_next_id_and_append()` to prevent duplicate IDs even under concurrent execution.
- If duplicate TST-IDs are suspected, run `scripts/dedup_test_ids.py --dry-run` to check for collisions without modifying the file. Remove the `--dry-run` flag to apply fixes.

## Test Report Format

The Tester writes `test-report.md` in the workpackage folder (`docs/workpackages/<WP-ID>/test-report.md`):

```markdown
# Test Report — <WP-ID>

**Tester:** <name or agent>
**Date:** YYYY-MM-DD
**Iteration:** <number>

## Summary
<Brief overall assessment>

## Tests Executed
| Test | Type | Result | Notes |
|------|------|--------|-------|
| ... | ... | ... | ... |

## Bugs Found
- BUG-NNN: <title> (logged in docs/bugs/bugs.csv)

## TODOs for Developer
- [ ] <specific actionable item>
- [ ] <specific actionable item>

## Verdict
<PASS — mark WP as Done> OR <FAIL — return to Developer with details above>
```

## Minimum Standards

- **No workpackage moves to `Done` without logged test results** in both the CSV and the WP's test-report.md.
- **Security WPs** require both protection tests and bypass-attempt tests — no exceptions.
- **Every bug fix** requires a regression test proving the bug is fixed and cannot recur.
- The testing protocol is the **floor**, not the ceiling. Always seek additional failure modes.
- **Pytest output policy:** pytest output must NEVER be redirected to a `.txt` file in the repository root. All output must go to `docs/workpackages/<WP-ID>/` or be discarded. Agents that create temporary output files MUST delete them before WP handoff.
- **test-report.md exit criterion:** The Tester Agent MUST create `test-report.md` in `docs/workpackages/<WP-ID>/` as a hard exit criterion before marking a WP as Done. A WP cannot be marked Done without a `test-report.md`.

---

## TST-ID Assignment — Mandatory Script Usage

Agents **MUST** use `scripts/run_tests.py` to execute tests and log results. This script runs pytest, parses the output, and atomically logs the result to `docs/test-results/test-results.csv` — closing the "self-reported results" loophole. The script is **proof that tests were actually executed**.

```powershell
# Run WP-specific tests and log result
.venv\Scripts\python scripts/run_tests.py --wp GUI-001 --type Unit --env "Windows 11 + Python 3.13"

# Run full regression suite and log result
.venv\Scripts\python scripts/run_tests.py --wp GUI-001 --type Regression --env "Windows 11 + Python 3.13" --full-suite
```

For cases where `run_tests.py` cannot be used (e.g., manual test verification), `scripts/add_test_result.py` may be used as a fallback:

```powershell
.venv\Scripts\python scripts/add_test_result.py `
    --name "test_foo_bar" `
    --type Unit `
    --wp GUI-001 `
    --status Pass `
    --env "Windows 11 + Python 3.13" `
    --result "5 passed / 0 failed" `
    --notes "Optional notes"
```

Rules:
1. **Never edit test-results.csv by hand.** Always use the script.
2. **Never reuse or reassign TST-IDs.** Once an ID is issued it is permanent, even if the row is later removed.
3. The script uses `locked_next_id_and_append()` which holds a file lock for the entire read-compute-write cycle — safe for parallel agent execution.
4. See `scripts/README.md` for full usage reference.

---

## Test Script Preservation

Test scripts are **permanent project artifacts**. They are not throw-away code.

- The final test script for each workpackage (`tests/<WP-ID>/test_<name>.py`) **must never be deleted** after the WP reaches `Done`.
- These scripts serve as regression tests for every future version of the project.
- Minimize one-time / disposable code. If temporary test scaffolding is needed during development, remove it before handoff — the committed test script must be clean and reusable.
- The results produced by the final test script are what is archived in `docs/test-results/test-results.csv`. Future releases run the same scripts; if output changes, it is a regression.
- When adding edge-case tests during Tester review, add them to the same `tests/<WP-ID>/` file — do not create separate throw-away scripts.

---

## Version Bump Tests — Single Source of Truth

Version bump workpackages create tests that verify version strings in source files.
These tests **must not** hardcode the current version as a constant. Instead, they must
use a dynamic inline expression that reads from `src/launcher/config.py`:

```python
import re as _re
EXPECTED_VERSION: str = _re.search(
    r'^VERSION\s*:\s*str\s*=\s*"([^"]+)"',
    (REPO_ROOT / "src" / "launcher" / "config.py").read_text(encoding="utf-8"),
    _re.MULTILINE,
).group(1)
del _re
```

Or import from the shared utility (requires `REPO_ROOT` to be on `sys.path`):

```python
from tests.shared.version_utils import CURRENT_VERSION as EXPECTED_VERSION
```

`tests/shared/version_utils.py` reads the version dynamically from `src/launcher/config.py`,
which is the single source of truth. This means:

- Future version bumps only need to update the 5 source files (config.py, pyproject.toml, setup.iss, build_dmg.sh, build_appimage.sh).
- No test files outside `tests/shared/` ever need updating for a version bump.
- **Allowed to remain hardcoded:** historical version strings such as `OLD_VERSION`, `PREVIOUS_VERSION`, `SKIP_ONE_VERSION`, `STALE_VERSIONS` — these are correct fixed values that should never change.
