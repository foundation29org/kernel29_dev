"""
DeepSeek model definitions for Groq's API.

This module contains specific DeepSeek model classes for Groq's API.
Each model is decorated with @register_model which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from ..groq_tracker import GroqTracker, register_model


@register_model()
class DeepseekLlamaR1(GroqTracker):
    """Deepseek R1 Distill Llama 70B model on Groq."""
    
    MODEL_NAME = "deepseek-r1-distill-llama-70b"
    ALIASES = ["deepseek-llama-70b"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.75
        self.completion_price = 0.99
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 275


@register_model()
class DeepseekQwenR1(GroqTracker):
    """Deepseek R1 Distill Qwen 32B model on Groq."""
    
    MODEL_NAME = "deepseek-r1-distill-qwen-32b"
    ALIASES = ["deepseek-qwen-32b"]
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.69
        self.completion_price = 0.69
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 140
