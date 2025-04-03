# azure_openai_chat_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config

class AzureOpenAIChatBase(BaseModelConfig):
    """
    For Azure-hosted OpenAI models, such as GPT-4 or GPT-3.5,
    using an AzureChatOpenAI approach.
    """
    def __init__(self):
        self.azure_deployment = None
        self.openai_api_version_env = "OPENAI_API_VERSION"
        self.temperature = 0
        self.max_tokens = 800
        self.additional_kwargs = {}

    def get_params(self) -> dict:
        return {
            "azure_deployment": self.azure_deployment,
            "openai_api_version": os.getenv(self.openai_api_version_env, ""),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "additional_kwargs": self.additional_kwargs
        }

    def caller_class(self):
        from llm_calls import AzureOpenAIChatCaller
        return AzureOpenAIChatCaller


@register_config
class GPT4_0613AzureConfig(AzureOpenAIChatBase):
    @classmethod
    def alias(cls) -> str:
        return "gpt4_0613azure"

    def __init__(self):
        super().__init__()
        self.azure_deployment = os.getenv("DEPLOYMENT_NAME")  # e.g. "gpt4-0613"
        self.temperature = 0
        self.max_tokens = 2000
        self.additional_kwargs = {"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0}


@register_config
class GPT4TurboAzureConfig(AzureOpenAIChatBase):
    """
    This references 'gpt4turboazure' from the snippet:
      azure_deployment = "nav29turbo",
      temperature = 0,
      max_tokens = 800,
      additional_kwargs = {"top_p": 1, ...}
    """
    @classmethod
    def alias(cls) -> str:
        return "gpt4turboazure"

    def __init__(self):
        super().__init__()
        self.azure_deployment = "nav29turbo"
        self.temperature = 0
        self.max_tokens = 800
        self.additional_kwargs = {"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0}
