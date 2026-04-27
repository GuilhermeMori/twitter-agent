#!/usr/bin/env python3
"""
Script to verify the assistants table was created correctly.
Usage: python verify_assistants_migration.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_migration():
    """Verify the assistants table and data."""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
    
    print(f"🔌 Connecting to Supabase: {supabase_url}")
    client = create_client(supabase_url, supabase_key)
    
    try:
        # Query assistants table
        print("\n📊 Querying assistants table...")
        response = client.table("assistants").select("*").execute()
        
        if not response.data:
            print("⚠️  Warning: No assistants found in the table")
            print("   The migration may not have been executed yet.")
            return
        
        print(f"✅ Found {len(response.data)} assistant(s)")
        print()
        
        # Verify we have exactly 3 assistants
        if len(response.data) != 3:
            print(f"⚠️  Warning: Expected 3 assistants, found {len(response.data)}")
        
        # Display each assistant
        roles_found = set()
        for assistant in response.data:
            role = assistant.get("role")
            name = assistant.get("name")
            title = assistant.get("title")
            skills = assistant.get("skills", [])
            is_editable = assistant.get("is_editable")
            
            roles_found.add(role)
            
            print(f"🤖 {name}")
            print(f"   Title: {title}")
            print(f"   Role: {role}")
            print(f"   Skills: {', '.join(skills) if skills else 'None'}")
            print(f"   Editable: {'Yes' if is_editable else 'No'}")
            print(f"   Principles: {len(assistant.get('principles', []))} items")
            print(f"   Quality Criteria: {len(assistant.get('quality_criteria', []))} items")
            print()
        
        # Verify all roles are present
        expected_roles = {"search", "comment", "review"}
        missing_roles = expected_roles - roles_found
        extra_roles = roles_found - expected_roles
        
        if missing_roles:
            print(f"⚠️  Warning: Missing roles: {', '.join(missing_roles)}")
        
        if extra_roles:
            print(f"⚠️  Warning: Unexpected roles: {', '.join(extra_roles)}")
        
        if roles_found == expected_roles and len(response.data) == 3:
            print("✅ Migration verification successful!")
            print("   All 3 assistants are present with correct roles.")
        
    except Exception as e:
        print(f"❌ Error querying assistants table: {e}")
        print()
        print("This likely means the migration hasn't been executed yet.")
        print("Please run the migration first using one of these methods:")
        print()
        print("1. Supabase Dashboard SQL Editor")
        print("2. PostgreSQL CLI (psql)")
        print()
        print("See backend/migrations/README_ASSISTANTS.md for instructions.")
        sys.exit(1)

if __name__ == "__main__":
    verify_migration()
