import time
import logging
import random
import tweepy

from src.utils.logging_setup import setup_logging
from src.utils.timing import human_delay
from src.state import BotState
from src.api.client import initialize_twitter_client
from src.api.endpoints import search_for_mentions, process_mention, check_rate_limits
from src.rate_limiting.backoff import handle_rate_limit_response

def hound_the_cult():
    """
    Main bot function that processes mentions and quotes tweets.
    """
    bot_state = BotState()
    client = initialize_twitter_client()
    
    logging.info("🎯 Bot activated with secure user preferences, state validation, and gradual rate limiting!")
    
    check_interval = 0
    
    while True:
        try:
            # Randomized main loop timing
            human_delay(60, 300)  # 1-5 min between cycles
            
            # Check API limits
            if bot_state.reads_today >= 95:
                logging.warning("⚠️ Approaching monthly read limit. Sleeping 24h.")
                human_delay(86400 - 300, 86400 + 300)  # 24h ±5m
                continue
                
            if bot_state.posts_today >= 490:
                logging.warning("⚠️ Approaching monthly post limit. Sleeping 24h.")
                human_delay(86400 - 300, 86400 + 300)
                continue
                
            # Periodically check actual rate limits from Twitter API
            check_interval += 1
            if check_interval >= 10:  # Check every 10 cycles
                check_rate_limits(client, bot_state)
                check_interval = 0
                
            # Process mentions
            mentions = search_for_mentions(client, bot_state)
            if mentions:
                logging.info(f"🎯 Found {len(mentions)} new mentions!")
                for mention in mentions:
                    process_mention(mention, client, bot_state)
                bot_state.update_check_time()
            
            # Variable sleep with jitter - more natural behavior
            base_sleep = random.randint(3600, 14400)  # 1-4h
            human_delay(base_sleep - 600, base_sleep + 600)  # ±10m
            
        except tweepy.errors.TooManyRequests as e:
            logging.warning(f"⚠️ Rate limited! Cooling off...")
            handle_rate_limit_response(429, getattr(e, 'response', {}).headers if hasattr(e, 'response') else None, 
                                      bot_state, "search")
            human_delay(900, 3600)  # Additional 15-60m cooldown
        except tweepy.errors.Forbidden as e:
            if "suspended" in str(e).lower():
                logging.critical("💀 ACCOUNT SUSPENDED!")
                break
            human_delay(3600, 7200)
        except tweepy.errors.TweepyException as e:
            logging.error(f"💥 Tweepy error: {e}. Restarting in 5-10m...")
            human_delay(300, 600)
        except Exception as e:
            logging.error(f"💥 Unexpected error: {e}. Restarting in 5-10m...")
            human_delay(300, 600)

def main():
    """
    Entry point for the application.
    Sets up logging and handles restarts with exponential backoff.
    """
    setup_logging()
    
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:  # Permanent restart loop with retry limit
        try:
            hound_the_cult()
            # If we exit normally, just restart
            logging.info("Bot exited normally. Restarting in 60s...")
            time.sleep(60)
        except KeyboardInterrupt:
            logging.info("👋 Bot stopped by user.")
            break
        except Exception as e:
            retry_count += 1
            backoff = min(300 * retry_count, 3600)  # Exponential backoff, max 1h
            logging.critical(f"💀 Fatal error: {e}. Retry {retry_count}/{max_retries} in {backoff//60}m...")
            time.sleep(backoff)
    
    if retry_count >= max_retries:
        logging.critical("☠️ Too many fatal errors. Bot shutting down. Manual restart required.")

if __name__ == "__main__":
    main()
