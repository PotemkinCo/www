import os
import re

recipe_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'

def fix_markdown_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    
    # Check frontmatter boundary
    if not lines or lines[0].strip() != '---':
        return
    
    fm_end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            fm_end = i
            break
            
    if fm_end == -1:
        return
        
    fm_lines = lines[:fm_end+1]
    body_lines = lines[fm_end+1:]
    
    fixed_body = []
    in_code = False
    
    for idx, line in enumerate(body_lines):
        stripped = line.strip()
        
        # Check if line is a code fence
        if stripped.startswith('```'):
            if in_code:
                # We are inside code, so this line should CLOSE the code block
                fixed_body.append('```\n')
                in_code = False
                continue
            else:
                # We are opening code
                in_code = True
                # Clean up language tag if it contains paths like ```/etc/caddy/Caddyfile -> ```caddyfile or ```bash
                tag = stripped[3:].strip()
                if '/' in tag:
                    fixed_body.append(f'# {tag}\n')
                    fixed_body.append('```bash\n')
                elif tag in ['```', '````']:
                    fixed_body.append('```\n')
                elif not tag:
                    fixed_body.append('```bash\n')
                else:
                    fixed_body.append(f'```{tag}\n')
                continue
        
        # If outside code block:
        if not in_code:
            # Fix lines that start with ## # or ## sudo or ## echo that were meant to be code or notes
            if re.match(r'^##\s+#\s*', line):
                # Turn into note comment or normal text
                clean = re.sub(r'^##\s+#\s*', '', line).strip()
                fixed_body.append(f'> **Note**: {clean}\n')
                continue
            elif re.match(r'^##\s+(echo|sudo|cat|curl|export|chmod|chown|systemctl)\s+', line):
                cmd = re.sub(r'^##\s+', '', line).strip()
                fixed_body.append('```bash\n' + cmd + '\n```\n')
                continue
            elif re.match(r'^#!\/(bin|usr)', line):
                # Loose shebang outside code fence
                fixed_body.append('```bash\n' + line)
                in_code = True
                continue
                
        fixed_body.append(line)
        
    if in_code:
        fixed_body.append('\n```\n')
        in_code = False
        
    full = ''.join(fm_lines) + ''.join(fixed_body)
    with open(filepath, 'w', encoding='utf-8') as fp:
        fp.write(full)

for f in sorted(os.listdir(recipe_dir)):
    if f.endswith('.md'):
        fix_markdown_file(os.path.join(recipe_dir, f))

print("Completed markdown fence and heading repair.")
