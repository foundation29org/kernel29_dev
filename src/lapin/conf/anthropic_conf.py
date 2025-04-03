# anthropic_configs.py
import os
from .base_conf import BaseModelConfig, register_config

class AnthropicBaseConfig(BaseModelConfig):
    """
    Holds general logic for Anthropic-based models.
    Subclasses must provide the exact 'model' string.
    """
    def __init__(self):
        self.temperature = 0
        self.max_tokens = 2000
        self.model = None  # e.g. "claude-3-opus-20240229"
        self.api_key_env = "ANTHROPIC_API_KEY"

    def get_params(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key": os.getenv(self.api_key_env, "")
        }

    def caller_class(self):
        from .callers.anthropic_caller import AnthropicCaller #relative import, this will work?
        return AnthropicCaller


@register_config
class AnthropicC3OpusConfig(AnthropicBaseConfig):
    """
    For "claude-3-opus-20240229" model.
    """
    @classmethod
    def alias(cls) -> str:
        return "c3opus"

    def __init__(self):
        super().__init__()
        self.model = "claude-3-opus-20240229"
        self.max_tokens = 2000


@register_config
class AnthropicC35SonnetConfig(AnthropicBaseConfig):
    """
    For "claude-3-5-sonnet-20240620" model.
    """
    @classmethod
    def alias(cls) -> str:
        return "c35sonnet"

    def __init__(self):
        super().__init__()
        self.model = "claude-3-5-sonnet-20240620"
        self.max_tokens = 2000
