#!/usr/bin/env python3
"""
Script to run SQL migrations against Supabase database.
Usage: python run_migration.py <migration_file.sql>
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

def run_migration(migration_file: str):
    """Run a SQL migration file against Supabase."""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
    
    # Read migration file
    migration_path = Path(__file__).parent / "migrations" / migration_file
    if not migration_path.exists():
        print(f"❌ Error: Migration file not found: {migration_path}")
        sys.exit(1)
    
    print(f"📄 Reading migration file: {migration_file}")
    with open(migration_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # Create Supabase client
    print(f"🔌 Connecting to Supabase: {supabase_url}")
    client = create_client(supabase_url, supabase_key)
    
    # Execute SQL
    print(f"⚙️  Executing migration...")
    try:
        # Supabase Python client doesn't have direct SQL execution
        # We need to use the REST API or PostgREST
        # For now, we'll use the rpc method if available
        
        # Note: Supabase Python client doesn't support raw SQL execution
        # Users should run this via Supabase Dashboard SQL Editor or psql
        print("⚠️  Note: Supabase Python client doesn't support raw SQL execution.")
        print("📋 Please run this migration using one of these methods:")
        print()
        print("1. Supabase Dashboard SQL Editor:")
        print(f"   - Go to: {supabase_url.replace('https://', 'https://app.supabase.com/project/')}")
        print("   - Navigate to SQL Editor")
        print(f"   - Copy and paste the contents of: {migration_path}")
        print("   - Click 'Run'")
        print()
        print("2. Using psql (PostgreSQL CLI):")
        print(f"   psql -h db.<project-ref>.supabase.co -U postgres -d postgres -f {migration_path}")
        print()
        print("📄 Migration SQL content:")
        print("=" * 80)
        print(sql_content)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error executing migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        print("Example: python run_migration.py create_assistants_table.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    run_migration(migration_file)
