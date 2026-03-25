#!/usr/bin/env python3
"""Reset the hook denial counter state."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / ".hook_state.json"


def _is_session_entry(value: object) -> bool:
    """Return True if *value* looks like a session counter dict."""
    return isinstance(value, dict) and "deny_count" in value


def reset_counters(
    session_id: "str | None" = None,
    state_path: "Path | None" = None,
) -> "tuple[int, str]":
    """Reset counters.  Returns `(num_reset, message)` tuple."""
    path = Path(state_path) if state_path is not None else STATE_FILE

    # --- missing file ---
    if not path.is_file():
        return 0, "No state file found. Nothing to reset."

    # --- load ---
    try:
        raw = path.read_text(encoding="utf-8")
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise ValueError("root is not a JSON object")
    except (json.JSONDecodeError, ValueError):
        # corrupt file: warn, write fresh empty state
        _atomic_write(path, {})
        return 0, "Warning: corrupt state file. Created fresh empty state."

    # --- reset logic ---
    if session_id is not None:
        # specific session
        if session_id in state and _is_session_entry(state[session_id]):
            del state[session_id]
            _atomic_write(path, state)
            return 1, f"Session {session_id} reset."
        return 0, f"Session {session_id} not found."

    # all sessions
    session_keys = [k for k, v in state.items() if _is_session_entry(v)]
    count = len(session_keys)
    for k in session_keys:
        del state[k]
    _atomic_write(path, state)
    return count, f"Reset {count} session(s)."


def _atomic_write(path: Path, data: dict) -> None:
    """Write *data* as JSON via temp-file + os.replace."""
    dir_path = str(path.parent)
    fd, tmp_path = tempfile.mkstemp(
        dir=dir_path, suffix=".tmp", prefix=".hook_state_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Reset hook denial counters.")
    parser.add_argument(
        "--session-id",
        default=None,
        help="Reset only this session (omit to reset all).",
    )
    args = parser.parse_args()

    try:
        _count, message = reset_counters(session_id=args.session_id)
        print(message)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
