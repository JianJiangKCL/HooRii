#!/usr/bin/env python3
"""
Migration to add interaction_count field to User table
"""
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config
from database_service import DatabaseService

def migrate_add_interaction_count():
    """Add interaction_count column to users table if it doesn't exist"""
    print("🔧 Running migration: Add interaction_count to User table")
    
    try:
        config = load_config()
        db_service = DatabaseService(config)
        
        # Get a database session
        session = db_service.get_session()
        
        try:
            # Check if column exists by trying to select it
            result = session.execute(text("SELECT interaction_count FROM users LIMIT 1"))
            print("✅ Column interaction_count already exists")
            
        except Exception as e:
            if "no such column" in str(e).lower() or "column" in str(e).lower():
                print("📝 Adding interaction_count column...")
                
                # Add the column with default value
                session.execute(text("ALTER TABLE users ADD COLUMN interaction_count INTEGER DEFAULT 0 NOT NULL"))
                session.commit()
                print("✅ Added interaction_count column successfully")
            else:
                print(f"❌ Unexpected error: {e}")
                raise
        
        finally:
            session.close()
            
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_add_interaction_count()