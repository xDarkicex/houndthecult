import logging
import random
from collections import deque
from datetime import datetime

# Rate Limiting Constants
SEARCH_RECENT_LIMIT = 180  # Requests per 15-minute window
TWEET_LOOKUP_LIMIT = 300   # Requests per 15-minute window
POST_TWEET_LIMIT = 200     # Requests per 15-minute window
WINDOW_SIZE = 15 * 60      # 15 minutes in seconds

# Gradual backoff thresholds
LOW_THRESHOLD = 0.5        # 50% of limit
MEDIUM_THRESHOLD = 0.7     # 70% of limit
HIGH_THRESHOLD = 0.9       # 90% of limit

class RateLimiter:
    def __init__(self):
        # Rate limiting with rolling windows
        self.search_requests = deque()
        self.tweet_lookup_requests = deque()
        self.post_tweet_requests = deque()
    
    def _clean_timestamp_queues(self):
        """Remove timestamps outside the current window."""
        now = datetime.now().timestamp()
        cutoff = now - WINDOW_SIZE
        
        # Clean up queues by removing timestamps older than the window
        while self.search_requests and self.search_requests[0] < cutoff:
            self.search_requests.popleft()
            
        while self.tweet_lookup_requests and self.tweet_lookup_requests[0] < cutoff:
            self.tweet_lookup_requests.popleft()
            
        while self.post_tweet_requests and self.post_tweet_requests[0] < cutoff:
            self.post_tweet_requests.popleft()
    
    def get_search_usage_ratio(self):
        """Get current search API usage ratio."""
        self._clean_timestamp_queues()
        return len(self.search_requests) / SEARCH_RECENT_LIMIT
    
    def get_lookup_usage_ratio(self):
        """Get current lookup API usage ratio."""
        self._clean_timestamp_queues()
        return len(self.tweet_lookup_requests) / TWEET_LOOKUP_LIMIT
    
    def get_post_usage_ratio(self):
        """Get current post API usage ratio."""
        self._clean_timestamp_queues()
        return len(self.post_tweet_requests) / POST_TWEET_LIMIT
    
    def can_search(self):
        """Check if we can make a search request within rate limits."""
        return self.get_search_usage_ratio() < 1.0
    
    def can_lookup_tweet(self):
        """Check if we can look up a tweet within rate limits."""
        return self.get_lookup_usage_ratio() < 1.0
    
    def can_post_tweet(self):
        """Check if we can post a tweet within rate limits."""
        return self.get_post_usage_ratio() < 1.0
    
    def get_search_window_reset(self):
        """Get seconds until search window resets."""
        if not self.search_requests:
            return 0
        oldest = self.search_requests[0]
        return max(0, (oldest + WINDOW_SIZE) - datetime.now().timestamp())
    
    def get_lookup_window_reset(self):
        """Get seconds until lookup window resets."""
        if not self.tweet_lookup_requests:
            return 0
        oldest = self.tweet_lookup_requests[0]
        return max(0, (oldest + WINDOW_SIZE) - datetime.now().timestamp())
    
    def get_post_window_reset(self):
        """Get seconds until post window resets."""
        if not self.post_tweet_requests:
            return 0
        oldest = self.post_tweet_requests[0]
        return max(0, (oldest + WINDOW_SIZE) - datetime.now().timestamp())
    
    def get_gradual_backoff_delay(self, request_type):
        """Calculate delay based on current API usage level."""
        usage_ratio = 0
        
        if request_type == "search":
            usage_ratio = self.get_search_usage_ratio()
        elif request_type == "lookup":
            usage_ratio = self.get_lookup_usage_ratio()
        elif request_type == "post":
            usage_ratio = self.get_post_usage_ratio()
        
        # No delay if below low threshold
        if usage_ratio < LOW_THRESHOLD:
            return 0
        
        # Gradual backoff delays
        if usage_ratio < MEDIUM_THRESHOLD:
            # 50-70% utilization: short delay
            return random.uniform(1, 5)
        elif usage_ratio < HIGH_THRESHOLD:
            # 70-90% utilization: medium delay
            return random.uniform(5, 30)
        else:
            # >90% utilization: significant delay
            return random.uniform(30, 120)
    
    def record_search(self):
        """Record a search request."""
        now = datetime.now().timestamp()
        self.search_requests.append(now)
        ratio = self.get_search_usage_ratio()
        level = "LOW"
        if ratio >= HIGH_THRESHOLD:
            level = "HIGH"
        elif ratio >= MEDIUM_THRESHOLD:
            level = "MEDIUM"
        elif ratio >= LOW_THRESHOLD:
            level = "MODERATE"
        logging.info(f"Search request: {len(self.search_requests)}/{SEARCH_RECENT_LIMIT} in window ({level}: {ratio:.2%})")
    
    def record_lookup(self):
        """Record a tweet lookup request."""
        now = datetime.now().timestamp()
        self.tweet_lookup_requests.append(now)
        ratio = self.get_lookup_usage_ratio()
        level = "LOW"
        if ratio >= HIGH_THRESHOLD:
            level = "HIGH"
        elif ratio >= MEDIUM_THRESHOLD:
            level = "MEDIUM"
        elif ratio >= LOW_THRESHOLD:
            level = "MODERATE"
        logging.info(f"Lookup request: {len(self.tweet_lookup_requests)}/{TWEET_LOOKUP_LIMIT} in window ({level}: {ratio:.2%})")
    
    def record_post(self):
        """Record a post request."""
        now = datetime.now().timestamp()
        self.post_tweet_requests.append(now)
        ratio = self.get_post_usage_ratio()
        level = "LOW"
        if ratio >= HIGH_THRESHOLD:
            level = "HIGH"
        elif ratio >= MEDIUM_THRESHOLD:
            level = "MEDIUM"
        elif ratio >= LOW_THRESHOLD:
            level = "MODERATE"
        logging.info(f"Post request: {len(self.post_tweet_requests)}/{POST_TWEET_LIMIT} in window ({level}: {ratio:.2%})")
