"""
Groq model definitions.

This module contains specific model classes for Groq's API.
Each model is decorated with @register_model which automatically adds it
to the MODEL_REGISTRY for lookup by name or alias.
"""

from groq_tracker import GroqTracker, register_model


@register_model("llama3-8b-8192", aliases=["llama3-8b"])
class Llama3_8b(GroqTracker):
    """Llama 3 8B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.20
        self.completion_price = 0.60
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama3-70b-8192", aliases=["llama3-70b"])
class Llama3_70b(GroqTracker):
    """Llama 3 70B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.70
        self.completion_price = 2.10
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("deepseek-r1-distill-llama-70b", aliases=["deepseek-llama-70b"])
class DeepseekLlamaR1(GroqTracker):
    """Deepseek R1 Distill Llama 70B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False.context_window = 32768
        self.is_vision_capable = False


@register_model("deepseek-r1-distill-qwen-32b", aliases=["deepseek-qwen-32b"])
class DeepseekQwenR1(GroqTracker):
    """Deepseek R1 Distill Qwen 32B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False


@register_model("gemma2-9b-it", aliases=["gemma2-9b"])
class Gemma2_9b(GroqTracker):
    """Gemma 2 9B IT model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 15000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-3.1-8b-instant", aliases=["llama-3.1-8b", "llama3.1-8b"])
class Llama3_1_8b(GroqTracker):
    """Llama 3.1 8B Instant model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 6000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-3.2-1b-preview", aliases=["llama-3.2-1b", "llama3.2-1b"])
class Llama3_2_1b(GroqTracker):
    """Llama 3.2 1B Preview model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-3.2-3b-preview", aliases=["llama-3.2-3b", "llama3.2-3b"])
class Llama3_2_3b(GroqTracker):
    """Llama 3.2 3B Preview model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-3.2-11b-vision-preview", aliases=["llama-3.2-11b-vision", "llama3.2-11b-vision"])
class Llama3_2_11b_Vision(GroqTracker):
    """Llama 3.2 11B Vision Preview model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 7000
        self.tpm = 7000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = True


@register_model("llama-3.2-90b-vision-preview", aliases=["llama-3.2-90b-vision", "llama3.2-90b-vision"])
class Llama3_2_90b_Vision(GroqTracker):
    """Llama 3.2 90B Vision Preview model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 15
        self.rpd = 3500
        self.tpm = 7000
        self.tpd = 250000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = True


@register_model("llama-3.3-70b-specdec", aliases=["llama-3.3-70b-specdec", "llama3.3-70b-specdec"])
class Llama3_3_70b_Specdec(GroqTracker):
    """Llama 3.3 70B SpecDec model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = 100000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-3.3-70b-versatile", aliases=["llama-3.3-70b-versatile", "llama3.3-70b-versatile", "llama3-70b-versatile"])
class Llama3_3_70b_Versatile(GroqTracker):
    """Llama 3.3 70B Versatile model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = 100000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("llama-guard-3-8b", aliases=["llama-guard", "llamaguard"])
class LlamaGuard3_8b(GroqTracker):
    """Llama Guard 3 8B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 14400
        self.tpm = 15000
        self.tpd = 500000
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 8192
        self.is_vision_capable = False


@register_model("mistral-saba-24b", aliases=["mistral-saba", "mistral"])
class MistralSaba24b(GroqTracker):
    """Mistral Saba 24B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self.context_window = 32768
        self.is_vision_capable = False


@register_model("qwen-2.5-32b", aliases=["qwen-2.5", "qwen"])
class Qwen2_5_32b(GroqTracker):
    """Qwen 2.5 32B model on Groq."""
    
    def __init__(self):
        super().__init__(self.MODEL_NAME)
        
        # Set rate limits
        self.rpm = 30
        self.rpd = 1000
        self.tpm = 6000
        self.tpd = None
        
        # Set pricing
        self.prompt_price = 0.0
        self.completion_price = 0.0
        self.price_scale = "per_million"
        
        # Set attributes
        self