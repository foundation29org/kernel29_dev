# bedrock_claude_caller.py
import os
import json
import boto3

class BedrockClaudeCaller:
    """
    Calls AWS Bedrock for Claude-based models.
    
    Expected keys in params:
      - model_id: str (e.g. "anthropic.claude-3-sonnet-20240229-v1:0")
      - temperature: float
      - max_tokens: int
      - aws_access_key_id: str
      - aws_secret_access_key: str
      - region: str
      - anthropic_version: str (optional, e.g. "bedrock-2023-05-31")
    """
    def __init__(self, params: dict):
        self.model_id = params["model_id"]
        self.temperature = params["temperature"]
        self.max_tokens = params["max_tokens"]
        self.aws_access_key_id = params["aws_access_key_id"]
        self.aws_secret_access_key = params["aws_secret_access_key"]
        self.region = params["region"]
        self.anthropic_version = params.get("anthropic_version", "bedrock-2023-05-31")

    def call_llm(self, prompt: str) -> str:
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )
        client = session.client(service_name="bedrock-runtime")
        body = json.dumps({
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
            "anthropic_version": self.anthropic_version
        })
        response = client.invoke_model(
            body=body,
            modelId=self.model_id,
            accept="application/json",
            contentType="application/json",
        )
        resp_json = json.loads(response.get("body").read())
        try:
            return resp_json["content"][0]["text"]
        except (KeyError, IndexError):
            return json.dumps(resp_json)
