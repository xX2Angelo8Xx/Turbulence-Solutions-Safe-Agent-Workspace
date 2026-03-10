# Coding Standards

Rules for code quality, scope discipline, and implementation practices.

---

## Scope Discipline

- **Only implement what the assigned workpackage specifies.** No bonus features, no drive-by refactors.
- Do not add comments, docstrings, or type annotations to code you did not change.
- Do not refactor or "improve" adjacent code unless it is broken and blocking your workpackage.

## Code Quality

- Write clean, well-commented code. Comments explain **why**, not **what**.
- Use meaningful variable and function names.
- Follow the conventions of the language being used.
- Prefer readability over cleverness.
- No unused imports or dead code.

## Python Conventions

- Follow PEP 8 for formatting and style.
- Use type hints for all new function signatures.
- Use `pytest` as the test framework.
- **Virtual environments are mandatory.** Always use the workspace `.venv` for all development, testing, and tooling. Run commands via `.venv\Scripts\python` (Windows) or `.venv/bin/python` (macOS/Linux).
- **No global Python installs.** Never install packages globally (`pip install <pkg>` at system level). Always use `.venv\Scripts\pip install`. If a global install is unavoidable, stop and ask the user for explicit approval first.

## Security in Code

- All security-critical code requires a test that validates the protection **and** a test that attempts the bypass.
- Cross-platform compatibility (Windows, macOS, Linux) is mandatory for all safety features.
- Prefer failing closed (deny) over failing open (allow) in all security decisions.
- Error handling must be present and meaningful at system boundaries.

## Dependencies

- All dependencies must be declared in `requirements.txt` or `pyproject.toml`.
- Pin major versions for stability.
- Do not introduce new dependencies without justification in the workpackage comments.

## Code Permanence

- **Test scripts are permanent.** The final test file for each workpackage (`tests/<WP-ID>/`) must never be deleted after the WP is `Done`. It serves as the regression baseline for all future versions.
- **Minimize one-time code.** Avoid creating throwaway scripts that are discarded after use. If temporary scaffolding is genuinely needed, label it clearly and remove it before WP handoff.
- The committed test script must be clean, self-contained, and runnable without modification.
