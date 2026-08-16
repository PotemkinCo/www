import os
import re

recipe_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'
files = sorted(os.listdir(recipe_dir))

for f in files:
    with open(os.path.join(recipe_dir, f), 'r', encoding='utf-8') as fp:
        content = fp.read()
    
    # Check for unclosed codeblocks
    code_fences = len(re.findall(r'^```', content, flags=re.M))
    if code_fences % 2 != 0:
        print(f'WARNING: Unclosed code block in {f} ({code_fences} fences)')
    
    # Check for suspicious markdown headers
    suspicious_headers = re.findall(r'^##+\s+(#.*|!.*|/.*|sudo.*|echo.*|cat.*|curl.*)', content, flags=re.M)
    if suspicious_headers:
        print(f'Suspicious headers in {f}: {suspicious_headers}')
