"""Golden-file snapshot tests for security_gate.py decisions.

Each .json file in this directory defines an input, workspace root, and the
expected allow/deny decision from security_gate.decide().  If a gate decision
changes between versions, these tests catch it immediately.

SAF-078: The --update-snapshots flag rewrites snapshot files with the actual
decision when a change is intentional.  Every update must be documented in
dev-log.md under '## Behavior Changes'.  The snapshot IS the documentation.
"""
from __future__ import annotations

import json
import sys
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Make security_gate importable from its non-standard location
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(
    Path(__file__).resolve().parents[3]
    / "templates" / "agent-workbench" / ".github" / "hooks" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import security_gate as sg  # noqa: E402

# ---------------------------------------------------------------------------
# Snapshot loader
# ---------------------------------------------------------------------------
SNAPSHOTS_DIR = Path(__file__).parent


def _load_snapshots():
    """Load all *.json snapshot files from this directory."""
    snapshots = []
    for f in sorted(SNAPSHOTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            snapshots.append(pytest.param(data, id=f.stem))
        except (json.JSONDecodeError, KeyError):
            continue
    return snapshots


_SNAPSHOTS = _load_snapshots()


# ---------------------------------------------------------------------------
# Tests — only collected when snapshot files exist
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("snapshot", _SNAPSHOTS)
def test_security_gate_snapshot(snapshot, update_snapshots):
    """Verify security_gate.decide() matches the golden-file expectation.

    When --update-snapshots is supplied, the snapshot file is rewritten with
    the actual decision instead of failing.  Use only for intentional
    security-decision changes; document each update in dev-log.md under
    '## Behavior Changes'.
    """
    assert "description" in snapshot, "Snapshot missing 'description' field"
    assert "input" in snapshot, "Snapshot missing 'input' field"
    assert "expected_decision" in snapshot, "Snapshot missing 'expected_decision' field"
    assert snapshot["expected_decision"] in ("allow", "deny"), (
        f"Invalid expected_decision: {snapshot['expected_decision']}"
    )

    ws_root = snapshot.get("ws_root", "/workspace")
    actual = sg.decide(snapshot["input"], ws_root)

    if actual != snapshot["expected_decision"]:
        if update_snapshots:
            # Rewrite the snapshot file so the next clean run passes.
            scenario_id = snapshot.get("description", "unknown scenario")
            snapshot_file = SNAPSHOTS_DIR / f"{scenario_id}.json"
            # Locate by matching description across all JSON files.
            for f in SNAPSHOTS_DIR.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                if data.get("description") == snapshot.get("description") and \
                        data.get("input") == snapshot.get("input"):
                    data["expected_decision"] = actual
                    f.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    return  # snapshot updated — test passes
            # If we couldn't locate the file, fall through to the normal failure.

        raise AssertionError(
            f"Security decision changed from '{snapshot['expected_decision']}' to "
            f"'{actual}' for scenario '{snapshot['description']}'.\n"
            f"  input:   {snapshot['input']}\n"
            f"  ws_root: {ws_root}\n"
            f"If intentional, update the snapshot with --update-snapshots and "
            f"document in dev-log.md under '## Behavior Changes'."
        )
