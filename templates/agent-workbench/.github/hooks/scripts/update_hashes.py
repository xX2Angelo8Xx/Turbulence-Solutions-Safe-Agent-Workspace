"""update_hashes.py — SAF-011 Hash Update Tool

Recomputes the SHA256 hashes of security_gate.py and settings.json and
re-embeds them into security_gate.py.

Run from any directory:
    python .github/hooks/scripts/update_hashes.py

Or from the scripts directory itself:
    python update_hashes.py
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _resolve_paths() -> tuple[Path, Path]:
    """Return (gate_path, settings_path) relative to this script's location."""
    scripts_dir = Path(__file__).resolve().parent
    # Layout: scripts/ -> hooks/ -> .github/ -> workspace_root/
    workspace_root = scripts_dir.parent.parent.parent
    gate_path = scripts_dir / "security_gate.py"
    settings_path = workspace_root / ".vscode" / "settings.json"
    return gate_path, settings_path


# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    """Return the lowercase SHA256 hex digest of a file's raw bytes, normalized."""
    content = path.read_bytes()
    # Normalize CRLF -> LF so the hash is platform-independent.
    content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def _compute_canonical_gate_hash(content_bytes: bytes) -> str:
    """Compute the canonical gate hash from file content bytes.

    Canonical form: the value of _KNOWN_GOOD_GATE_HASH is replaced with 64
    zeros before hashing.  This mirrors the algorithm used by
    security_gate._compute_gate_canonical_hash().
    """
    # Normalize CRLF -> LF so the hash is platform-independent.
    content_bytes = content_bytes.replace(b"\r\n", b"\n")
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b"0" * 64,
        content_bytes,
    )
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# Content patching
# ---------------------------------------------------------------------------

_SETTINGS_HASH_RE = re.compile(
    rb'(?<=_KNOWN_GOOD_SETTINGS_HASH: str = ")[0-9a-fA-F]{64}'
)
_GATE_HASH_RE = re.compile(
    rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}'
)


def _patch_hash(content: bytes, pattern: re.Pattern[bytes], new_hash: str) -> bytes:
    """Replace the first match of pattern with new_hash (encoded as ASCII).

    Raises ValueError if the pattern is not found (expected constant missing).
    """
    new_hash_bytes = new_hash.encode("ascii")
    result, n = pattern.subn(new_hash_bytes, content, count=1)
    if n == 0:
        raise ValueError(
            f"Hash constant pattern not found in security_gate.py — "
            f"pattern: {pattern.pattern!r}"
        )
    return result


# ---------------------------------------------------------------------------
# Main update routine
# ---------------------------------------------------------------------------

def update_hashes() -> None:
    """Recompute and re-embed both hash constants into security_gate.py."""
    gate_path, settings_path = _resolve_paths()

    # Validate both files exist before touching anything.
    if not settings_path.is_file():
        print(
            f"ERROR: settings.json not found at {settings_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not gate_path.is_file():
        print(
            f"ERROR: security_gate.py not found at {gate_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 1: Compute new settings hash from the file on disk.
    new_settings_hash = _sha256_file(settings_path)

    # Step 2: Read security_gate.py.
    content = gate_path.read_bytes()

    # Step 3: Patch the settings hash constant (in memory).
    content = _patch_hash(content, _SETTINGS_HASH_RE, new_settings_hash)

    # Step 4: Compute the canonical gate hash from the settings-updated content.
    # (Canonical form: _KNOWN_GOOD_GATE_HASH value zeroed before hashing.)
    new_gate_hash = _compute_canonical_gate_hash(content)

    # Step 5: Patch the gate hash constant.
    content = _patch_hash(content, _GATE_HASH_RE, new_gate_hash)

    # Step 6: Write the updated content back to disk.
    gate_path.write_bytes(content)

    print(f"Updated _KNOWN_GOOD_SETTINGS_HASH → {new_settings_hash}")
    print(f"Updated _KNOWN_GOOD_GATE_HASH      → {new_gate_hash}")
    print("security_gate.py updated successfully.")


if __name__ == "__main__":
    update_hashes()
