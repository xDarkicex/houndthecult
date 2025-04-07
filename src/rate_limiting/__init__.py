# This file makes the rate_limiting directory a Python package

from .limiter import (
    RateLimiter,
    SEARCH_RECENT_LIMIT,
    TWEET_LOOKUP_LIMIT,
    POST_TWEET_LIMIT,
    WINDOW_SIZE,
    LOW_THRESHOLD,
    MEDIUM_THRESHOLD,
    HIGH_THRESHOLD
)

from .backoff import handle_rate_limit_response

# Expose key components at the package level
__all__ = [
    'RateLimiter',
    'handle_rate_limit_response',
    'SEARCH_RECENT_LIMIT',
    'TWEET_LOOKUP_LIMIT',
    'POST_TWEET_LIMIT',
    'WINDOW_SIZE',
    'LOW_THRESHOLD',
    'MEDIUM_THRESHOLD',
    'HIGH_THRESHOLD'
]
