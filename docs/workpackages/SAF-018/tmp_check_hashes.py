import hashlib, re
from pathlib import Path

def compute_canonical_hash(path):
    content = Path(path).read_bytes()
    canonical = re.sub(
        rb'(?<=_KNOWN_GOOD_GATE_HASH: str = ")[0-9a-fA-F]{64}',
        b'0' * 64,
        content,
    )
    return hashlib.sha256(canonical).hexdigest()

p1 = 'Default-Project/.github/hooks/scripts/security_gate.py'
p2 = 'templates/coding/.github/hooks/scripts/security_gate.py'
h1 = compute_canonical_hash(p1)
h2 = compute_canonical_hash(p2)
stored1 = re.search(rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', Path(p1).read_bytes()).group(1).decode()
stored2 = re.search(rb'_KNOWN_GOOD_GATE_HASH: str = "([0-9a-f]{64})"', Path(p2).read_bytes()).group(1).decode()
print(f'Default-Project computed: {h1}')
print(f'templates/coding computed: {h2}')
print(f'Stored in Default-Project: {stored1}')
print(f'Stored in templates/coding: {stored2}')
print(f'DP hash matches stored: {h1 == stored1}')
print(f'TPL hash matches stored: {h2 == stored2}')
