# azure_caller.py
import os

class AzureCaller:
    """
    Calls an Azure ML Endpoint for LLMs.
    
    Expected keys in params:
      - endpoint_url: str
      - endpoint_api_key: str
      - deployment_name: str
      - endpoint_api_type: str (optional; e.g. "serverless")
      - model_kwargs: dict (e.g. {"temperature": 0, "max_new_tokens": 800})
    """
    def __init__(self, params: dict):
        self.endpoint_url = params["endpoint_url"]
        self.api_key = params["endpoint_api_key"]
        self.deployment_name = params["deployment_name"]
        self.api_type = params.get("endpoint_api_type", "serverless")
        self.model_kwargs = params.get("model_kwargs", {})

    def call_llm(self, prompt: str) -> str:
        from langchain_community.chat_models.azureml_endpoint import AzureMLChatOnlineEndpoint
        from langchain_community.chat_models.azureml_endpoint import CustomOpenAIChatContentFormatter
        from langchain_core.messages import HumanMessage

        llm = AzureMLChatOnlineEndpoint(
            endpoint_url=self.endpoint_url,
            endpoint_api_type=self.api_type,
            endpoint_api_key=self.api_key,
            content_formatter=CustomOpenAIChatContentFormatter(),
            deployment_name=self.deployment_name,
            model_kwargs=self.model_kwargs
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
