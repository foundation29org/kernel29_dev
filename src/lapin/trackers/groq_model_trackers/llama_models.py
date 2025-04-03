"""
Llama model definitions for Groq's API.

This module contains specific Llama model classes for Groq's API.
Each model is decorated with @register_tracker which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from ..groq_tracker import GroqTracker, register_tracker


@register_tracker
class Llama3_8b(GroqTracker):
    """Llama 3 8B model on Groq."""
    
    def __init__(self):
        self.model_name = "llama3-8b-8192"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.05
        self.completion_price = 0.08
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 1250


@register_tracker
class Llama3_70b(GroqTracker):
    """Llama 3 70B model on Groq."""
    
    def __init__(self):
        self.model_name = "llama3-70b-8192"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.59
        self.completion_price = 0.79
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 330


@register_tracker
class Llama3_1_8b(GroqTracker):
    """Llama 3.1 8B Instant model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.1-8b-instant"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.05
        self.completion_price = 0.08
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 750


@register_tracker
class Llama3_2_1b(GroqTracker):
    """Llama 3.2 1B Preview model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.2-1b-preview"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.04
        self.completion_price = 0.04
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 3100


@register_tracker
class Llama3_2_3b(GroqTracker):
    """Llama 3.2 3B Preview model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.2-3b-preview"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.06
        self.completion_price = 0.06
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 1600


@register_tracker
class Llama3_2_11b_Vision(GroqTracker):
    """Llama 3.2 11B Vision Preview model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.2-11b-vision-preview"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        # Note: Pricing not provided in the input data, keeping at 0.0
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = True


@register_tracker
class Llama3_2_90b_Vision(GroqTracker):
    """Llama 3.2 90B Vision Preview model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.2-90b-vision-preview"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 15
        self.rpd = 3500
        self.tpm = 7000
        self.tpd = 250000
        
        # Set pricing
        # Note: Pricing not provided in the input data, keeping at 0.0
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = True


@register_tracker
class Llama3_3_70b_Specdec(GroqTracker):
    """Llama 3.3 70B SpecDec model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.3-70b-specdec"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = 100000
        
        # Set pricing
        self.prompt_price = 0.59
        self.completion_price = 0.99
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 1600


@register_tracker
class Llama3_3_70b_Versatile(GroqTracker):
    """Llama 3.3 70B Versatile model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-3.3-70b-versatile"
        super().__init__(self.model_name)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = 100000
        
        # Set pricing
        self.prompt_price = 0.59
        self.completion_price = 0.79
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False
        
        # Add token speed
        self.tokens_per_second = 275


@register_tracker
class LlamaGuard3_8b(GroqTracker):
    """Llama Guard 3 8B model on Groq."""
    
    def __init__(self):
        self.model_name = "llama-guard-3-8b"
        super().__init__(self.model_name)
        
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
        self.tokens_per_second = 765
