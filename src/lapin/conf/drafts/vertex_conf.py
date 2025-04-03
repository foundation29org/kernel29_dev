# vertex_gemini_configs.py
import os
from base import BaseModelConfig
from config_registry import register_config

class VertexGeminiBaseConfig(BaseModelConfig):
    """
    Base config for GCP Vertex AI with 'gemini-1.5-pro-preview-0409'.
    """
    def __init__(self):
        self.model = "gemini-1.5-pro-preview-0409"
        self.project_id = "nav29-21389"
        self.region = "us-central1"
        self.credentials_file = "./nav29-21389-c1a94e300dcb.json"
        self.temperature = 0
        self.max_output_tokens = 800

    def get_params(self) -> dict:
        return {
            "model": self.model,
            "project_id": self.project_id,
            "region": self.region,
            "credentials_file": self.credentials_file,
            "generation_config": {
                "max_output_tokens": self.max_output_tokens,
                "temperature": self.temperature,
                "top_p": 1,
                "top_k": 32
            },
            "safety_settings": {},
            "stream": False
        }

    def caller_class(self):
        from llm_calls import VertexCaller
        return VertexCaller


@register_config
class VertexGeminiProConfig(VertexGeminiBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "geminipro"

    def __init__(self):
        super().__init__()
        # override temperature or project_id if needed
