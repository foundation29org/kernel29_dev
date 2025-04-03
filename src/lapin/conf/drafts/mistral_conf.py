# mistral_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config



@register_config
class MistralMoeBigConfig(BaseModelConfig):
    """
    For 'open-mixtral-8x22b' via Mistral direct (not via Bedrock).
    We assume there's a separate caller for direct Mistral usage.
    """
    @classmethod
    def alias(cls) -> str:
        return "mistralmoebig"

    def __init__(self):
        self.model = "open-mixtral-8x22b"
        self.api_key_env = "MISTRAL_API_KEY"
        self.temperature = 0
        self.max_tokens = 800

    def get_params(self) -> dict:
        return {
            "model": self.model,
            "api_key": os.getenv(self.api_key_env, ""),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

    def caller_class(self):
        from llm_calls import MistralDirectCaller
        return MistralDirectCaller
