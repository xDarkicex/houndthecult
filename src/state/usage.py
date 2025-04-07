import logging
from datetime import datetime

class UsageTracker:
    """
    Tracks API usage for monthly limits.
    """
    def __init__(self):
        """
        Initialize usage tracker.
        """
        self.reads_today = 0
        self.posts_today = 0
        self.last_reset_date = datetime.now().date().isoformat()
        self.last_check_time = datetime.now().isoformat()
    
    def increment_read(self):
        """
        Increment the read counter.
        """
        self.check_reset()
        self.reads_today += 1
        logging.info(f"API Reads this month: {self.reads_today}/100")
    
    def increment_post(self):
        """
        Increment the post counter.
        """
        self.check_reset()
        self.posts_today += 1
        logging.info(f"API Posts this month: {self.posts_today}/500")
    
    def update_check_time(self):
        """
        Update the last check time to now.
        """
        self.last_check_time = datetime.now().isoformat()
    
    def check_reset(self):
        """
        Check if the month has changed and reset counters if needed.
        """
        current_date = datetime.now().date()
        last_date = datetime.fromisoformat(self.last_reset_date).date() if isinstance(self.last_reset_date, str) else self.last_reset_date
        
        if current_date.month != last_date.month:
            logging.info(f"Resetting API usage counters. Previous: {self.reads_today} reads, {self.posts_today} posts")
            self.reads_today = 0
            self.posts_today = 0
            self.last_reset_date = current_date.isoformat()
            return True
        return False
