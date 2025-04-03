# azure_llama_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config

class AzureBaseConfig(BaseModelConfig):
    """
    Base for all models on Azure ML Endpoint.
    """
    def __init__(self):
        self.endpoint_url_env = "AZURE_ML_ENDPOINT"
        self.api_key_env = "AZURE_ML_API_KEY"
        self.deployment_name = None
        self.temperature = 0
        self.max_new_tokens = 800

    def get_params(self) -> dict:
        return {
            "endpoint_url": os.getenv(self.endpoint_url_env, ""),
            "endpoint_api_key": os.getenv(self.api_key_env, ""),
            "deployment_name": self.deployment_name,
            "model_kwargs": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens
            }
        }

    def caller_class(self):
        from llm_calls import AzureCaller
        return AzureCaller


@register_config
class AzureLlama2_7bConfig(AzureBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "llama2_7b"

    def __init__(self):
        super().__init__()
        self.deployment_name = "Llama-2-7b-chat-dxgpt"


@register_config
class AzureLlama3_8bConfig(AzureBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "llama3_8b"

    def __init__(self):
        super().__init__()
        self.endpoint_url_env = "AZURE_ML_ENDPOINT_3"
        self.api_key_env = "AZURE_ML_API_KEY_3"
        self.deployment_name = "llama-3-8b-chat-dxgpt"


@register_config
class AzureLlama3_70bConfig(AzureBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "llama3_70b"

    def __init__(self):
        super().__init__()
        self.endpoint_url_env = "AZURE_ML_ENDPOINT_4"
        self.api_key_env = "AZURE_ML_API_KEY_4"
        self.deployment_name = "llama-3-70b-chat-dxgpt"



class AzureCohereBaseConfig(BaseModelConfig):
    def __init__(self):
        self.endpoint_url_env = "AZURE_ML_ENDPOINT_2"
        self.api_key_env = "AZURE_ML_API_KEY_2"
        self.deployment_name = "Cohere-command-r-plus-dxgpt"
        self.temperature = 0
        self.max_new_tokens = 800

    def get_params(self) -> dict:
        return {
            "endpoint_url": os.getenv(self.endpoint_url_env, ""),
            "endpoint_api_key": os.getenv(self.api_key_env, ""),
            "deployment_name": self.deployment_name,
            "model_kwargs": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens
            }
        }

    def caller_class(self):
        from llm_calls import AzureCaller
        return AzureCaller


@register_config
class AzureCohereCPlusConfig(AzureCohereBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "cohere_cplus"

    def __init__(self):
        super().__init__()
        # You can override temperature, etc. if needed