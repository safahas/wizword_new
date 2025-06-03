"""
Rate limiting module for Word Guess Game.
Implements token bucket algorithm for rate limiting.
"""

import time
import threading
from typing import Dict, Tuple
from collections import defaultdict
from functools import wraps
from backend.monitoring import monitor

class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, fill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            fill_rate: Tokens per second to add
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        
        self.tokens = capacity
        self.last_update = time.time()
        
        self._lock = threading.Lock()
    
    def _add_tokens(self) -> None:
        """Add new tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        new_tokens = elapsed * self.fill_rate
        
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        with self._lock:
            self._add_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self):
        # Per-IP limits
        self.ip_buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=100, fill_rate=2)  # 100 requests per minute
        )
        
        # Global limits
        self.global_bucket = TokenBucket(capacity=1000, fill_rate=20)  # 1000 requests per minute
        
        # Cleanup old IP buckets periodically
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_buckets)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
    
    def _cleanup_old_buckets(self) -> None:
        """Remove IP buckets that haven't been used recently."""
        while True:
            time.sleep(300)  # Run every 5 minutes
            now = time.time()
            
            with threading.Lock():
                for ip, bucket in list(self.ip_buckets.items()):
                    if now - bucket.last_update > 3600:  # Remove after 1 hour of inactivity
                        del self.ip_buckets[ip]
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited.
        
        Args:
            ip: Client IP address
            
        Returns:
            Tuple of (allowed, limits) where limits is a dict with rate limit info
        """
        # Check global limit first
        if not self.global_bucket.consume():
            monitor.track_error('RateLimitExceeded')
            return False, {
                'limit': self.global_bucket.capacity,
                'remaining': int(self.global_bucket.tokens),
                'reset': int(time.time() + (self.global_bucket.capacity - self.global_bucket.tokens) / self.global_bucket.fill_rate)
            }
        
        # Then check per-IP limit
        bucket = self.ip_buckets[ip]
        if not bucket.consume():
            monitor.track_error('RateLimitExceeded')
            return False, {
                'limit': bucket.capacity,
                'remaining': int(bucket.tokens),
                'reset': int(time.time() + (bucket.capacity - bucket.tokens) / bucket.fill_rate)
            }
        
        return True, {
            'limit': bucket.capacity,
            'remaining': int(bucket.tokens),
            'reset': int(time.time() + (bucket.capacity - bucket.tokens) / bucket.fill_rate)
        }

def rate_limit(f):
    """Decorator to apply rate limiting to API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Get client IP
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip is None:
            return jsonify({'error': 'Could not determine client IP'}), 400
        
        # Check rate limit
        allowed, limits = rate_limiter.check_rate_limit(ip)
        
        # Add rate limit headers
        response = f(*args, **kwargs) if allowed else (
            jsonify({'error': 'Rate limit exceeded'}), 429
        )
        
        if isinstance(response, tuple):
            response, status = response
        else:
            status = 200
        
        # Add rate limit headers
        headers = {
            'X-RateLimit-Limit': str(limits['limit']),
            'X-RateLimit-Remaining': str(limits['remaining']),
            'X-RateLimit-Reset': str(limits['reset'])
        }
        
        if isinstance(response, dict):
            return jsonify(response), status, headers
        return response, status, headers
    
    return decorated_function

# Global rate limiter instance
rate_limiter = RateLimiter() 