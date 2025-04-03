# vertex_caller.py
import os
import json
import boto3

class VertexCaller:
    """
    Calls Google Vertex AI for generative models.
    
    Expected keys in params:
      - model: str (e.g. "gemini-1.5-pro-preview-0409")
      - project_id: str
      - region: str
      - credentials_file: str (path to service account JSON)
      - generation_config: dict (e.g. {"max_output_tokens": 800, "temperature": 0, "top_p": 1, "top_k": 32})
      - safety_settings: dict (optional)
      - stream: bool (optional)
    """
    def __init__(self, params: dict):
        self.model = params["model"]
        self.project_id = params["project_id"]
        self.region = params["region"]
        self.credentials_file = params["credentials_file"]
        self.generation_config = params["generation_config"]
        self.safety_settings = params.get("safety_settings", {})
        self.stream = params.get("stream", False)

    def call_llm(self, prompt: str) -> str:
        try:
            from google.oauth2 import service_account
            import vertexai
            from vertexai.preview.generative_models import GenerativeModel
        except ImportError:
            raise ImportError("Required Vertex AI packages not installed.")
        
        creds = service_account.Credentials.from_service_account_file(self.credentials_file)
        vertexai.init(project=self.project_id, location=self.region, credentials=creds)
        generative_model = GenerativeModel(self.model)
        response = generative_model.generate_content(
            [prompt],
            generation_config={**self.generation_config},
            safety_settings={**self.safety_settings},
            stream=self.stream
        )
        resp_dict = response.to_dict()
        if not resp_dict.get("candidates"):
            return "No response available due to error."
        return resp_dict["candidates"][0]["content"]["parts"][0]["text"]
