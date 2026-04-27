import os
from apify_client import ApifyClient
from src.core.database import get_supabase_client
from src.repositories.configuration_repository import ConfigurationRepository
from src.services.configuration_manager import ConfigurationManager
from src.utils.encryption import Encryptor

def test():
    db = get_supabase_client()
    config_repo = ConfigurationRepository(db)
    encryptor = Encryptor()
    config_mgr = ConfigurationManager(config_repo, encryptor)
    config = config_mgr.get_configuration()
    
    client = ApifyClient(config.apify_token)
    run_input = {
        "searchTerms": ["DTC brand scaling"],
        "maxResults": 1,
        "mode": "search",
    }
    
    # Inject cookies if available
    if config.twitter_auth_token and config.twitter_ct0:
        run_input["twitterCookie"] = f"auth_token={config.twitter_auth_token}; ct0={config.twitter_ct0}"
    
    print("Running Apify actor...")
    run = client.actor("automation-lab/twitter-scraper").call(run_input=run_input)
    dataset_id = run["defaultDatasetId"]
    
    items = list(client.dataset(dataset_id).iterate_items())
    if items:
        print("KEYS IN RAW ITEM:")
        print(items[0].keys())
        print("\nFULL RAW ITEM (keys and a bit of values):")
        for k, v in items[0].items():
            print(f"{k}: {str(v)[:100]}")
    else:
        print("No items returned from Apify.")

if __name__ == "__main__":
    test()
