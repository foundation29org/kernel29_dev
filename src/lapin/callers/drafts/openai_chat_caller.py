# openai_chat_caller.py
import os

class OpenAIChatCaller:
    """
    Calls the OpenAI Chat API via a wrapper like langchain's ChatOpenAI.
    
    Expected keys in params:
      - model_name: str (e.g. "gpt-4-1106-preview" or "gpt-4-turbo-2024-04-09")
      - openai_api_key: str (or it may be taken from environment if provided)
      - temperature: float
      - max_tokens: int
    """
    def __init__(self, params: dict)    :
        self.model_name = params["model_name"]
        self.openai_api_key = params.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        self.temperature = params.get("temperature", 0)
        self.max_tokens = params.get("max_tokens", 800)

    def call_llm(self, prompt: str) -> str:
        from langchain.chat_models import ChatOpenAI
        llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        result = llm([{"role": "user", "content": prompt}])
        return result.content
