# callers/groq_caller.py
from typing import Dict, Any, List, Optional, Union, Tuple
from .base_caller import BaseLLMCaller

class GroqCaller(BaseLLMCaller):
    """
    Calls the Groq API using the base caller interface.

    Required parameters:
      - model: str (e.g. "mixtral-8x7b-32768")
      - api_key: str (the Groq API key)
    
    Optional parameters:
      - temperature: float
      - max_tokens: int
      - top_p: float
      - frequency_penalty: float
      - presence_penalty: float
      - stop: List[str] or str or None
      - stream: bool
      - system_message: str or None
      - response_format: Dict or None
      - seed: int or None
      - tools: List[Dict] or None
      - tool_choice: str or Dict or None
    """
    @staticmethod
    def make_imports(verbose = False) -> bool:
        """
        Try to import all required libraries for the Groq caller.
        
        Returns:
            bool: True if all imports succeed, False otherwise
        """
        try:
            import groq
            if verbose:
                print("Successfully imported groq package.")
            return True
        except ImportError as e:
            print(f"Failed to import the 'groq' package: {str(e)}")
            print("Please install it using: pip install groq")
            return False
    
    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        # Required parameters
        self.model = params["model"]
        self.api_key = params["api_key"]
        
        # Add async_mode parameter
        self.async_mode = params.get("async_mode", False)
        params.pop("async_mode", None)
        # Optional parameters with defaults
        self.temperature = params.get("temperature", None)
        self.max_tokens = params.get("max_tokens", None)
        self.top_p = params.get("top_p", None)
        self.frequency_penalty = params.get("frequency_penalty", None)
        self.presence_penalty = params.get("presence_penalty", None)
        self.stop = params.get("stop", None)
        self.stream = params.get("stream", False)
        self.system_message = params.get("system_message", None)
        self.response_format = params.get("response_format", None)
        self.seed = params.get("seed", None)
        self.tools = params.get("tools", None)
        self.tool_choice = params.get("tool_choice", None)
        
        self._client = None
    
    def params_dict(self) -> Tuple[Dict[str, Any], List[str]]:
        """
        Define the API parameters dictionary and required parameters.
        
        Returns:
            (Dict[str, Any], List[str]): Parameters dict and required parameters list
        """
        params = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": self.stream,
            "stop": self.stop,
            "response_format": self.response_format,
            "seed": self.seed,
            "tools": self.tools,
            "tool_choice": self.tool_choice
        }
        
        required_params = ["model", "api_key"]
        
        return params, required_params
    
    def get_client(self):
        """
        Get or initialize the Groq client.
        """
        if self._client is None:
            import groq
            
            if hasattr(self, 'async_mode') and self.async_mode:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=self.api_key)
            else:
                self._client = groq.Groq(api_key=self.api_key)
        
        return self._client

        #TODO
    # def set_messages(self, messages: List[Dict[str, Any]] = []):
    #     if self.system_message:
    #     #The sys message is still not added to the messages list    
    #         self.messages.append({"role": "system", "content": self.system_message})
    #         #Remove the system message to avoid duplication 
    #         self.system_message = None

    #     if not messages:
    #         #its a single prompt
    #         self.messages = self.prompt
    #     else:
    #         #its a list of messages
    #         self.messages.extend(messages)
        
    #     # Add system message if provided
    
    #     # Add user message
    #     self.messages.append()

    # def get_query(self, prompt: str, client: Any, messages: List[Dict[str, Any]] = []) -> Any: TODO
    def get_query(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the Groq API.
        
        Args:
            prompt: The input prompt
            client: The Groq client
            messages: The list of messages to be added to the conversation  
            
        Returns:
            The raw response from the Groq API
        """
        #TODO
        # if not messages:
        #     self.prompt = {"role": "user", "content": prompt}
        #     self.set_messages()
        # else:
        #     if messages and prompt:
        #         self.set_messages(messages)

        #         messages.append({"role": "user", "content": prompt})
        
        # Get the API parameters and add messages
        params = self.get_params()

        messages = []
        messages.append({"role": "user", "content": prompt})
        params["messages"] = messages
        
        # Make the API call
        self.async_mode = True
        if self.async_mode:
            import asyncio
            response = asyncio.run(self.get_query_async(prompt, client))
        else:
            response = client.chat.completions.create(**params)
        
        return response
    
    def format_query(self, response: Any) -> str:
        """
        Extract the text from the Groq API response.
        
        Args:
            response: The raw response from the API
            
        Returns:
            The extracted text as a string

        """
        return response.choices[0].message.content

        # try:
        #     # Handle streaming responses
        #     if hasattr(response, "__iter__") and callable(response.__iter__):
        #         return self.handle_stream(response)
            
        #     # Handle regular responses
        #     return response.choices[0].message.content
        # except (IndexError, AttributeError) as e:
        #     print(f"Error extracting content from response: {e}")
        #     # Fallback to string representation of response
        #     return str(response)
    
    def handle_stream(self, response: Any) -> str:
        """
        Process a streaming response from the Groq API.
        
        Args:
            response: The streaming response from the API
            
        Returns:
            The concatenated text from all chunks
        """
        collected_text = []
        try:
            for chunk in response:
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        collected_text.append(delta.content)
            return "".join(collected_text)
        except Exception as e:
            print(f"Error processing stream response: {e}")
            return "".join(collected_text) if collected_text else str(response)

    async def get_query_async(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the Groq API asynchronously.
        
        Args:
            prompt: The input prompt
            client: The Groq AsyncClient
            
        Returns:
            The raw response from the Groq API
        """
        messages = []
        
        # Add system message if provided
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        # Get the API parameters and add messages
        params = self.get_params()
        params["messages"] = messages
        
        # Make the async API call
        response = await client.chat.completions.create(**params)
        
        return response
