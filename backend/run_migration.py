#!/usr/bin/env python3
"""
Run database migration to add 'scenes_processing' status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase import SupabaseService
from app.config import settings

def run_migration():
    """Run the migration to add scenes_processing status"""

    print("🔄 Running migration: Add 'scenes_processing' status to projects table...")

    # Initialize Supabase service
    supabase_service = SupabaseService()

    if not supabase_service.admin_client:
        print("❌ Error: Admin client not available. Check SUPABASE_SERVICE_KEY in .env")
        return False

    # Migration SQL
    migration_sql = """
    -- Drop the existing constraint
    ALTER TABLE projects DROP CONSTRAINT projects_status_check;

    -- Add the new constraint with 'scenes_processing' included
    ALTER TABLE projects ADD CONSTRAINT projects_status_check
        CHECK (status IN ('created', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete', 'scenes_processing'));
    """

    try:
        # Execute the migration
        result = supabase_service.admin_client.rpc('exec', {'sql': migration_sql}).execute()

        print("✅ Migration completed successfully!")
        print("✅ 'scenes_processing' status is now allowed for projects")

        # Test the migration by checking current constraint
        print("\n🔍 Verifying migration...")
        test_result = supabase_service.admin_client.rpc('exec', {
            'sql': """
            SELECT
                conname as constraint_name,
                consrc as constraint_definition
            FROM pg_constraint
            WHERE conname = 'projects_status_check';
            """
        }).execute()

        if test_result.data:
            print(f"✅ Current constraint: {test_result.data}")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")

        # Try alternative approach using direct SQL execution
        try:
            print("🔄 Trying alternative approach...")

            # Step 1: Drop constraint
            supabase_service.admin_client.rpc('exec', {
                'sql': "ALTER TABLE projects DROP CONSTRAINT projects_status_check;"
            }).execute()

            # Step 2: Add new constraint
            supabase_service.admin_client.rpc('exec', {
                'sql': """ALTER TABLE projects ADD CONSTRAINT projects_status_check
                         CHECK (status IN ('created', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete', 'scenes_processing'));"""
            }).execute()

            print("✅ Migration completed with alternative approach!")
            return True

        except Exception as e2:
            print(f"❌ Alternative approach also failed: {str(e2)}")
            print("\n💡 Manual steps needed:")
            print("1. Go to Supabase dashboard → SQL Editor")
            print("2. Run this SQL:")
            print("   ALTER TABLE projects DROP CONSTRAINT projects_status_check;")
            print("   ALTER TABLE projects ADD CONSTRAINT projects_status_check CHECK (status IN ('created', 'transcribing', 'analyzing', 'generating', 'reviewing', 'complete', 'scenes_processing'));")
            return False

if __name__ == "__main__":
    print("🗄️  OMVEE Database Migration")
    print("=" * 50)

    success = run_migration()

    if success:
        print("\n🎉 Migration completed! Scene generation should now work.")
        print("🧪 Try the scene generation API call again.")
    else:
        print("\n❌ Migration failed. Manual intervention required.")

    sys.exit(0 if success else 1)