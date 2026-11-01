#!/usr/bin/env python3
"""Small offline repository hygiene check, not a complete secret scanner."""
from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
result = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                        cwd=ROOT, capture_output=True, check=True)
files = sorted(set(result.stdout.decode().split('\0')) - {''})
errors = []
private_ip = re.compile(r'\b(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b')
patterns = [private_ip, re.compile('gh' + '[pousr]_[A-Za-z0-9]{20,}'),
            re.compile('github' + '_pat_[A-Za-z0-9_]{20,}'),
            re.compile('-----BEGIN ' + '(?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
            re.compile(r'\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b')]
blocked = {'.wgt', '.tpk', '.dll', '.pdb', '.so', '.db', '.p12', '.pem', '.key', '.pfx'}
for name in files:
    path = ROOT / name
    if '.local' in path.parts or path.suffix in blocked:
        errors.append(name + ': private/generated file')
        continue
    if path.is_symlink():
        errors.append(name + ': symlink not allowed in export')
        continue
    try:
        content = path.read_text()
    except UnicodeError:
        errors.append(name + ': unexpected binary')
        continue
    if any(p.search(content) for p in patterns):
        errors.append(name + ': possible private data (value suppressed)')
    if path.suffix == '.json':
        json.loads(content)
    if path.suffix == '.md':
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if '://' in target or target.startswith('#'):
                continue
            local = target.split('#', 1)[0]
            if local and not (path.parent / local).exists():
                errors.append(name + ': broken relative link ' + local)
if errors:
    raise SystemExit('\n'.join(errors))
print(f'{len(files)} candidate files checked; no matched private-data patterns or broken relative links.')
