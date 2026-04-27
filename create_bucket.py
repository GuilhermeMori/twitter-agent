#!/usr/bin/env python3
"""
Script to create the required Supabase Storage bucket for campaign documents.
"""

import os
from supabase import create_client, Client

def create_bucket():
    """Create the campaign-documents bucket in Supabase Storage."""
    
    # Load environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment")
        return False
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    bucket_name = "campaign-documents"
    
    try:
        # Try to create the bucket
        result = supabase.storage.create_bucket(bucket_name)
        print(f"✅ Successfully created bucket: {bucket_name}")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        error_str = str(e)
        if "already exists" in error_str.lower():
            print(f"✅ Bucket {bucket_name} already exists")
            return True
        else:
            print(f"❌ Failed to create bucket: {e}")
            return False

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    success = create_bucket()
    if success:
        print("\n🎉 Bucket setup complete! You can now execute campaigns.")
    else:
        print("\n❌ Bucket setup failed. Please check your Supabase credentials.")