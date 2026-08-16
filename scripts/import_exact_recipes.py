import os
import re

src_dir = '/home/alex/ai/potemkin.co/RecipesDump'
dst_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'

# Clear destination directory first
for f in os.listdir(dst_dir):
    if f.endswith('.md') or f.endswith('.mdx'):
        os.remove(os.path.join(dst_dir, f))

files = sorted([f for f in os.listdir(src_dir) if f.endswith('.md')])

def slugify(title):
    s = title.lower()
    # Remove emoji
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s).strip('-')
    return s

def clean_wiki_links(text):
    def repl(m):
        inner = m.group(1).strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', inner):
            return f'*{inner}*'
        return inner
    return re.sub(r'\[\[(.*?)\]\]', repl, text)

def fix_code_fences(body):
    lines = body.splitlines()
    fixed_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code:
                fixed_lines.append('```')
                in_code = False
                continue
            else:
                in_code = True
                tag = stripped[3:].strip()
                if '/' in tag:
                    fixed_lines.append(f'# {tag}')
                    fixed_lines.append('```bash')
                elif tag in ['```', '````']:
                    fixed_lines.append('```')
                elif not tag:
                    fixed_lines.append('```bash')
                else:
                    fixed_lines.append(f'```{tag}')
                continue
        fixed_lines.append(line)
        
    if in_code:
        fixed_lines.append('```')
        
    return '\n'.join(fixed_lines)

for filename in files:
    src_file = os.path.join(src_dir, filename)
    with open(src_file, 'r', encoding='utf-8') as fp:
        raw_content = fp.read()
        
    # Get exact title from filename (removing emoji and .md)
    title = filename.replace('.md', '').replace('😈 ', '').strip()
    slug = slugify(title)
    
    # Process body: preserve user's words exactly, only clean wiki links and code fence syntax
    body = clean_wiki_links(raw_content)
    body = fix_code_fences(body)
    
    # Frontmatter
    # Escape quotes in title if any
    safe_title = title.replace('"', '\\"')
    frontmatter = f"""---
title: "{safe_title}"
---

"""
    final_content = frontmatter + body.strip() + '\n'
    
    out_file = os.path.join(dst_dir, f"{slug}.md")
    with open(out_file, 'w', encoding='utf-8') as fp:
        fp.write(final_content)
        
    print(f"Created: {slug}.md (Title: {title})")

print(f"Total processed: {len(files)} recipes")
