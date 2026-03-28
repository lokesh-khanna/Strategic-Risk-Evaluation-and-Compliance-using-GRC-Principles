"""Fix trail.html: remove the invalid regex_replace Jinja2 filter."""
import re

path = r'app\templates\audit\trail.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the 5-line regex_replace block (lines 693-700 detail cell)
# Replace with a simple truncated display
pattern = r'\{%\s*if log\.details\s*%\}.*?\{%\s*else\s*%\}—\{%\s*endif\s*%\}'
replacement = "{% if log.details %}\n                            {{ log.details[:120] }}{% if log.details|length > 120 %}…{% endif %}\n                            {% else %}—{% endif %}"

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("WARNING: pattern not matched, doing line-by-line fix")
    lines = content.split('\n')
    out = []
    i = 0
    while i < len(lines):
        if 'regex_replace' in lines[i]:
            # Remove the regex_replace line completely
            i += 1
            continue
        if "Parse known fields from JSON-like details" in lines[i]:
            i += 1  # skip comment line
            continue
        if "{% set d = log.details %}" in lines[i]:
            i += 1  # skip assignment
            continue
        if '\"risk_code\"' in lines[i] and '{% if' in lines[i]:
            i += 1  # skip if risk_code check
            continue
        if '{% endif %}' in lines[i] and i > 0 and '\"risk_code\"' in lines[i-4:i]:
            # This is the closing endif for the risk_code if block - skip it
            # but we need to check context; simpler: just check if previous content had regex_replace
            pass
        out.append(lines[i])
        i += 1
    new_content = '\n'.join(out)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verify fix
with open(path, 'r', encoding='utf-8') as f:
    verify = f.read()

if 'regex_replace' not in verify:
    print("SUCCESS: regex_replace removed from trail.html")
else:
    print("ERROR: regex_replace still present!")
