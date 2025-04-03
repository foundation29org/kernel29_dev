# openai_chat_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config

class OpenAIChatBase(BaseModelConfig):
    """
    For direct OpenAI Chat API (non-Azure).
    We can wrap LangChain's ChatOpenAI as well.
    """
    def __init__(self):
        self.model_name = None
        self.openai_api_key_env = "OPENAI_API_KEY"
        self.temperature = 0
        self.max_tokens = 800

    def get_params(self) -> dict:
        return {
            "model_name": self.model_name,
            "openai_api_key": os.getenv(self.openai_api_key_env, ""),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

    def caller_class(self):
        from llm_calls import OpenAIChatCaller
        return OpenAIChatCaller


@register_config
class GPT4Turbo1106Config(OpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "gpt4turbo1106"

    def __init__(self):
        super().__init__()
        self.model_name = "gpt-4-1106-preview"
        self.temperature = 0
        self.max_tokens = 800


@register_config
class GPT4Turbo0409Config(OpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "gpt4turbo0409"

    def __init__(self):
        super().__init__()
        self.model_name = "gpt-4-turbo-2024-04-09"
        self.temperature = 0
        self.max_tokens = 800


@register_config
class GPT4OConfig(OpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "gpt4o"

    def __init__(self):
        super().__init__()
        self.model_name = "gpt-4o"
        self.temperature = 0
        self.max_tokens = 800


@register_config
class O1MiniConfig(OpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "o1_mini"

    def __init__(self):
        super().__init__()
        self.model_name = "o1-mini"
        self.temperature = 1
        self.max_tokens = 800


@register_config
class O1PreviewConfig(OpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "o1_preview"

    def __init__(self):
        super().__init__()
        self.model_name = "o1-preview"
        self.temperature = 1
        self.max_tokens = 800
