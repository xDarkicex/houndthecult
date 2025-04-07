import time
import random

def human_delay(min_sec: float, max_sec: float):
    """
    Randomized delay to mimic human behavior.
    
    Args:
        min_sec (float): Minimum delay in seconds.
        max_sec (float): Maximum delay in seconds.
    
    Returns:
        None
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
