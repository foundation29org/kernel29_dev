# conf/groq_conf.py
import os
from .base_conf import BaseModelConfig, register_config

class GroqBaseConfig(BaseModelConfig):
    """
    Holds general logic for Groq-based models.
    Subclasses must provide the exact 'model' string.
    """
    def __init__(self):
        # Default parameter values
        self.temperature = 0.7
        self.max_tokens = 1024
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.model = None  # e.g. "mixtral-8x7b-32768"
        self.api_key_env = "GROQ_API_KEY"
        self.system_message = "You are a helpful assistant."
        self.stream = False
        self.stop = None
        self.response_format = None
        self.seed = None
        self.tools = None
        self.tool_choice = None
        if not os.getenv("GROQ_API_KEY"):
            print("Error: GROQ_API_KEY environment variable is not set.")
            print("Please set it using: export GROQ_API_KEY=your-api-key")
            

    def get_params(self) -> dict:
        """
        Returns a dictionary of parameters for the Groq API call.
        Simply returns all parameters without filtering None values,
        as the caller will handle that filtering.
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "api_key": os.getenv(self.api_key_env, ""),
            "system_message": self.system_message,
            "stream": self.stream,
            "stop": self.stop,
            "response_format": self.response_format,
            "seed": self.seed,
            "tools": self.tools,
            "tool_choice": self.tool_choice
        }

    def caller_class_backward(self):
        """
        Returns the appropriate caller class for Groq models.
        """
        # print ("here")
        from ..callers.groq_caller import GroqCaller
        return GroqCaller

    def caller_class(self):
        """
        Returns the appropriate caller class for Groq models.
        """
        # print ("here")
        from ..callers.groq.sync_groq_caller import SyncGroqCaller
        return SyncGroqCaller


    def async_caller_class(self):
        """
        Returns the appropriate async caller class for Groq models.
        """
        from ..callers.groq.async_groq_caller import AsyncGroqCaller
        return AsyncGroqCaller


    def tracker_class(self):
        """
        Returns the appropriate tracker class for Groq models.
        """
        from ..trackers.groq_tracker import GroqTracker
        return GroqTracker

        
    def enable_json_mode(self):
        """
        Configures the model to return responses in JSON format.
        """
        self.response_format = {"type": "json_object"}
        return self
    
    def set_system_message(self, message: str):
        """
        Sets a custom system message.
        """
        self.system_message = message
        return self
    
    def enable_streaming(self, enabled=True):
        """
        Enables or disables streaming mode.
        """
        self.stream = enabled
        return self


# Llama 3 Family Models

@register_config
class LlamaThreeThreeSeventyBVersatileConfig(GroqBaseConfig):
    """
    For "llama-3.3-70b-versatile" model.
    128K context window, 32,768 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama3-70b-versatile"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 32768


@register_config
class LlamaThreeOneEightBInstantConfig(GroqBaseConfig):
    """
    For "llama-3.1-8b-instant" model.
    128K context window, 8,192 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama3-8b-instant"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.1-8b-instant"
        self.max_tokens = 8192


@register_config
class LlamaGuardThreeEightBConfig(GroqBaseConfig):
    """
    For "llama-guard-3-8b" model, specialized for content moderation.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-guard-3-8b"

    def __init__(self):
        super().__init__()
        self.model = "llama-guard-3-8b"
        self.max_tokens = 4096
        self.system_message = "You are a content policy assistant. Analyze the content for policy violations."


@register_config
class LlamaThreeSeventyBConfig(GroqBaseConfig):
    """
    For "llama3-70b-8192" model.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama3-70b"

    def __init__(self):
        super().__init__()
        self.model = "llama3-70b-8192"
        self.max_tokens = 8192


@register_config
class LlamaThreeEightBConfig(GroqBaseConfig):
    """
    For "llama3-8b-8192" model.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama3-8b"

    def __init__(self):
        super().__init__()
        self.model = "llama3-8b-8192"
        self.max_tokens = 8192
        self.response_format = {"type": "json_object"}


# Mixtral Model

@register_config
class MixtralEightXSevenBConfig(GroqBaseConfig):
    """
    For "mixtral-8x7b-32768" model.
    32,768 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "mixtral-8x7b"

    def __init__(self):
        super().__init__()
        self.model = "mixtral-8x7b-32768"
        self.max_tokens = 32768


# Gemma Model

@register_config
class GemmaTwoNineBConfig(GroqBaseConfig):
    """
    For "gemma2-9b-it" model.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "gemma2-9b"

    def __init__(self):
        super().__init__()
        self.model = "gemma2-9b-it"
        self.max_tokens = 8192


# Preview Models

