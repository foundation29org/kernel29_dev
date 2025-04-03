# callers/groq/base_groq_caller.py
from typing import Dict, Any, List, Optional, Union, Tuple
from ..base_caller import BaseLLMCaller

class BaseGroqCaller(BaseLLMCaller):
    """
    Base class for Groq callers with shared functionality.
    This class is intended to be subclassed by GroqCaller, SyncGroqCaller, and AsyncGroqCaller.
    """
    @staticmethod
    def make_imports(verbose=False) -> bool:
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
    
    def format_query(self, response: Any) -> str:
        """
        Extract the text from the Groq API response.
        
        Args:
            response: The raw response from the API
            
        Returns:
            The extracted text as a string
        """
        return response.choices[0].message.content
        
    def set_messages(self, prompt: str) -> List[Dict[str, str]]:
        """
        Create a messages list for the API request containing only a user message.
        
        Args:
            prompt: The user prompt text
            
        Returns:
            List of message dictionaries
        """

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
    
        # Add user message
        # self.messages.append()
        





        messages = []
        messages.append({"role": "user", "content": prompt})
        return messages
