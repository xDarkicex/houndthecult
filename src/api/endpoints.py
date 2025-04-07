import tweepy
import logging
import random
import time
from datetime import datetime, timedelta

from src.utils.timing import human_delay
from src.rate_limiting.backoff import handle_rate_limit_response
from config import load_config

def search_for_mentions(client, bot_state, username="HoundTheCult"):
    """
    Search for mentions with realistic timing and gradual rate limiting.
    
    Args:
        client (tweepy.Client): Authenticated Twitter API client.
        bot_state: Bot state manager object.
        username (str): Twitter username to search for mentions of.
        
    Returns:
        list: List of mentions found, or empty list if none or error.
    """
    human_delay(5, 15)  # Random delay before searching
    
    # Apply gradual backoff based on current usage
    backoff_delay = bot_state.get_gradual_backoff_delay("search")
    if backoff_delay > 0:
        logging.info(f"Applying gradual backoff delay of {backoff_delay:.1f}s for search (usage: {bot_state.get_search_usage_ratio():.2%})")
        time.sleep(backoff_delay)
    
    # Check if we can make a search request within rate limits
    if not bot_state.can_search():
        wait_time = bot_state.get_search_window_reset() + random.randint(5, 20)
        logging.warning(f"⚠️ Search rate limit reached. Waiting {wait_time:.1f}s")
        time.sleep(wait_time)
    
    query = f"@{username} -is:retweet"
    start_time = None
    
    if bot_state.last_check_time:
        last_check = datetime.fromisoformat(bot_state.last_check_time)
        if (datetime.now() - last_check).total_seconds() < 60:
            start_time = (datetime.now() - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            start_time = last_check.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    try:
        response = client.search_recent_tweets(
            query=query,
            max_results=10,
            expansions=["referenced_tweets.id", "referenced_tweets.id.author_id", "author_id"],
            tweet_fields=["created_at", "author_id", "conversation_id"],
            start_time=start_time,
            user_auth=True
        )
        
        # Record the search request in our rate limiter
        bot_state.record_search()
        
        if not response.data:
            logging.info("😴 No new mentions found.")
            return []
        
        mentions = []
        referenced_tweets = {}
        
        # Build a dict of referenced tweets for quick lookup
        if response.includes and "tweets" in response.includes:
            referenced_tweets = {t.id: t for t in response.includes["tweets"]}
        
        for tweet in response.data:
            mention_data = {
                "id": tweet.id,
                "text": tweet.text,
                "author_id": tweet.author_id,
                "created_at": tweet.created_at,
                "referenced_tweet_id": None
            }
            
            if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets:
                for ref in tweet.referenced_tweets:
                    if ref.type == "replied_to":
                        mention_data["referenced_tweet_id"] = ref.id
                        if ref.id in referenced_tweets:
                            mention_data["referenced_tweet"] = referenced_tweets[ref.id]
                        break
            
            mentions.append(mention_data)
        
        return mentions
    
    except tweepy.errors.TooManyRequests as e:
        handle_rate_limit_response(429, getattr(e, 'response', {}).headers if hasattr(e, 'response') else None, bot_state, "search")
        return []
    except Exception as e:
        logging.error(f"Error searching mentions: {e}")
        handle_rate_limit_response(None, None, bot_state, "search")
        return []

def process_mention(mention, client, bot_state):
    """
    Process a single mention with all safety checks.
    
    Args:
        mention (dict): Mention data.
        client (tweepy.Client): Authenticated Twitter API client.
        bot_state: Bot state manager object.
    """
    config = load_config()
    SNARKY_COMMENTS = config.get("snarky_comments", [
        "Found one!",
        "Another gem from the cult..."
    ])
    
    user_id = str(mention["author_id"])
    
    # Handle opt-in/out commands
    if "!optout" in mention.get("text", "").lower():
        bot_state.update_user_prefs(user_id, "opt_out")
        return
    elif "!optin" in mention.get("text", "").lower():
        bot_state.update_user_prefs(user_id, "opt_in")
        return
    
    # Skip opted-out users
    if bot_state.is_opted_out(user_id):
        logging.info(f"Skipping opted-out user ...{user_id[-4:]}")
        return
    
    # Add randomness to skip some mentions (seems more human-like)
    if random.random() < 0.1:  # 10% chance to skip
        logging.info("Randomly skipping this mention (human-like behavior)")
        return
    
    # Process regular mentions
    if mention.get("referenced_tweet_id"):
        try:
            original_tweet_id = mention["referenced_tweet_id"]
            original_tweet = None
            
            if "referenced_tweet" not in mention:
                # Apply gradual backoff for lookup based on current usage
                backoff_delay = bot_state.get_gradual_backoff_delay("lookup")
                if backoff_delay > 0:
                    logging.info(f"Applying gradual backoff delay of {backoff_delay:.1f}s for lookup (usage: {bot_state.get_lookup_usage_ratio():.2%})")
                    time.sleep(backoff_delay)
                
                # Check if we're within rate limits for tweet lookup
                if not bot_state.can_lookup_tweet():
                    wait_time = bot_state.get_lookup_window_reset() + random.randint(5, 20)
                    logging.warning(f"⚠️ Lookup rate limit reached. Waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                
                original_tweet = client.get_tweet(
                    original_tweet_id,
                    expansions=["author_id"],
                    tweet_fields=["created_at", "author_id", "text"]
                )
                
                # Record the lookup request
                bot_state.record_lookup()
            else:
                original_tweet = {"data": mention["referenced_tweet"]}
            
            if original_tweet and hasattr(original_tweet, 'data') and original_tweet.data:
                # Apply gradual backoff for posting based on current usage
                backoff_delay = bot_state.get_gradual_backoff_delay("post")
                if backoff_delay > 0:
                    logging.info(f"Applying gradual backoff delay of {backoff_delay:.1f}s for posting (usage: {bot_state.get_post_usage_ratio():.2%})")
                    time.sleep(backoff_delay)
                
                # Check if we're within rate limits for posting
                if not bot_state.can_post_tweet():
                    wait_time = bot_state.get_post_window_reset() + random.randint(5, 20)
                    logging.warning(f"⚠️ Post rate limit reached. Waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                
                # Occasionally add slight typos to snarky comments (more human-like)
                snarky_comment = random.choice(SNARKY_COMMENTS)
                if random.random() < 0.05:  # 5% chance of typo
                    char_pos = random.randint(0, len(snarky_comment)-1)
                    snarky_comment = snarky_comment[:char_pos] + snarky_comment[char_pos+1:]
                
                human_delay(5, 45)  # Random delay before posting
                
                result = client.create_tweet(
                    text=snarky_comment,
                    quote_tweet_id=original_tweet_id
                )
                
                # Record the post request
                bot_state.record_post()
                logging.info(f"🔥 Quote tweeted: {snarky_comment}")
                
        except tweepy.errors.TooManyRequests as e:
            handle_rate_limit_response(429, getattr(e, 'response', {}).headers if hasattr(e, 'response') else None, bot_state, "post")
        except tweepy.errors.NotFound:
            logging.warning("🚫 Referenced tweet deleted")
        except tweepy.errors.Forbidden as e:
            logging.warning(f"🚫 Forbidden action: {str(e)}")
            if "suspended" in str(e).lower():
                raise  # Re-raise to handle suspension at a higher level
        except tweepy.errors.TweepyException as e:
            logging.error(f"Error processing tweet: {e}")
            handle_rate_limit_response(None, None, bot_state, "post")
        except Exception as e:
            logging.error(f"Unexpected error processing mention: {e}")
            human_delay(10, 30)  # Brief pause before continuing to next mention

def check_rate_limits(client, bot_state):
    """
    Check current rate limits from Twitter API and reconcile with our tracking.
    
    Args:
        client (tweepy.Client): Authenticated Twitter API client.
        bot_state: Bot state manager object.
    """
    from src.rate_limiting.limiter import SEARCH_RECENT_LIMIT, TWEET_LOOKUP_LIMIT, POST_TWEET_LIMIT
    
    try:
        # This endpoint gives detailed rate limit info
        limits = client.get_rate_limit_status()
        
        # Log current rate limits for key endpoints
        if limits and hasattr(limits, "resources"):
            resources = limits.resources
            
            # Search API
            if "search" in resources and "/search/tweets" in resources["search"]:
                search_limit = resources["search"]["/search/tweets"]
                actual_remaining = search_limit.remaining
                our_used = len(bot_state.search_requests)
                our_remaining = SEARCH_RECENT_LIMIT - our_used
                
                logging.info(f"Search API: Twitter says {actual_remaining}/{search_limit.limit} remaining, we track {our_remaining}/{SEARCH_RECENT_LIMIT} remaining")
                
                # Reconcile if our tracking is off by more than 5%
                if abs(actual_remaining - our_remaining) > (SEARCH_RECENT_LIMIT * 0.05):
                    logging.warning(f"⚠️ Search rate limit tracking discrepancy! Adjusting our tracking to match Twitter's data")
                    # Rebuild our queue with corrected number of timestamps
                    now = datetime.now().timestamp()
                    # Keep most recent items up to the correct count
                    correct_count = SEARCH_RECENT_LIMIT - actual_remaining
                    fresh_queue = deque(sorted(list(bot_state.search_requests))[-correct_count:] if correct_count > 0 else [])
                    bot_state.search_requests = fresh_queue
                    bot_state.save_state()
                
            # Tweet lookup API
            if "statuses" in resources and "/statuses/show/:id" in resources["statuses"]:
                lookup_limit = resources["statuses"]["/statuses/show/:id"]
                actual_remaining = lookup_limit.remaining
                our_used = len(bot_state.tweet_lookup_requests)
                our_remaining = TWEET_LOOKUP_LIMIT - our_used
                
                logging.info(f"Lookup API: Twitter says {actual_remaining}/{lookup_limit.limit} remaining, we track {our_remaining}/{TWEET_LOOKUP_LIMIT} remaining")
                
                if abs(actual_remaining - our_remaining) > (TWEET_LOOKUP_LIMIT * 0.05):
                    logging.warning(f"⚠️ Lookup rate limit tracking discrepancy! Adjusting our tracking to match Twitter's data")
                    now = datetime.now().timestamp()
                    correct_count = TWEET_LOOKUP_LIMIT - actual_remaining
                    fresh_queue = deque(sorted(list(bot_state.tweet_lookup_requests))[-correct_count:] if correct_count > 0 else [])
                    bot_state.tweet_lookup_requests = fresh_queue
                    bot_state.save_state()
            
            # Post API
            if "statuses" in resources and "/statuses/update" in resources["statuses"]:
                post_limit = resources["statuses"]["/statuses/update"]
                actual_remaining = post_limit.remaining
                our_used = len(bot_state.post_tweet_requests)
                our_remaining = POST_TWEET_LIMIT - our_used
                
                logging.info(f"Post API: Twitter says {actual_remaining}/{post_limit.limit} remaining, we track {our_remaining}/{POST_TWEET_LIMIT} remaining")
                
                if abs(actual_remaining - our_remaining) > (POST_TWEET_LIMIT * 0.05):
                    logging.warning(f"⚠️ Post rate limit tracking discrepancy! Adjusting our tracking to match Twitter's data")
                    now = datetime.now().timestamp()
                    correct_count = POST_TWEET_LIMIT - actual_remaining
                    fresh_queue = deque(sorted(list(bot_state.post_tweet_requests))[-correct_count:] if correct_count > 0 else [])
                    bot_state.post_tweet_requests = fresh_queue
                    bot_state.save_state()
    
    except tweepy.errors.TooManyRequests as e:
        logging.warning(f"⚠️ Rate limited while checking rate limits! Backing off...")
        handle_rate_limit_response(429, getattr(e, 'response', {}).headers if hasattr(e, 'response') else None, bot_state, "search")
    except Exception as e:
        logging.warning(f"Failed to check rate limits: {e}")
