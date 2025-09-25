#!/usr/bin/env python3
"""
Fix relative imports within the same package
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports based on file location"""

    # Determine the module path based on file location
    if 'src/core' in filepath:
        replacements = [
            (r'from src\.core\.(\w+) import', r'from .\1 import'),
            (r'from src\.services\.', 'from ..services.'),
            (r'from src\.utils\.', 'from ..utils.'),
            (r'from src\.models\.', 'from ..models.'),
            (r'from src\.workflows\.', 'from ..workflows.'),
        ]
    elif 'src/services' in filepath:
        replacements = [
            (r'from src\.services\.(\w+) import', r'from .\1 import'),
            (r'from src\.core\.', 'from ..core.'),
            (r'from src\.utils\.', 'from ..utils.'),
            (r'from src\.models\.', 'from ..models.'),
            (r'from src\.workflows\.', 'from ..workflows.'),
        ]
    elif 'src/workflows' in filepath:
        replacements = [
            (r'from src\.workflows\.(\w+) import', r'from .\1 import'),
            (r'from src\.core\.', 'from ..core.'),
            (r'from src\.services\.', 'from ..services.'),
            (r'from src\.utils\.', 'from ..utils.'),
            (r'from src\.models\.', 'from ..models.'),
        ]
    elif 'src/api' in filepath:
        replacements = [
            (r'from src\.api\.(\w+) import', r'from .\1 import'),
            (r'from src\.core\.', 'from ..core.'),
            (r'from src\.services\.', 'from ..services.'),
            (r'from src\.utils\.', 'from ..utils.'),
            (r'from src\.models\.', 'from ..models.'),
            (r'from src\.workflows\.', 'from ..workflows.'),
        ]
    elif 'src/utils' in filepath:
        replacements = [
            (r'from src\.utils\.(\w+) import', r'from .\1 import'),
            (r'from src\.core\.', 'from ..core.'),
            (r'from src\.services\.', 'from ..services.'),
            (r'from src\.models\.', 'from ..models.'),
            (r'from src\.workflows\.', 'from ..workflows.'),
        ]
    elif 'src/models' in filepath:
        replacements = [
            (r'from src\.models\.(\w+) import', r'from .\1 import'),
            (r'from src\.core\.', 'from ..core.'),
            (r'from src\.services\.', 'from ..services.'),
            (r'from src\.utils\.', 'from ..utils.'),
            (r'from src\.workflows\.', 'from ..workflows.'),
        ]
    else:
        return  # No changes needed for files outside src/

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        original_content = content

        for old_import, new_import in replacements:
            content = re.sub(old_import, new_import, content)

        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed relative imports in: {filepath}")
        else:
            print(f"⏭️  No relative import changes: {filepath}")
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")

def main():
    """Fix relative imports in all src files"""
    src_dir = 'src'

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.join(root, file)
                fix_imports_in_file(filepath)

if __name__ == "__main__":
    main()