@register_config
class QwenQwqThirtyTwoBConfig(GroqBaseConfig):
    """
    For "qwen-qwq-32b" preview model.
    128K context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "qwen-qwq-32b"

    def __init__(self):
        super().__init__()
        self.model = "qwen-qwq-32b"
        self.max_tokens = 16384


@register_config
class MistralSabaTwentyFourBConfig(GroqBaseConfig):
    """
    For "mistral-saba-24b" preview model.
    32K context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "mistral-saba-24b"

    def __init__(self):
        super().__init__()
        self.model = "mistral-saba-24b"
        self.max_tokens = 32768


@register_config
class QwenTwoPointFiveCoderThirtyTwoBConfig(GroqBaseConfig):
    """
    For "qwen-2.5-coder-32b" preview model specialized for coding.
    128K context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "qwen-coder-32b"

    def __init__(self):
        super().__init__()
        self.model = "qwen-2.5-coder-32b"
        self.max_tokens = 16384
        self.system_message = "You are a helpful coding assistant. Provide clear and efficient code."


@register_config
class QwenTwoPointFiveThirtyTwoBConfig(GroqBaseConfig):
    """
    For "qwen-2.5-32b" preview model.
    128K context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "qwen-2.5-32b"

    def __init__(self):
        super().__init__()
        self.model = "qwen-2.5-32b"
        self.max_tokens = 16384


@register_config
class DeepseekR1DistillQwenThirtyTwoBConfig(GroqBaseConfig):
    """
    For "deepseek-r1-distill-qwen-32b" preview model.
    128K context window, 16,384 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "deepseek-qwen-32b"

    def __init__(self):
        super().__init__()
        self.model = "deepseek-r1-distill-qwen-32b"
        self.max_tokens = 16384


@register_config
class DeepseekR1DistillLlamaSeventyBSpecDecConfig(GroqBaseConfig):
    """
    For "deepseek-r1-distill-llama-70b-specdec" preview model.
    128K context window, 16,384 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "deepseek-llama-70b-specdec"

    def __init__(self):
        super().__init__()
        self.model = "deepseek-r1-distill-llama-70b-specdec"
        self.max_tokens = 16384


@register_config
class DeepseekR1DistillLlamaSeventyBConfig(GroqBaseConfig):
    """
    For "deepseek-r1-distill-llama-70b" preview model.
    128K context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "deepseek-llama-70b"

    def __init__(self):
        super().__init__()
        self.model = "deepseek-r1-distill-llama-70b"
        self.max_tokens = 16384


@register_config
class LlamaThreePointThreeSeventyBSpecDecConfig(GroqBaseConfig):
    """
    For "llama-3.3-70b-specdec" preview model.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-3.3-70b-specdec"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.3-70b-specdec"
        self.max_tokens = 8192


@register_config
class LlamaThreePointTwoOneBePreviewConfig(GroqBaseConfig):
    """
    For "llama-3.2-1b-preview" model.
    128K context window, 8,192 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-3.2-1b"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.2-1b-preview"
        self.max_tokens = 8192


@register_config
class LlamaThreePointTwoThreeBPreviewConfig(GroqBaseConfig):
    """
    For "llama-3.2-3b-preview" model.
    128K context window, 8,192 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-3.2-3b"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.2-3b-preview"
        self.max_tokens = 8192


@register_config
class LlamaThreePointTwoElevenBVisionPreviewConfig(GroqBaseConfig):
    """
    For "llama-3.2-11b-vision-preview" model.
    128K context window, 8,192 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-3.2-11b-vision"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.2-11b-vision-preview"
        self.max_tokens = 8192
        self.system_message = "You are a helpful vision-language assistant capable of understanding both text and images."


@register_config
class LlamaThreePointTwoNinetyBVisionPreviewConfig(GroqBaseConfig):
    """
    For "llama-3.2-90b-vision-preview" model.
    128K context window, 8,192 max completion tokens.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama-3.2-90b-vision"

    def __init__(self):
        super().__init__()
        self.model = "llama-3.2-90b-vision-preview"
        self.max_tokens = 8192
        self.system_message = "You are a helpful vision-language assistant capable of understanding both text and images."


# Factory functions to create model instances with specific configurations

def create_groq_model(model_alias: str, **kwargs):
    """
    Factory function to create and configure a Groq model with custom parameters.
    
    Args:
        model_alias: The alias of the model to create
        **kwargs: Additional parameters to override the model's default configuration
        
    Returns:
        A configured model configuration object
        
    Raises:
        ValueError: If the model alias is not found
    """
    if model_alias not in CONFIG_REGISTRY:
        raise ValueError(f"Model alias '{model_alias}' not found. Available models: {', '.join(CONFIG_REGISTRY.keys())}")
    
    config_cls = CONFIG_REGISTRY[model_alias]
    config_obj = config_cls()
    
    # Apply custom parameters
    for key, value in kwargs.items():
        if hasattr(config_obj, key):
            setattr(config_obj, key, value)
    
    return config_obj
