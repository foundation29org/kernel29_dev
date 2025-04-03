# mistral_caller.py
import os
import json
import boto3

class MistralBedrockCaller:
    """
    Calls Mistral models via AWS Bedrock.
    
    Expected keys in params:
      - bedrock_model_id: str (e.g. "mistral.mixtral-8x7b-instruct-v0:1")
      - temperature: float
      - max_tokens: int
      - prompt_format: str (e.g. "<s>[INST] {prompt} [/INST]")
      - aws_access_key_id: str
      - aws_secret_access_key: str
      - region: str
      - top_p: float (optional, default provided in config)
    """
    def __init__(self, params: dict):
        self.bedrock_model_id = params["bedrock_model_id"]
        self.temperature = params["temperature"]
        self.max_tokens = params["max_tokens"]
        self.prompt_format = params.get("prompt_format", "<s>[INST] {prompt} [/INST]")
        self.aws_access_key_id = params["aws_access_key_id"]
        self.aws_secret_access_key = params["aws_secret_access_key"]
        self.region = params["region"]
        self.top_p = params.get("top_p", 1)

    def call_llm(self, prompt: str) -> str:
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region
        )
        client = session.client(service_name="bedrock-runtime")
        final_prompt = self.prompt_format.format(prompt=prompt)
        body = json.dumps({
            "prompt": final_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p
        })
        response = client.invoke_model(
            body=body,
            modelId=self.bedrock_model_id,
            accept="application/json",
            contentType="application/json",
        )
        resp_json = json.loads(response.get("body").read())
        try:
            return resp_json["outputs"][0]["text"]
        except (KeyError, IndexError):
            return json.dumps(resp_json)
