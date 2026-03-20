"""Quick verification of Phase A CSV repairs."""
import csv
from pathlib import Path

wp = Path("docs/workpackages/workpackages.csv")
with open(wp, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

ids = {r["ID"] for r in rows}
print(f"workpackages.csv: {len(rows)} rows")
print(f"  FIX-037 present: {'FIX-037' in ids}")

for r in rows:
    if r["ID"] in ("FIX-036", "FIX-037", "FIX-040", "FIX-047"):
        us = r.get("User Story", "")
        print(f"  {r['ID']} User Story: '{us}'")

bug = Path("docs/bugs/bugs.csv")
with open(bug, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["ID"] in ("BUG-084", "BUG-088", "BUG-089", "BUG-090"):
            print(f"  {row['ID']}: Status={row['Status']}, Fixed In WP={row.get('Fixed In WP', '')}")
