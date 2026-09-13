"""
rate_limiter.py — Rate limiting configuration untuk LocalPDF Studio.

Menggunakan slowapi dengan in-memory storage untuk mencegah
abuse/DoS pada endpoint processing yang CPU-bound.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory rate limiter (cocok untuk app desktop single-user)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],
    storage_uri="memory://",
)

# Rate limit string constants per tier
RATE_HEAVY = "5/minute"      # CPU-bound processing endpoints
RATE_UPLOAD = "10/minute"    # File upload endpoint
RATE_MUTATION = "10/minute"  # Destructive/modifying endpoints
RATE_GENERAL = "30/minute"   # Default for read endpoints
