import os
from src.core.database import get_supabase_client

def check():
    db = get_supabase_client()
    # Get one tweet from a recent campaign
    result = db.table("results").select("*").limit(1).execute()
    if result.data:
        print("TWEET DATA FROM DB:")
        print(result.data[0])
    else:
        print("No results found in DB.")

if __name__ == "__main__":
    check()
