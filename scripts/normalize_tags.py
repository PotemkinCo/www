import os
import re

recipe_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'

# Mapping uncommon language identifiers to supported shiki/expressive-code languages
lang_map = {
    'caddy': 'txt',
    'caddyfile': 'txt',
    'compose': 'yaml',
    'docker-compose': 'yaml',
    'rclone.conf': 'ini',
    'conf': 'ini',
    'toml': 'toml',
    'cron': 'bash',
    'crontab': 'bash',
    'yaml': 'yaml',
    'yml': 'yaml',
    'start.sh': 'bash',
    'vllm_ocr.service': 'ini',
    'service': 'ini',
}

for fname in sorted(os.listdir(recipe_dir)):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(recipe_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
        
    changed = False
    new_lines = []
    for line in lines:
        if line.startswith('```'):
            raw_tag = line[3:].strip()
            lower_tag = raw_tag.lower()
            if lower_tag in lang_map:
                new_lines.append(f'```{lang_map[lower_tag]}\n')
                changed = True
                continue
            elif raw_tag.isupper() and lower_tag in ['bash', 'sh', 'json', 'yaml', 'toml', 'python', 'sql']:
                new_lines.append(f'```{lower_tag}\n')
                changed = True
                continue
        new_lines.append(line)
        
    if changed:
        with open(fpath, 'w', encoding='utf-8') as fp:
            fp.writelines(new_lines)
        print(f"Normalized language tags in {fname}")

print("Done normalizing code block language tags.")
