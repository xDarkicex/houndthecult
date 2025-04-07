# This file makes the api directory a Python package

from .client import initialize_twitter_client
from .endpoints import search_for_mentions, process_mention, check_rate_limits

# Expose main API functions at the package level
__all__ = [
    'initialize_twitter_client',
    'search_for_mentions',
    'process_mention',
    'check_rate_limits'
]
