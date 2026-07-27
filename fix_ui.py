import os
import re

directory = 'frontend'

replacements = {
    r'bg-\[\#0B1220\]': 'bg-background',
    r'bg-\[\#111827\]': 'bg-surface',
    r'bg-\[\#1a2537\]': 'bg-surface-2',
    r'border-\[\#1E2D45\]': 'border-border-default',
    r'bg-\[\#1E2D45\]': 'bg-border-default',
    r'text-\[\#9CA3AF\]': 'text-muted-foreground',
    r'text-\[\#F9FAFB\]': 'text-foreground',
    r'bg-gradient-to-': 'bg-linear-to-',
    r'max-w-\[850px\]': 'max-w-212.5',
    r'max-w-\[120px\]': 'max-w-30',
    r'max-w-\[160px\]': 'max-w-40',
    r'max-w-\[200px\]': 'max-w-50',
    r'min-w-\[110px\]': 'min-w-27.5'
}

for root, _, files in os.walk(directory):
    if 'node_modules' in root or '.next' in root:
        continue
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts') or file.endswith('.css'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {path}")
