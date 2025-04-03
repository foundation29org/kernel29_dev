"""
Base tracker module for rate limit and price tracking.
"""

import time
from typing import Dict, List, Optional, Tuple, Any, Type, ClassVar, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod





class BaseTracker(ABC):
    """
    Base class for tracking rate limits and pricing.
    
    This class provides the foundation for tracking usage against various limits:
    - Requests per minute (RPM)
    - Requests per day (RPD)
    - Tokens per minute (TPM)
    - Tokens per day (TPD)
    
    It also includes pricing calculations for API usage.
    """
    @abstractmethod
    def __init__(self):
        # Default rate limits
        self.rpm = 0  # Requests per minute
        self.rpd = 0  # Requests per day
        self.tpm = 0  # Tokens per minute
        self.tpd = 0  # Tokens per day
        
        # Default pricing
        self.prompt_price = 0.0  # Per token or as specified by price_scale
        self.completion_price = 0.0  # Per token or as specified by price_scale
        self.price_scale = 'per_million'  # 'per_million', 'per_mil', or 'per_token'
        
        # Usage tracking
        self.requests = []  # List of timestamps
        self.tokens = []  # List of (timestamp, token_count) tuples
        self.success_count = 0
        self.failed_count = 0

    @abstractmethod
    def record_request_by_provider(self):
        """
        Record a request at the provider level.
        
        This allows tracking against provider-wide rate limits.
        """
        pass
    

    def record_request(self, tokens: Optional[int] = None, prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None, success: bool = True):
        """
        Record a request for rate limit tracking.
        
        Args:
            tokens: Number of tokens used (if applicable)
            success: Whether the request was successful
        """
        # Record timestamp for this request
        now = datetime.now()
        self.requests.append(now)
        
        # Record tokens if provided
        if tokens is not None:
            self.tokens.append((now, tokens))
        else:
            if prompt_tokens is not None and completion_tokens is not None:     
                tokens = prompt_tokens + completion_tokens
                self.tokens.append((now, tokens))
            else:
                raise ValueError("Either tokens or prompt_tokens and completion_tokens must be provided")
            
        # Update success/failure count
        if success:
            self.success_count += 1
        else:
            self.failed_count += 1
        
        # Clean up old entries (older than 24 hours)
        self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """Remove entries older than 24 hours."""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        
        # Clean up request timestamps
        self.requests = [ts for ts in self.requests if ts > day_ago]
        
        # Clean up token records
        self.tokens = [(ts, tokens) for ts, tokens in self.tokens if ts > day_ago]
    
    def check_rate_limits(self, buffer_percent: float = 0.9) -> Dict[str, Any]:
        """
        Check if we're approaching rate limits.
        
        Args:
            buffer_percent: When usage is this percentage of limit, consider it near limit
            
        Returns:
            Dict with status information
        """
        # Get current timestamps
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        day_ago = now - timedelta(days=1)
        
        # Count requests in the last minute and day
        requests_last_minute = sum(1 for ts in self.requests if ts > minute_ago)
        requests_last_day = len(self.requests)
        
        # Calculate tokens in the last minute and day
        tokens_last_minute = sum(tokens for ts, tokens in self.tokens if ts > minute_ago)
        tokens_last_day = sum(tokens for ts, tokens in self.tokens)
        
        # Calculate percentages
        rpm_percent = (requests_last_minute / self.rpm) if self.rpm else 0
        rpd_percent = (requests_last_day / self.rpd) if self.rpd else 0
        tpm_percent = (tokens_last_minute / self.tpm) if self.tpm else 0
        tpd_percent = (tokens_last_day / self.tpd) if self.tpd else 0
        
        # Check if we're near any limits
        near_limit = False
        limit_messages = []
        
        if rpm_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"RPM: {requests_last_minute}/{self.rpm} ({rpm_percent:.1%})")
            
        if rpd_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"RPD: {requests_last_day}/{self.rpd} ({rpd_percent:.1%})")
            
        if self.tpm and tpm_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"TPM: {tokens_last_minute}/{self.tpm} ({tpm_percent:.1%})")
            
        if self.tpd and tpd_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"TPD: {tokens_last_day}/{self.tpd} ({tpd_percent:.1%})")
        
        # Calculate time until rate limit resets
        minutes_until_rpm_reset = 1
        minutes_until_tpm_reset = 1
        hours_until_rpd_reset = 24 - (now - day_ago).total_seconds() / 3600
        hours_until_tpd_reset = hours_until_rpd_reset  # Same as RPD reset
        
        result = {
            "status": "near_limit" if near_limit else "ok",
            "rpm": {"current": requests_last_minute, "limit": self.rpm, "percent": rpm_percent},
            "rpd": {"current": requests_last_day, "limit": self.rpd, "percent": rpd_percent},
            "minutes_until_rpm_reset": minutes_until_rpm_reset,
            "hours_until_rpd_reset": hours_until_rpd_reset
        }
        
        if self.tpm:
            result["tpm"] = {"current": tokens_last_minute, "limit": self.tpm, "percent": tpm_percent}
            result["minutes_until_tpm_reset"] = minutes_until_tpm_reset
            
        if self.tpd:
            result["tpd"] = {"current": tokens_last_day, "limit": self.tpd, "percent": tpd_percent}
            result["hours_until_tpd_reset"] = hours_until_tpd_reset
            
        if near_limit:
            result["limit_messages"] = limit_messages
            
        return result
    
    def should_pause(self, buffer_percent: float = 0.9) -> Tuple[bool, Optional[str]]:
        """
        Determine if we should pause processing due to rate limits.
        
        Args:
            buffer_percent: When usage is this percentage of limit, consider it near limit
            
        Returns:
            Tuple of (should_pause, reason)
        """
        limits = self.check_rate_limits(buffer_percent)
        
        if limits["status"] == "near_limit":
            reason = "Rate limits approaching: " + ", ".join(limits.get("limit_messages", []))
            return True, reason
            
        return False, None
    
    def wait_for_reset(self, limit_type: str) -> int:
        """
        Calculate how long to wait for a rate limit to reset.
        
        Args:
            limit_type: Type of limit (rpm, rpd, tpm, tpd)
            
        Returns:
            Seconds to wait
        """
        now = datetime.now()
        
        if limit_type == "rpm" or limit_type == "tpm":
            # Wait until the current minute completes
            seconds_until_next_minute = 60 - now.second
            return seconds_until_next_minute + 5  # Add a small buffer
        
        elif limit_type == "rpd" or limit_type == "tpd":
            # Wait until tomorrow (midnight)
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_tomorrow = (tomorrow - now).total_seconds()
            return int(seconds_until_tomorrow) + 5  # Add a small buffer
        
        return 60  # Default to a minute if unknown
    
    def prompt2price(self, prompt_tokens=0, completion_tokens=0, scale=1, verbose=True):
        """
        Calculate price for prompt and completion tokens based on model's pricing.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            scale: Scale factor for calculating bulk pricing
            verbose: Whether to print price information
            
        Returns:
            Calculated price
        """
        # Determine price per token based on price scale
        if self.price_scale == 'per_million':
            prompt_price_per_token = self.prompt_price / 1_000_000
            completion_price_per_token = self.completion_price / 1_000_000
        elif self.price_scale == 'per_mil':
            prompt_price_per_token = self.prompt_price / 1_000
            completion_price_per_token = self.completion_price / 1_000
        else:  # 'per_token'
            prompt_price_per_token = self.prompt_price
            completion_price_per_token = self.completion_price
        
        # Calculate prices
        prompt_price = prompt_tokens * prompt_price_per_token
        completion_price = completion_tokens * completion_price_per_token
        total_price = (prompt_price + completion_price)
        total_price_scaled = total_price * scale
        
        # Print information if requested
        if verbose:
            if scale == 1:
                print(f"Prompt Price: ${prompt_price:.6f}, Completion Price: ${completion_price:.6f}, Total Price: ${total_price:.6f}")
            else:
                print(f"Price per prompt: ${total_price:.6f}, price per {scale} prompt/s: ${total_price_scaled:.6f}")
        
        return total_price_scaled
