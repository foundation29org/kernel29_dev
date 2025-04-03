 # bedrock_claude_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config

class BedrockClaudeBaseConfig(BaseModelConfig):
    """
    Base class for calling Claude via AWS Bedrock.
    Subclasses define 'model_id'.
    """
    def __init__(self):
        self.model_id = None
        self.temperature = 0
        self.max_tokens = 2000
        self.aws_access_key_id_env = "BEDROCK_USER_KEY"
        self.aws_secret_access_key_env = "BEDROCK_USER_SECRET"
        self.region = "us-east-1"

    def get_params(self) -> dict:
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "aws_access_key_id": os.getenv(self.aws_access_key_id_env, ""),
            "aws_secret_access_key": os.getenv(self.aws_secret_access_key_env, ""),
            "region": self.region
        }

    def caller_class(self):
        from llm_calls import BedrockClaudeCaller
        return BedrockClaudeCaller


@register_config
class BedrockClaudeConfig(BedrockClaudeBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "c3sonnet"

    def __init__(self):
        super().__init__()
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

        
class MistralBedrockBaseConfig(BaseModelConfig):
    """
    Calls Mistral models via AWS Bedrock
    """
    def __init__(self):
        self.bedrock_model_id = None
        self.temperature = 0
        self.max_tokens = 800
        self.prompt_format = "<s>[INST] {prompt} [/INST]"
        self.aws_access_key_id_env = "BEDROCK_USER_KEY"
        self.aws_secret_access_key_env = "BEDROCK_USER_SECRET"
        self.region = "us-east-1"

    def get_params(self) -> dict:
        return {
            "bedrock_model_id": self.bedrock_model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "prompt_format": self.prompt_format,
            "aws_access_key_id": os.getenv(self.aws_access_key_id_env, ""),
            "aws_secret_access_key": os.getenv(self.aws_secret_access_key_env, ""),
            "region": self.region
        }

    def caller_class(self):
        from llm_calls import MistralBedrockCaller
        return MistralBedrockCaller


@register_config
class MistralMoeConfig(MistralBedrockBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "mistralmoe"

    def __init__(self):
        super().__init__()
        self.bedrock_model_id = "mistral.mixtral-8x7b-instruct-v0:1"


@register_config
class Mistral7bConfig(MistralBedrockBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "mistral7b"

    def __init__(self):
        super().__init__()
        self.bedrock_model_id = "mistral.mistral-7b-instruct-v0:2"
