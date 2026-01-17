"""Rate limiting configuration using slowapi with Redis backend."""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.config import settings


def get_key_func(request):
    """
    Get rate limit key from request.
    Uses IP address for unauthenticated requests.
    Could be extended to use user ID for authenticated requests.
    """
    return get_remote_address(request)


# Disable rate limiting during tests
_testing = os.environ.get("TESTING", "").lower() == "true"

# Create limiter with Redis storage for distributed rate limiting
limiter = Limiter(
    key_func=get_key_func,
    storage_uri=settings.redis_url,
    default_limits=["100/minute"],  # Default: 100 requests per minute
    enabled=not _testing,  # Disabled in test mode
)


# Rate limit configurations for different endpoint types
class RateLimits:
    """Rate limit strings for different endpoint categories."""

    # Auth endpoints - strict to prevent brute force
    LOGIN = "5/minute"  # 5 login attempts per minute
    REGISTER = "3/minute"  # 3 registrations per minute per IP

    # Search endpoints - moderate (external API calls)
    SEARCH = "30/minute"  # 30 searches per minute

    # Write operations - moderate
    RATING = "60/minute"  # 60 ratings per minute
    COMPARISON = "60/minute"  # 60 comparisons per minute

    # Read operations - generous
    READ = "100/minute"  # 100 reads per minute

    # Recommendations - moderate (compute intensive)
    RECOMMENDATIONS = "20/minute"  # 20 recommendation requests per minute
