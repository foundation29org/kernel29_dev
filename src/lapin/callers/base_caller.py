# callers/base_caller.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List

class BaseLLMCaller(ABC):
    """
    Abstract base class for all LLM callers.
    
    Each implementation must override required methods to handle
    the specific API interaction for its LLM provider.
    """
    
    @staticmethod
    @abstractmethod
    def make_imports() -> bool:
        """
        Try to import all required libraries for this caller.
        
        This method should handle all imports in a try-except block
        and return True if all imports succeed, False otherwise.
        
        Implementations should clearly indicate which imports failed.
        """
        pass
    
    def __init__(self, params: Dict[str, Any], verbose = False):
        """
        Initialize the caller with configuration parameters.
        
        Args:
            params: Dictionary containing provider-specific parameters
        """
        self.params = params
        self.verbose = verbose
        # Add async_mode param with default to False
        self.async_mode = params.get("async_mode", False)
    
    @abstractmethod
    def params_dict(self) -> Dict[str, Any]:
        """
        Define the API parameters dictionary and required parameters.
        
        This method should return a tuple containing:
        1. A dictionary of parameters for the API call
        2. A list of required parameter names
        
        Returns:
            (Dict[str, Any], List[str]): Parameters dict and required parameters list
        """
        return {}, []
    
    def get_params(self) -> Dict[str, Any]:
        """
        Validate required parameters and filter out None values.
        
        This method:
        1. Gets parameters and requirements from params_dict()
        2. Checks if all required parameters are present
        3. Filters out parameters with None values
        
        Returns:
            A dictionary with validated, non-None parameters
            
        Raises:
            ValueError: If any required parameter is missing
        """
        params, required_params = self.params_dict()
        
        # Check for required parameters
        missing = [param for param in required_params if param not in self.params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        
        # Filter out None values
        return {k: v for k, v in params.items() if v is not None}
    
    @abstractmethod
    def get_client(self) -> Any:
        """
        Get or create the client/session for the LLM API.
        
        Returns:
            The client or session object for making API calls
        """
        pass
    
    @abstractmethod
    def get_query(self, prompt: str, client: Any) -> Any:
        """
        Execute the query against the LLM API.
        
        Args:
            prompt: The input prompt for the LLM
            client: The client to use for the API call
            
        Returns:
            The raw response from the LLM API
        """
        pass
    
    @abstractmethod
    def format_query(self, response: Any) -> str:
        """
        Extract the text from the LLM API response.
        
        Args:
            response: The raw response from the API
            
        Returns:
            The extracted text as a string
        """
        pass
    
    def call_llm(self, prompt: str) -> str:
        """
        Call the LLM with the provided prompt.
        
        This method orchestrates the entire workflow:
        1. Get the client using get_client()
        2. Execute the query using get_query()
        3. Extract the text using format_query()
        
        Args:
            prompt: The input prompt for the LLM
            
        Returns:
            The text response from the LLM as a string
        """
        # Check that imports are available
        if not self.make_imports():
            raise ImportError("Required packages are not installed.")
        
        # Get the client
        client = self.get_client()
        
        # Execute the query
        response = self.get_query(prompt, client)
        # print (response)
        # Extract and return the text
        parsed_response = self.format_query(response)

        # print(parsed_response)
        return response, parsed_response

    # Add async call method
    async def call_async(self, prompt: str) -> str:
        """
        Call the LLM asynchronously with the given prompt and return the response.
        
        Args:
            prompt: The input prompt
            
        Returns:
            The model's response as a string
        """
        if not hasattr(self, 'get_query_async'):
            raise NotImplementedError("Async call not implemented for this caller")
            
        client = self.get_client()
        response = await self.get_query_async(prompt, client)
        return self.format_query(response)
