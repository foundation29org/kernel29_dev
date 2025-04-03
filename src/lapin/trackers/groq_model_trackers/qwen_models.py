"""
Qwen model definitions for Groq's API.

This module contains specific Qwen model classes for Groq's API.
Each model is decorated with @register_model which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from ..groq_tracker import GroqTracker, register_model


@register_model()
class Qwen2_5_32b(GroqTracker):
    """Qwen 2.5 32B model on Groq."""
    
    MODEL_NAME = "qwen-2.5-32b"
    ALIASES = ["qwen-2.5", "qwen"]
    
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
        self.tokens_per_second = 200


@register_model()
class Qwen2_5_Coder_32b(GroqTracker):
    """Qwen 2.5 Coder 32B model on Groq."""
    
    MODEL_NAME = "qwen-2.5-coder-32b"
    ALIASES = ["qwen-2.5-coder", "qwen-coder"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits - using similar models as reference
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
        self.tokens_per_second = 390


@register_model()
class QwenQwQ_32b(GroqTracker):
    """Qwen QwQ 32B (Preview) model on Groq."""
    
    MODEL_NAME = "qwen-qwq-32b"
    ALIASES = ["qwen-qwq"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits - using similar models as reference
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.29
        self.completion_price = 0.39
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 400
