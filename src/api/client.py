import tweepy
import random
import logging
import time

from config import load_config

def initialize_twitter_client():
    """
    Initialize Twitter API client with error handling.
    
    Returns:
        tweepy.Client: Authenticated Twitter API client.
        
    Raises:
        tweepy.errors.Unauthorized: If authentication fails.
        tweepy.errors.Forbidden: If account is suspended.
        Exception: If client initialization fails after max retries.
    """
    config = load_config()
    twitter_api = config["twitter_api"]
    
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            client = tweepy.Client(
                bearer_token=twitter_api["BEARER_TOKEN"],
                consumer_key=twitter_api["API_KEY"],
                consumer_secret=twitter_api["API_SECRET"],
                access_token=twitter_api["ACCESS_TOKEN"],
                access_token_secret=twitter_api["ACCESS_SECRET"],
                wait_on_rate_limit=False  # We'll handle rate limits ourselves
            )
            
            # Test connection by checking account
            me = client.get_me()
            if me and hasattr(me, "data") and me.data:
                logging.info(f"✅ Twitter API connection successful - authenticated as @{me.data.username}")
                return client
            else:
                raise tweepy.errors.TweepyException("Failed account verification")
                
        except tweepy.errors.Unauthorized:
            logging.critical("❌ Twitter API authentication failed. Check API keys.")
            # Don't retry auth failures - keys are likely invalid
            raise
        except tweepy.errors.Forbidden:
            logging.critical("⛔ Your Twitter account may be suspended or tokens revoked.")
            # Don't retry forbidden errors - account issues
            raise
        except tweepy.errors.TooManyRequests as e:
            retry_count += 1
            wait_time = 60 * retry_count
            
            # Check for Retry-After header
            if hasattr(e, 'response') and e.response and 'Retry-After' in e.response.headers:
                try:
                    wait_time = int(e.response.headers['Retry-After']) + random.randint(1, 5)
                except (ValueError, TypeError):
                    pass
                    
            logging.warning(f"⚠️ Rate limited during initialization. Retry {retry_count}/{max_retries} in {wait_time}s")
            time.sleep(wait_time)
        except Exception as e:
            retry_count += 1
            wait_time = 30 * retry_count
            logging.error(f"❌ Failed to initialize Twitter client: {e}. Retry {retry_count}/{max_retries} in {wait_time}s")
            time.sleep(wait_time)
    
    # If we've exhausted all retries
    raise Exception("Failed to initialize Twitter client after multiple attempts")
