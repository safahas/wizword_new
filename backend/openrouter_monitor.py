import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuotaMonitor:
    def __init__(self):
        self.quota_info = {
            "remaining": None,  # Remaining quota
            "reset_time": None,  # Next reset time
            "last_check": None,  # Last time we checked the quota
            "warning_threshold": 0.1,  # Warn when 10% quota remains
            "critical_threshold": 0.05,  # Critical when 5% quota remains
        }
        
        # Rate limiting
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 3600,
            "request_count": 0,
            "minute_start": time.time(),
            "hour_start": time.time()
        }
    
    def update_quota(self, headers: Dict) -> None:
        """
        Update quota information from API response headers.
        
        Args:
            headers: Response headers from OpenRouter API
        """
        try:
            # Extract quota information
            remaining = headers.get('x-ratelimit-remaining')
            reset_time = headers.get('x-ratelimit-reset')
            
            if remaining is not None:
                self.quota_info["remaining"] = int(remaining)
            
            if reset_time is not None:
                # Convert reset time to datetime
                reset_dt = datetime.fromtimestamp(int(reset_time), timezone.utc)
                self.quota_info["reset_time"] = reset_dt
            
            self.quota_info["last_check"] = datetime.now(timezone.utc)
            
            # Log quota update (debug level)
            logger.debug(
                f"Quota updated - Remaining: {self.quota_info['remaining']}, "
                f"Reset: {self.quota_info['reset_time']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update quota information: {e}")
    
    def check_rate_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Check if we're within rate limits.
        
        Returns:
            (is_allowed, error_message)
        """
        current_time = time.time()
        
        # Reset counters if time windows have passed
        if current_time - self.rate_limits["minute_start"] >= 60:
            self.rate_limits["request_count"] = 0
            self.rate_limits["minute_start"] = current_time
        
        if current_time - self.rate_limits["hour_start"] >= 3600:
            self.rate_limits["request_count"] = 0
            self.rate_limits["hour_start"] = current_time
        
        # Check limits
        if self.rate_limits["request_count"] >= self.rate_limits["requests_per_minute"]:
            return False, "Rate limit exceeded. Please wait a moment."
        
        # Increment counter
        self.rate_limits["request_count"] += 1
        return True, None
    
    def get_quota_warning(self) -> Optional[Dict[str, str]]:
        """
        Get quota warning if thresholds are exceeded.
        
        Returns:
            Warning dict with level and message, or None if no warning
        """
        if self.quota_info["remaining"] is None:
            return None
            
        # Calculate time until reset
        if self.quota_info["reset_time"]:
            now = datetime.now(timezone.utc)
            time_until_reset = self.quota_info["reset_time"] - now
            minutes_until_reset = int(time_until_reset.total_seconds() / 60)
        else:
            minutes_until_reset = "unknown"
        
        # Check critical threshold
        if self.quota_info["remaining"] <= self.quota_info["critical_threshold"]:
            return {
                "level": "error",
                "message": (
                    f"⚠️ Critical: Only {self.quota_info['remaining']} API calls remaining! "
                    f"Quota resets in {minutes_until_reset} minutes. "
                    "Consider using offline mode."
                )
            }
        
        # Check warning threshold
        if self.quota_info["remaining"] <= self.quota_info["warning_threshold"]:
            return {
                "level": "warning",
                "message": (
                    f"⚠️ Warning: {self.quota_info['remaining']} API calls remaining. "
                    f"Quota resets in {minutes_until_reset} minutes."
                )
            }
        
        return None
    
    def get_quota_status(self) -> Dict:
        """
        Get current quota status information.
        
        Returns:
            Dict containing quota status details
        """
        now = datetime.now(timezone.utc)
        
        return {
            "remaining": self.quota_info["remaining"],
            "reset_time": self.quota_info["reset_time"],
            "last_check": self.quota_info["last_check"],
            "time_since_check": (now - self.quota_info["last_check"]).total_seconds() if self.quota_info["last_check"] else None,
            "warning": self.get_quota_warning()
        }

# Global instance
quota_monitor = QuotaMonitor()

def update_quota_from_response(headers: Dict) -> None:
    """
    Update quota information from API response headers.
    
    Args:
        headers: Response headers from OpenRouter API
    """
    quota_monitor.update_quota(headers)

def check_rate_limits() -> Tuple[bool, Optional[str]]:
    """
    Check if we're within rate limits.
    
    Returns:
        (is_allowed, error_message)
    """
    return quota_monitor.check_rate_limits()

def get_quota_warning() -> Optional[Dict[str, str]]:
    """
    Get quota warning if thresholds are exceeded.
    
    Returns:
        Warning dict with level and message, or None if no warning
    """
    return quota_monitor.get_quota_warning()

def get_quota_status() -> Dict:
    """
    Get current quota status information.
    
    Returns:
        Dict containing quota status details
    """
    return quota_monitor.get_quota_status() 