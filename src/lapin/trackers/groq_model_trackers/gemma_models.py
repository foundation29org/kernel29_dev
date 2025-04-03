"""
Gemma model definitions for Groq's API.

This module contains specific Gemma model classes for Groq's API.
Each model is decorated with @register_model which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from ..groq_tracker import GroqTracker, register_model


@register_model()
class Gemma2_9b(GroqTracker):
    """Gemma 2 9B IT model on Groq."""
    
    MODEL_NAME = "gemma2-9b-it"
    ALIASES = ["gemma2-9b"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 15000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.20
        self.completion_price = 0.20
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 500
