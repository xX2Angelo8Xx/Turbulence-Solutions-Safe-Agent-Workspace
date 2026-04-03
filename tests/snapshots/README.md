# Golden-File Snapshot Tests

This directory contains golden-file (snapshot) test suites that detect unintended changes
to safety-critical decision logic.

---

## What Are Golden-File Snapshots?

A golden-file snapshot is a saved record of what the system *should* output for a given
input. Each snapshot file captures one scenario: the input, any relevant context, and the
expected output. The test framework replays that scenario against the live code and fails
if the output no longer matches.

Snapshots exist because safety-critical components (e.g. `security_gate.py`,
`zone_classifier.py`) must never silently change their decisions. A passing snapshot suite
guarantees that every previously-verified allow/deny decision still holds.

---

## Directory Structure

```
tests/snapshots/
├── README.md                   ← this file
└── security_gate/              ← one sub-directory per component under snapshot
    ├── conftest.py             ← pytest fixtures for this component
    ├── test_snapshots.py       ← auto-discovering parametrized tests
    ├── allow_*.json            ← allow-decision scenarios
    └── deny_*.json             ← deny-decision scenarios
```

Each component that needs snapshot coverage gets its own sub-directory following this
pattern. The sub-directory contains its own `test_snapshots.py` and `conftest.py` so it
can be run in isolation.

---

## Snapshot File Format

Each `.json` file in a sub-directory defines exactly one scenario:

```json
{
  "description": "Human-readable explanation of what this scenario tests",
  "ws_root": "/workspace",
  "input": {
    "tool_name": "read_file",
    "filePath": "/workspace/project/main.py"
  },
  "expected_decision": "allow"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | Plain-English explanation of the scenario. |
| `input` | Yes | The tool-call object passed to the decision function. |
| `expected_decision` | Yes | Either `"allow"` or `"deny"`. |
| `ws_root` | No | Workspace root path. Defaults to `"/workspace"` when absent. |
| `expected_reason` | No | Substring that must appear in the reason string (if tested). |

---

## How to Run Snapshot Tests

Run the entire snapshot suite:

```powershell
.venv\Scripts\python.exe -m pytest tests/snapshots/ -v
```

Run only the security_gate snapshots:

```powershell
.venv\Scripts\python.exe -m pytest tests/snapshots/security_gate/ -v
```

Each test is named after the snapshot file, making failures easy to identify:

```
PASSED  tests/snapshots/security_gate/test_snapshots.py::test_security_gate_snapshot[allow_always_allow_tool]
FAILED  tests/snapshots/security_gate/test_snapshots.py::test_security_gate_snapshot[deny_unknown_tool]
```

---

## How to Update Snapshots

> **The snapshot IS the documentation.**
> When you update a snapshot you are declaring: "this new decision is now the
> intended, authorised behaviour for this scenario."  Every update therefore
> requires the same level of justification as a code change.

**Snapshots must only be updated when a decision change is intentional** — i.e.
it is required by a workpackage, justified by the WP's acceptance criteria, and
approved by the Tester. Unilateral snapshot updates are not permitted.

### Prerequisites

Before updating any snapshot, you MUST be able to answer:

1. Why did the security decision change?
2. Which workpackage authorises the change?
3. What is the new intended behaviour?

If you cannot answer all three, **do not update the snapshot**.  Investigate the
root cause of the decision change instead.

### Procedure — using `--update-snapshots`

1. Run the snapshot suite to see which tests fail and what the new decisions are:

   ```powershell
   .venv\Scripts\python.exe -m pytest tests/snapshots/ -v
   ```

2. If the failing tests correspond to **intentional** changes authorised by
   your workpackage, re-run with the flag to update the snapshot files
   in-place:

   ```powershell
   .venv\Scripts\python.exe -m pytest tests/snapshots/ -v --update-snapshots
   ```

   Each snapshot whose `expected_decision` no longer matches the actual result
   will have its JSON file rewritten automatically.  The test run will pass.

3. Verify the rewritten files look correct:

   ```powershell
   git diff tests/snapshots/
   ```

4. **Document every updated snapshot in your WP's `dev-log.md`** under a
   required `## Behavior Changes` section (see the dev-log template in
   `docs/work-rules/agent-workflow.md`).  Include:

   - Snapshot file name
   - Old decision → new decision
   - Reason for the change and the WP/ADR that authorises it

5. Re-run **without** the flag to confirm everything is clean:

   ```powershell
   .venv\Scripts\python.exe -m pytest tests/snapshots/ -v
   ```

6. Commit the updated snapshot files together with the code change that caused
   them and the updated `dev-log.md`.

### When NOT to use `--update-snapshots`

| Situation | Correct Action |
|-----------|----------------|
| Snapshot fails **without** any intentional code change | **Bug** — investigate, do not update snapshots |
| Snapshot fails on one platform only | Platform inconsistency — fix the code |
| All snapshots fail simultaneously | Import error — fix the import, not the snapshots |
| You are unsure if the change was intentional | Stop — ask, do not update snapshots |

---

## When Is a Failing Snapshot a Real Regression?

| Situation | What It Means | Action |
|-----------|---------------|--------|
| A snapshot fails **without** any intentional code change | The gate decision changed unexpectedly — **this is a regression**. | Stop. Investigate the root cause. Do not update the snapshot. File a bug. |
| A snapshot fails **after** a SAF workpackage change | The test correctly detected a policy change. | Verify the change is intentional. Update the snapshot per the procedure above. |
| A snapshot fails **only on one platform** | Platform-specific quoting, path separator, or encoding issue. | Investigate and fix the platform inconsistency in the code. |
| All snapshots fail simultaneously | `security_gate.py` import error or missing dependency. | Fix the import error first; the snapshots themselves are not the problem. |

**Rule of thumb:** if you did not intend to change a security decision, a failing snapshot
is a bug — not a test to silence.

---

## Adding New Snapshots

To add a new scenario to an existing suite:

1. Create a new `.json` file in the appropriate sub-directory.
2. Name it descriptively: `allow_<scenario>.json` or `deny_<scenario>.json`.
3. Fill in all required fields (see format above).
4. Run the suite to confirm the new test passes.
5. Commit the file with your workpackage.

To add snapshot coverage for a new component:

1. Create a new sub-directory under `tests/snapshots/`.
2. Copy `conftest.py` from `security_gate/` and adapt the import paths.
3. Copy `test_snapshots.py` from `security_gate/` and update `SNAPSHOTS_DIR` if needed.
4. Add at least one `allow_*.json` and one `deny_*.json` as smoke tests.
5. Document the new component in this README.
