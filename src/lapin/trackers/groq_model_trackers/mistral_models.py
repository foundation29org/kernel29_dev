"""
Mistral model definitions for Groq's API.

This module contains specific Mistral and Mixtral model classes for Groq's API.
Each model is decorated with @register_model which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from ..groq_tracker import GroqTracker, register_model


@register_model()
class MistralSaba24b(GroqTracker):
    """Mistral Saba 24B model on Groq."""
    
    MODEL_NAME = "mistral-saba-24b"
    ALIASES = ["mistral-saba", "mistral"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.79
        self.completion_price = 0.79
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 330


@register_model()
class Mixtral8x7B(GroqTracker):
    """Mixtral 8x7B Instruct 32k model on Groq."""
    
    MODEL_NAME = "mixtral-8x7b-instruct-32k"
    ALIASES = ["mixtral-8x7b", "mixtral"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.24
        self.completion_price = 0.24
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 575
