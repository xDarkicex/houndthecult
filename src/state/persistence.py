import os
import json
import logging
from datetime import datetime
from collections import deque

class StateManager:
    """Manages saving and loading bot state to/from disk."""
    
    def __init__(self, state_file="data/bot_state.json"):
        """
        Initialize the state manager.
        
        Args:
            state_file (str): Path to the state file.
        """
        self.state_file = state_file
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Initialize files with empty defaults if missing."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        defaults = {
            "reads_today": 0,
            "posts_today": 0,
            "last_reset_date": datetime.now().date().isoformat(),
            "last_check_time": datetime.now().isoformat(),
            "search_timestamps": [],
            "tweet_lookup_timestamps": [],
            "post_tweet_timestamps": []
        }
        
        if not os.path.exists(self.state_file):
            with open(self.state_file, "w") as f:
                json.dump(defaults, f)
    
    def _validate_timestamp(self, ts):
        """
        Validate that a timestamp is a proper number and not too old or in the future.
        
        Args:
            ts: The timestamp to validate.
            
        Returns:
            bool: True if timestamp is valid, False otherwise.
        """
        try:
            ts_float = float(ts)
            now = datetime.now().timestamp()
            # Check if timestamp is more than 24 hours old or in the future
            if ts_float < now - 86400 or ts_float > now + 60:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    def load_state(self, bot_state):
        """
        Load bot state from file.
        
        Args:
            bot_state: The bot state object to populate.
        """
        try:
            with open(self.state_file) as f:
                state = json.load(f)
            
            # Validate numerical values
            bot_state.reads_today = max(0, int(state.get("reads_today", 0)))
            bot_state.posts_today = max(0, int(state.get("posts_today", 0)))
            
            # Validate date fields
            try:
                if isinstance(state.get("last_reset_date"), str):
                    # Validate date format
                    datetime.fromisoformat(state["last_reset_date"])
                    bot_state.last_reset_date = state["last_reset_date"]
                else:
                    bot_state.last_reset_date = datetime.now().date().isoformat()
            except (ValueError, TypeError):
                logging.warning("Invalid last_reset_date in state file. Using current date.")
                bot_state.last_reset_date = datetime.now().date().isoformat()
            
            try:
                if isinstance(state.get("last_check_time"), str):
                    # Validate datetime format
                    datetime.fromisoformat(state["last_check_time"])
                    bot_state.last_check_time = state["last_check_time"]
                else:
                    bot_state.last_check_time = datetime.now().isoformat()
            except (ValueError, TypeError):
                logging.warning("Invalid last_check_time in state file. Using current time.")
                bot_state.last_check_time = datetime.now().isoformat()
            
            # Load rate limit timestamps with validation
            from src.rate_limiting.limiter import WINDOW_SIZE
            now = datetime.now().timestamp()
            cutoff = now - WINDOW_SIZE
            
            # Validate timestamps are proper numbers and within reasonable range
            valid_search_timestamps = [
                ts for ts in state.get("search_timestamps", [])
                if self._validate_timestamp(ts) and ts > cutoff
            ]
            
            valid_lookup_timestamps = [
                ts for ts in state.get("tweet_lookup_timestamps", [])
                if self._validate_timestamp(ts) and ts > cutoff
            ]
            
            valid_post_timestamps = [
                ts for ts in state.get("post_tweet_timestamps", [])
                if self._validate_timestamp(ts) and ts > cutoff
            ]
            
            # Access rate limiter through the bot_state
            bot_state.rate_limiter.search_requests = deque(valid_search_timestamps)
            bot_state.rate_limiter.tweet_lookup_requests = deque(valid_lookup_timestamps)
            bot_state.rate_limiter.post_tweet_requests = deque(valid_post_timestamps)
            
            # Log validation results
            total_search = len(state.get("search_timestamps", []))
            total_lookup = len(state.get("tweet_lookup_timestamps", []))
            total_post = len(state.get("post_tweet_timestamps", []))
            
            if total_search != len(valid_search_timestamps) or total_lookup != len(valid_lookup_timestamps) or total_post != len(valid_post_timestamps):
                logging.warning(f"Some invalid timestamps were filtered: "
                               f"Search {len(valid_search_timestamps)}/{total_search}, "
                               f"Lookup {len(valid_lookup_timestamps)}/{total_lookup}, "
                               f"Post {len(valid_post_timestamps)}/{total_post}")
            
            from src.rate_limiting.limiter import SEARCH_RECENT_LIMIT, TWEET_LOOKUP_LIMIT, POST_TWEET_LIMIT
            logging.info(f"Loaded rate limits: {len(bot_state.rate_limiter.search_requests)}/{SEARCH_RECENT_LIMIT} searches, "
                        f"{len(bot_state.rate_limiter.tweet_lookup_requests)}/{TWEET_LOOKUP_LIMIT} lookups, "
                        f"{len(bot_state.rate_limiter.post_tweet_requests)}/{POST_TWEET_LIMIT} posts in current window")
            
        except Exception as e:
            logging.error(f"Failed loading state: {e}")
            bot_state.rate_limiter.search_requests = deque()
            bot_state.rate_limiter.tweet_lookup_requests = deque()
            bot_state.rate_limiter.post_tweet_requests = deque()
            bot_state.reads_today = 0
            bot_state.posts_today = 0
            bot_state.last_reset_date = datetime.now().date().isoformat()
            bot_state.last_check_time = datetime.now().isoformat()
            logging.warning("Using default state due to loading error")
    
    def save_state(self, bot_state):
        """
        Save bot state to file with backup and atomic operations.
        
        Args:
            bot_state: The bot state object to save.
        """
        try:
            # Cleanup outdated timestamps before saving
            bot_state.rate_limiter._clean_timestamp_queues()
            
            # Create a backup of the current state file
            if os.path.exists(self.state_file):
                backup_file = f"{self.state_file}.bak"
                try:
                    os.replace(self.state_file, backup_file)
                except Exception as e:
                    logging.warning(f"Failed to create backup state file: {e}")
            
            # Write new state to temporary file first, then rename
            with open(f"{self.state_file}.tmp", "w") as f:
                json.dump({
                    "reads_today": bot_state.reads_today,
                    "posts_today": bot_state.posts_today,
                    "last_reset_date": bot_state.last_reset_date,
                    "last_check_time": bot_state.last_check_time,
                    "search_timestamps": list(bot_state.rate_limiter.search_requests),
                    "tweet_lookup_timestamps": list(bot_state.rate_limiter.tweet_lookup_requests),
                    "post_tweet_timestamps": list(bot_state.rate_limiter.post_tweet_requests)
                }, f)
            
            os.replace(f"{self.state_file}.tmp", self.state_file)
            
        except Exception as e:
            logging.error(f"Failed saving state: {e}")
            # Attempt to restore from backup if save failed
            backup_file = f"{self.state_file}.bak"
            if os.path.exists(backup_file):
                try:
                    os.replace(backup_file, self.state_file)
                    logging.info("Restored state file from backup after failed save")
                except Exception:
                    logging.error("Failed to restore state from backup")
