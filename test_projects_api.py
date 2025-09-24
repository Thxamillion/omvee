#!/usr/bin/env python3
"""
Test script to investigate projects API issue
"""

import sys
sys.path.append('/Users/quinortiz/Documents/omvee/backend')

from app.services.supabase import supabase_service

def test_projects_directly():
    """Test the supabase service directly"""
    print("🔍 Testing direct Supabase projects query...")

    try:
        # Test direct database query
        result = supabase_service.list_projects(skip=0, limit=10)
        print(f"✅ Direct query result: {result}")
        print(f"   - Total projects: {result.get('total', 0)}")
        print(f"   - Projects returned: {len(result.get('projects', []))}")

        # Show project details
        projects = result.get('projects', [])[:3]
        for i, project in enumerate(projects):
            print(f"   - Project {i+1}:")
            print(f"     • ID: {project.get('id')}")
            print(f"     • Name: {project.get('name')}")
            print(f"     • User ID: {project.get('user_id')}")
            print(f"     • Status: {project.get('status')}")
            print(f"     • Created: {project.get('created_at')}")

    except Exception as e:
        print(f"❌ Error with direct query: {e}")
        import traceback
        traceback.print_exc()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase connection...")

    try:
        # Test a simple query
        result = supabase_service.client.table('projects').select('count').execute()
        print(f"✅ Connection successful: {result}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting projects API investigation...")
    print("=" * 50)

    test_supabase_connection()
    print()
    test_projects_directly()

    print("\n" + "=" * 50)
    print("✅ Investigation complete!")