# callers/groq/async_groq_caller.py
from typing import Dict, Any, List, Optional, Union, Tuple
from .base_groq_caller import BaseGroqCaller

class AsyncGroqCaller(BaseGroqCaller):
    """
    Asynchronous Groq API caller.
    This class is designed for use in async contexts.

    Required parameters:
      - model: str (e.g. "mixtral-8x7b-32768")
      - api_key: str (the Groq API key)
    """
    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        # Add any AsyncGroqCaller-specific initialization here
    
    def get_client(self):
        """
        Get or initialize the async Groq client.
        """
        if self._client is None:
            import groq
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
        
        return self._client
    
    async def call_llm_async(self, prompt: str) -> Tuple[Any, str]:
        """
        Async version of call_llm.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Tuple of (raw_response, parsed_text)
        """
        # Verify imports are successful
        if not self.make_imports():
            raise ImportError("Required imports failed")
        
        # Validate required parameters
        # self.validate_params()
        
        # Get the client
        client = self.get_client()
        
        # Execute the query
        response = await self.get_query_async(prompt, client)
        
        # Parse the response
        parsed_response = self.format_query(response)
        
        return response, parsed_response

            
    def get_query(self, prompt: str, client: Any) -> Any:
            """
            Synchronous implementation of get_query required by the base class.
            This method raises a warning since AsyncGroqCaller is designed for async use only.
            
            Args:
                prompt: The input prompt
                client: The Groq client
                
            Raises:
                RuntimeError: Always raises this error as this class is for async use only
            """
            raise RuntimeError(
                "AsyncGroqCaller is designed for asynchronous use only. " +
                "Please use get_query_async instead, or use GroqCaller for synchronous operations."
            )


    async def get_query_async(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the Groq API asynchronously.
        
        Args:
            prompt: The input prompt
            client: The async Groq client
            
        Returns:
            The raw response from the async Groq API
        """
        messages = self.set_messages(prompt)
        
        # Get the API parameters and add messages
        params = self.get_params()
        params["messages"] = messages
        
        # Make the async API call
        # The method name might vary depending on Groq library implementation
        try:
            # Try the standard method name first
            response = await client.chat.completions.create(**params)
        except AttributeError:
            # If standard method fails, try alternative async method name
            if hasattr(client.chat.completions, "acreate"):
                response = await client.chat.completions.acreate(**params)
            else:
                raise ValueError("Could not find appropriate async method in Groq client")
        
        return response
















































        
    # TODO: implement handle_stream_async
    # async def handle_stream_async(self, response: Any) -> str:
    #     """
    #     Process a streaming response from the async Groq API.
        
    #     Args:
    #         response: The streaming response from the API
            
    #     Returns:
    #         The concatenated text from all chunks
    #     """
    #     collected_text = []
    #     try:
    #         async for chunk in response:
    #             if hasattr(chunk, "choices") and len(chunk.choices) > 0:
    #                 delta = chunk.choices[0].delta
    #                 if hasattr(delta, "content") and delta.content:
    #                     collected_text.append(delta.content)
    #         return "".join(collected_text)
    #     except Exception as e:
    #         print(f"Error processing async stream response: {e}")
    #         return "".join(collected_text) if collected_text else str(response)
