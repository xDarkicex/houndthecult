import logging
import random
import time

def handle_rate_limit_response(status_code=None, headers=None, bot_state=None, request_type=None):
    """
    Handle 429 responses explicitly and adaptively.
    
    Args:
        status_code (int, optional): HTTP status code from the response. 429 indicates rate limiting.
        headers (dict, optional): Response headers, may contain Retry-After information.
        bot_state (object, optional): Bot state object with rate limit tracking.
        request_type (str, optional): Type of request ("search", "lookup", or "post").
        
    Returns:
        None
    """
    if status_code == 429:
        # Check for Retry-After header
        retry_after = None
        if headers and 'Retry-After' in headers:
            try:
                retry_after = int(headers['Retry-After'])
                logging.warning(f"⚠️ Rate limited by Twitter API. Retry-After: {retry_after}s")
                time.sleep(retry_after + random.randint(5, 15))  # Add jitter
                return
            except (ValueError, TypeError):
                pass
        
        # If no valid Retry-After, use escalating backoff
        backoff = 300 + random.randint(0, 60)  # Start with 5m + jitter
        logging.warning(f"⚠️ Rate limited by Twitter API. Backing off for {backoff}s")
        time.sleep(backoff)
    else:
        # General error with gradual backoff based on rate limit usage
        wait_time = 5  # Default minimum wait
        
        if bot_state and request_type:
            additional_delay = bot_state.get_gradual_backoff_delay(request_type)
            wait_time += additional_delay
            
        logging.warning(f"⚠️ Request failed. Waiting {wait_time:.1f}s before retry")
        time.sleep(wait_time)
