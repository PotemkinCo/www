import os
import re

files_to_check = [
    'caddy-web-server-and-proxy.md',
    'cloudron-managed-apps.md',
    'freebsd-bare-metal-zfs-and-jails.md',
    'lago-open-source-billing.md',
    'postgresql-administration-and-backups.md'
]

recipe_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'

for fname in files_to_check:
    path = os.path.join(recipe_dir, fname)
    with open(path, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    
    print(f"=== {fname} ({len(lines)} lines) ===")
    in_code = False
    fence_lines = []
    for idx, line in enumerate(lines):
        if line.strip().startswith('```'):
            in_code = not in_code
            fence_lines.append((idx + 1, line.strip(), in_code))
    
    for fl in fence_lines:
        status = "OPEN " if fl[2] else "CLOSE"
        print(f"  Line {fl[0]:4d}: {status} {fl[1]}")
    if in_code:
        print(f"  --> END OF FILE IS STILL OPEN! Last opened at line {fence_lines[-1][0]}")
