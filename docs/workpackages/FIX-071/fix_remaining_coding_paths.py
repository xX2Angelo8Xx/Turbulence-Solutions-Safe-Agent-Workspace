"""Fix all remaining / "coding" pathlib multiline patterns in test files."""

import os
from pathlib import Path

base = Path(r"e:\Projekte\SAE-Development\Github Repository")

SKIP_FILES = {
    "tests/GUI-023/test_gui023_template_rename.py",
    "tests/GUI-023/test_gui023_tester_edge_cases.py",
}

OLD = '    / "coding"\n    / ".github"'
NEW = '    / "agent-workbench"\n    / ".github"'

fixed = []
for root, dirs, files in os.walk(str(base / "tests")):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = Path(root) / fname
        rel = str(fpath.relative_to(base)).replace("\\", "/")
        if rel in SKIP_FILES:
            continue
        content = fpath.read_text(encoding="utf-8")
        if OLD in content:
            new_content = content.replace(OLD, NEW)
            fpath.write_text(new_content, encoding="utf-8")
            count = content.count(OLD)
            fixed.append(f"{rel} ({count} replacements)")

for f in fixed:
    print(f"Fixed: {f}")
print(f"Total: {len(fixed)} files")
