# callers/groq/sync_groq_caller.py
from typing import Dict, Any, List, Optional, Union, Tuple
from .base_groq_caller import BaseGroqCaller

class SyncGroqCaller(BaseGroqCaller):
    """
    Explicit synchronous Groq API caller.
    This class is designed to be used when you specifically want synchronous behavior.

    Required parameters:
      - model: str (e.g. "mixtral-8x7b-32768")
      - api_key: str (the Groq API key)
    """
    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        # Add any SyncGroqCaller-specific initialization here
    
    def get_client(self):
        """
        Get or initialize the synchronous Groq client.
        """
        if self._client is None:
            import groq
            self._client = groq.Groq(api_key=self.api_key)
        
        return self._client
    
    def get_query(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the Groq API synchronously.
        
        Args:
            prompt: The input prompt
            client: The Groq client
            
        Returns:
            The raw response from the Groq API
        """
        messages = self.set_messages(prompt)
        
        # Get the API parameters and add messages
        params = self.get_params()
        params["messages"] = messages
        
        # Make the API call
        response = client.chat.completions.create(**params)
        
        return response

























        
    # TODO: implement handle_stream
    # def handle_stream(self, response: Any) -> str:
    #     """
    #     Process a streaming response from the Groq API.
        
    #     Args:
    #         response: The streaming response from the API
            
    #     Returns:
    #         The concatenated text from all chunks
    #     """
    #     collected_text = []
    #     try:
    #         for chunk in response:
    #             if hasattr(chunk, "choices") and len(chunk.choices) > 0:
    #                 delta = chunk.choices[0].delta
    #                 if hasattr(delta, "content") and delta.content:
    #                     collected_text.append(delta.content)
    #         return "".join(collected_text)
    #     except Exception as e:
    #         print(f"Error processing stream response: {e}")
    #         return "".join(collected_text) if collected_text else str(response)
