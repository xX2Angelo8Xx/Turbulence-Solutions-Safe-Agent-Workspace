"""Temporary transformation script for FIX-046.

Replaces all 'Default-Project' path references in test files with
'templates/coding' equivalents.

Usage: python docs/workpackages/FIX-046/tmp_transform.py
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests"


def transform(content: str) -> str:
    original = content

    # ------------------------------------------------------------------
    # Pattern 1: Same-line Path chain with trailing /
    #   / "Default-Project" /  ->  / "templates" / "coding" /
    # ------------------------------------------------------------------
    content = re.sub(r'/ "Default-Project" /', '/ "templates" / "coding" /', content)

    # ------------------------------------------------------------------
    # Pattern 2: os.path.join argument (with trailing comma)
    #   "Default-Project",  ->  "templates", "coding",
    # Only replace when not preceded by a / (path chain) to avoid double-replace.
    # Since pattern 1 already cleared those, this should be safe.
    # ------------------------------------------------------------------
    content = re.sub(r'"Default-Project",', '"templates", "coding",', content)

    # ------------------------------------------------------------------
    # Pattern 3: Multi-line Path chain where "Default-Project" ends a line
    #   / "Default-Project"\n    / "foo"
    # -> / "templates"\n    / "coding"\n    / "foo"
    # Handles both CRLF and LF.
    # ------------------------------------------------------------------
    def expand_multiline_path(m):
        indent = m.group(1)
        return f'/ "templates"\n{indent}/ "coding"\n{indent}/'

    content = re.sub(
        r'/ "Default-Project"\r?\n(\s+)/',
        expand_multiline_path,
        content,
    )

    # ------------------------------------------------------------------
    # Pattern 4: "Default-Project" at end of line (end of chain)
    #   / "Default-Project"   ->  / "templates" / "coding"
    # Matches only when NOT followed by more path continuation on same line.
    # ------------------------------------------------------------------
    content = re.sub(
        r'/ "Default-Project"(\s*(?:#.*)?(?:\r?\n|$))',
        r'/ "templates" / "coding"\1',
        content,
    )

    # ------------------------------------------------------------------
    # Pattern 5: Label tuples and strings — cosmetic but important for
    # clarity. Replace ("Default-Project", ...) label in tuples.
    #   ("Default-Project",  ->  ("templates/coding",
    # ------------------------------------------------------------------
    content = re.sub(r'\("Default-Project",', '("templates/coding",', content)

    # ------------------------------------------------------------------
    # Pattern 6: docstring/comment references "Default-Project file"
    # Just replace the path-contextual references in strings.
    # The historical ones in comments (not functional) we can leave.
    # But for imports/vars that set DEFAULT_FILE path:
    #   REPO_ROOT / "Default-Project"  (already handled above)
    # ------------------------------------------------------------------

    return content


def main():
    updated = []
    skipped = []

    for py_file in sorted(TEST_ROOT.rglob("*.py")):
        content = py_file.read_text(encoding="utf-8")
        new_content = transform(content)
        if new_content != content:
            py_file.write_text(new_content, encoding="utf-8")
            updated.append(py_file.relative_to(REPO_ROOT))
        else:
            skipped.append(py_file.relative_to(REPO_ROOT))

    print(f"Updated {len(updated)} files:")
    for f in updated:
        print(f"  {f}")
    print(f"\nUnchanged: {len(skipped)} files")


if __name__ == "__main__":
    main()
