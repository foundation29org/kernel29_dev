# callers/anthropic_caller.py
from typing import Dict, Any, List, Optional
from .base_caller import BaseLLMCaller

class AnthropicCaller(BaseLLMCaller):
    """
    Calls the Anthropic API using the base caller interface.

    Required parameters:
      - model: str (e.g. "claude-3-5-sonnet-20240620")
      - temperature: float
      - max_tokens: int
      - api_key: str (the Anthropic API key)
    """
    @staticmethod
    def make_imports() -> bool:
        """
        Try to import all required libraries for the Anthropic caller.
        
        Returns:
            bool: True if all imports succeed, False otherwise
        """
        try:
            import anthropic
            print("Successfully imported anthropic package.")
            return True
        except ImportError as e:
            print(f"Failed to import the 'anthropic' package: {str(e)}")
            print("Please install it using: pip install anthropic")
            return False
    
    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.model = params["model"]
        self.temperature = params["temperature"]
        self.max_tokens = params["max_tokens"]
        self.api_key = params["api_key"]
        self._client = None
    
    def _validate_params(self) -> None:
        """Validate required parameters are present."""
        required_params = ["model", "temperature", "max_tokens", "api_key"]
        missing = [param for param in required_params if param not in self.params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
    
    def get_client(self) -> Any:
        """
        Get or initialize the Anthropic client.
        
        Returns:
            The Anthropic client instance
        """
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        
        return self._client
    
    def get_query(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the Anthropic API.
        
        Args:
            prompt: The input prompt
            client: The Anthropic client
            
        Returns:
            The raw response from the Anthropic API
        """
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response
    
    def format_query(self, response: Any) -> str:
        """
        Extract the text from the Anthropic API response.
        
        Args:
            response: The raw response from the API
            
        Returns:
            The extracted text as a string
        """
        try:
            return response.content[0].text
        except (IndexError, AttributeError):
            return response.content
