"""Fix remaining / "coding" pathlib patterns with different indentation levels."""

import os
from pathlib import Path

base = Path(r"e:\Projekte\SAE-Development\Github Repository")

SKIP_FILES = {
    "tests/GUI-023/test_gui023_template_rename.py",
    "tests/GUI-023/test_gui023_tester_edge_cases.py",
}

# Fix 8-space indented version (inside functions)
OLD_8 = '        / "coding"\n        / ".github"'
NEW_8 = '        / "agent-workbench"\n        / ".github"'

# Also fix 4/8-space paths ending in security_gate.py or update_hashes.py
# that don't have ".github" immediately after (e.g. long paths)
# These are caught by the above since .github IS in the path

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
        if OLD_8 in content:
            new_content = content.replace(OLD_8, NEW_8)
            fpath.write_text(new_content, encoding="utf-8")
            count = content.count(OLD_8)
            fixed.append(f"{rel} ({count} replacements)")

for f in fixed:
    print(f"Fixed: {f}")
print(f"Total: {len(fixed)} files")
