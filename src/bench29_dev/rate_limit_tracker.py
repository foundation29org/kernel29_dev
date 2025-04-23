"""
Rate limit tracking and management utilities.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

class RateLimitTracker:
    """
    Tracks rate limits for different models and providers.
    
    Monitors usage against limits for:
    - Requests per minute (RPM)
    - Requests per day (RPD)
    - Tokens per minute (TPM)
    - Tokens per day (TPD)
    """
    
    def __init__(self):
        # Store rate limits by model
        self.rate_limits = {
            # Example format:
            # "model_alias": {
            #     "rpm": 30,        # Requests per minute
            #     "rpd": 14400,     # Requests per day 
            #     "tpm": 6000,      # Tokens per minute
            #     "tpd": 500000,    # Tokens per day
            # }
        }
        
        # Track usage
        self.usage = {}
        self.usage_history = {}
        
        # Initialize with some known models
        self._initialize_known_models()
    
    def _initialize_known_models(self):
        """Initialize rate limits for known models."""
        # Groq models
        groq_models = {
            "deepseek-r1-distill-llama-70b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
            "deepseek-r1-distill-qwen-32b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
            "gemma2-9b-it": {"rpm": 30, "rpd": 14400, "tpm": 15000, "tpd": 500000},
            "llama-3.1-8b-instant": {"rpm": 30, "rpd": 14400, "tpm": 6000, "tpd": 500000},
            "llama-3.2-1b-preview": {"rpm": 30, "rpd": 7000, "tpm": 7000, "tpd": 500000},
            "llama-3.2-3b-preview": {"rpm": 30, "rpd": 7000, "tpm": 7000, "tpd": 500000},
            "llama-3.2-11b-vision-preview": {"rpm": 30, "rpd": 7000, "tpm": 7000, "tpd": 500000},
            "llama-3.2-90b-vision-preview": {"rpm": 15, "rpd": 3500, "tpm": 7000, "tpd": 250000},
            "llama-3.3-70b-specdec": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": 100000},
            "llama-3.3-70b-versatile": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": 100000},
            "llama-guard-3-8b": {"rpm": 30, "rpd": 14400, "tpm": 15000, "tpd": 500000},
            "llama3-8b-8192": {"rpm": 30, "rpd": 14400, "tpm": 6000, "tpd": 500000},
            "llama3-70b-8192": {"rpm": 30, "rpd": 14400, "tpm": 6000, "tpd": 500000},
            "mistral-saba-24b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
            "qwen-2.5-32b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
            "qwen-2.5-coder-32b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
            "qwen-qwq-32b": {"rpm": 30, "rpd": 1000, "tpm": 6000, "tpd": None},
        }
        
        # Add all models to rate limits
        for model, limits in groq_models.items():
            self.rate_limits[model] = limits
            self.usage[model] = {
                "requests": [],
                "tokens": []
            }
            self.usage_history[model] = {
                "failed_count": 0,
                "success_count": 0
            }
    
    def add_model_limits(self, model_alias: str, rpm: int, rpd: int, tpm: Optional[int], tpd: Optional[int]):
        """
        Add or update rate limits for a model.
        
        Args:
            model_alias: The model alias
            rpm: Requests per minute
            rpd: Requests per day
            tpm: Tokens per minute (None if not applicable)
            tpd: Tokens per day (None if not applicable)
        """
        self.rate_limits[model_alias] = {
            "rpm": rpm,
            "rpd": rpd,
            "tpm": tpm,
            "tpd": tpd
        }
        
        # Initialize usage tracking if needed
        if model_alias not in self.usage:
            self.usage[model_alias] = {
                "requests": [],
                "tokens": []
            }
            
        if model_alias not in self.usage_history:
            self.usage_history[model_alias] = {
                "failed_count": 0,
                "success_count": 0
            }
    
    def record_request(self, model_alias: str, tokens: Optional[int] = None, success: bool = True):
        """
        Record a request for rate limit tracking.
        
        Args:
            model_alias: The model alias
            tokens: Number of tokens used (if applicable)
            success: Whether the request was successful
        """
        if model_alias not in self.usage:
            # Initialize if this is a new model
            self.usage[model_alias] = {
                "requests": [],
                "tokens": []
            }
            self.usage_history[model_alias] = {
                "failed_count": 0,
                "success_count": 0
            }
        
        # Record timestamp for this request
        now = datetime.now()
        self.usage[model_alias]["requests"].append(now)
        
        # Record tokens if provided
        if tokens is not None:
            self.usage[model_alias]["tokens"].append((now, tokens))
        
        # Update success/failure count
        if success:
            self.usage_history[model_alias]["success_count"] += 1
        else:
            self.usage_history[model_alias]["failed_count"] += 1
        
        # Clean up old entries (older than 24 hours)
        self._cleanup_old_entries(model_alias)
    
    def _cleanup_old_entries(self, model_alias: str):
        """
        Remove entries older than 24 hours.
        
        Args:
            model_alias: The model alias
        """
        if model_alias not in self.usage:
            return
            
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        minute_ago = now - timedelta(minutes=1)
        
        # Clean up request timestamps
        self.usage[model_alias]["requests"] = [
            ts for ts in self.usage[model_alias]["requests"]
            if ts > day_ago
        ]
        
        # Clean up token records
        self.usage[model_alias]["tokens"] = [
            (ts, tokens) for ts, tokens in self.usage[model_alias]["tokens"]
            if ts > day_ago
        ]
    
    def check_rate_limits(self, model_alias: str, buffer_percent: float = 0.9) -> Dict[str, Any]:
        """
        Check if we're approaching rate limits for a model.
        
        Args:
            model_alias: The model alias
            buffer_percent: When usage is this percentage of limit, consider it near limit
            
        Returns:
            Dict with status information
        """
        if model_alias not in self.rate_limits:
            return {"status": "unknown", "message": f"No rate limits defined for {model_alias}"}
        
        if model_alias not in self.usage:
            return {"status": "ok", "message": "No usage recorded yet"}
        
        # Get current timestamps
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        day_ago = now - timedelta(days=1)
        
        # Count requests in the last minute and day
        requests_last_minute = sum(1 for ts in self.usage[model_alias]["requests"] if ts > minute_ago)
        requests_last_day = len(self.usage[model_alias]["requests"])
        
        # Calculate tokens in the last minute and day
        tokens_last_minute = sum(tokens for ts, tokens in self.usage[model_alias]["tokens"] if ts > minute_ago)
        tokens_last_day = sum(tokens for ts, tokens in self.usage[model_alias]["tokens"])
        
        # Get limits
        rpm_limit = self.rate_limits[model_alias]["rpm"]
        rpd_limit = self.rate_limits[model_alias]["rpd"]
        tpm_limit = self.rate_limits[model_alias]["tpm"]
        tpd_limit = self.rate_limits[model_alias]["tpd"]
        
        # Calculate percentages
        rpm_percent = (requests_last_minute / rpm_limit) if rpm_limit else 0
        rpd_percent = (requests_last_day / rpd_limit) if rpd_limit else 0
        tpm_percent = (tokens_last_minute / tpm_limit) if tpm_limit else 0
        tpd_percent = (tokens_last_day / tpd_limit) if tpd_limit else 0
        
        # Check if we're near any limits
        near_limit = False
        limit_messages = []
        
        if rpm_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"RPM: {requests_last_minute}/{rpm_limit} ({rpm_percent:.1%})")
            
        if rpd_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"RPD: {requests_last_day}/{rpd_limit} ({rpd_percent:.1%})")
            
        if tpm_limit and tpm_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"TPM: {tokens_last_minute}/{tpm_limit} ({tpm_percent:.1%})")
            
        if tpd_limit and tpd_percent >= buffer_percent:
            near_limit = True
            limit_messages.append(f"TPD: {tokens_last_day}/{tpd_limit} ({tpd_percent:.1%})")
        
        # Calculate time until rate limit resets
        minutes_until_rpm_reset = 1
        minutes_until_tpm_reset = 1
        hours_until_rpd_reset = 24 - (now - day_ago).total_seconds() / 3600
        hours_until_tpd_reset = hours_until_rpd_reset  # Same as RPD reset
        
        result = {
            "status": "near_limit" if near_limit else "ok",
            "rpm": {"current": requests_last_minute, "limit": rpm_limit, "percent": rpm_percent},
            "rpd": {"current": requests_last_day, "limit": rpd_limit, "percent": rpd_percent},
            "minutes_until_rpm_reset": minutes_until_rpm_reset,
            "hours_until_rpd_reset": hours_until_rpd_reset
        }
        
        if tpm_limit:
            result["tpm"] = {"current": tokens_last_minute, "limit": tpm_limit, "percent": tpm_percent}
            result["minutes_until_tpm_reset"] = minutes_until_tpm_reset
            
        if tpd_limit:
            result["tpd"] = {"current": tokens_last_day, "limit": tpd_limit, "percent": tpd_percent}
            result["hours_until_tpd_reset"] = hours_until_tpd_reset
            
        if near_limit:
            result["limit_messages"] = limit_messages
            
        return result
    
    def should_pause(self, model_alias: str, buffer_percent: float = 0.9) -> Tuple[bool, Optional[str]]:
        """
        Determine if we should pause processing due to rate limits.
        
        Args:
            model_alias: The model alias
            buffer_percent: When usage is this percentage of limit, consider it near limit
            
        Returns:
            Tuple of (should_pause, reason)
        """
        limits = self.check_rate_limits(model_alias, buffer_percent)
        
        if limits["status"] == "near_limit":
            reason = "Rate limits approaching: " + ", ".join(limits.get("limit_messages", []))
            return True, reason
            
        return False, None
    
    def wait_for_reset(self, model_alias: str, limit_type: str) -> int:
        """
        Calculate how long to wait for a rate limit to reset.
        
        Args:
            model_alias: The model alias
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
