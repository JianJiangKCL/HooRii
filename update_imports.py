#!/usr/bin/env python3
"""
Update imports after restructuring
"""

import os
import re

# Define the import replacements
REPLACEMENTS = [
    # Core imports
    (r'from intent_analyzer import', 'from src.core.intent_analyzer import'),
    (r'from device_controller import', 'from src.core.device_controller import'),
    (r'from character_system import', 'from src.core.character_system import'),
    (r'from context_manager import', 'from src.core.context_manager import'),
    (r'import intent_analyzer', 'import src.core.intent_analyzer'),
    (r'import device_controller', 'import src.core.device_controller'),
    (r'import character_system', 'import src.core.character_system'),
    (r'import context_manager', 'import src.core.context_manager'),

    # Services imports
    (r'from database_service import', 'from src.services.database_service import'),
    (r'from langfuse_session_manager import', 'from src.services.langfuse_session_manager import'),
    (r'import database_service', 'import src.services.database_service'),
    (r'import langfuse_session_manager', 'import src.services.langfuse_session_manager'),

    # Models imports
    (r'from models import', 'from src.models.database import'),
    (r'import models', 'import src.models.database'),

    # Utils imports
    (r'from config import', 'from src.utils.config import'),
    (r'from device_simulator import', 'from src.utils.device_simulator import'),
    (r'from task_planner import', 'from src.utils.task_planner import'),
    (r'from user_device_management import', 'from src.utils.user_device_management import'),
    (r'import config', 'import src.utils.config'),

    # Workflow imports
    (r'from main import', 'from src.workflows.traditional_workflow import'),
    (r'from langraph_workflow import', 'from src.workflows.langraph_workflow import'),
    (r'import main', 'import src.workflows.traditional_workflow'),
    (r'import langraph_workflow', 'import src.workflows.langraph_workflow'),

    # API imports
    (r'from api import', 'from src.api.server import'),
    (r'import api', 'import src.api.server'),
]

def update_imports_in_file(filepath):
    """Update imports in a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        original_content = content

        for old_import, new_import in REPLACEMENTS:
            content = re.sub(old_import, new_import, content)

        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Updated: {filepath}")
        else:
            print(f"⏭️  No changes: {filepath}")
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")

def main():
    """Update all Python files"""
    # List of directories to process
    directories = [
        'src/core',
        'src/services',
        'src/workflows',
        'src/api',
        'src/utils',
        'src/models',
        'tests',
        'scripts'
    ]

    for directory in directories:
        if not os.path.exists(directory):
            continue

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    update_imports_in_file(filepath)

if __name__ == "__main__":
    main()