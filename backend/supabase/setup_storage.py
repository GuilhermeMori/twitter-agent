"""
Supabase Storage bucket setup script.

Run this once after creating your Supabase project to create the
'campaign-documents' bucket used for storing generated .doc files.

Usage:
    cd backend
    python supabase/setup_storage.py
"""

import sys
import os

# Allow running from the backend/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import get_supabase_client  # noqa: E402


def setup_storage_bucket() -> None:
    """Create the campaign-documents storage bucket if it doesn't exist."""
    client = get_supabase_client()
    bucket_name = "campaign-documents"

    try:
        # List existing buckets
        buckets = client.storage.list_buckets()
        existing_names = [b.name for b in buckets]

        if bucket_name in existing_names:
            print(f"✅ Bucket '{bucket_name}' already exists — skipping creation.")
            return

        # Create the bucket (private — access via signed URLs)
        client.storage.create_bucket(
            bucket_name,
            options={
                "public": False,
                "allowed_mime_types": [
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/msword",
                ],
                "file_size_limit": 10 * 1024 * 1024,  # 10 MB
            },
        )
        print(f"✅ Bucket '{bucket_name}' created successfully.")

    except Exception as exc:
        print(f"❌ Failed to set up storage bucket: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    setup_storage_bucket()
