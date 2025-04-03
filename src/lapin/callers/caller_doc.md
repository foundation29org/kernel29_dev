# LLM Caller Framework Documentation

## Overview

The LLM Caller Framework provides a standardized way to interact with different Large Language Model (LLM) providers through a unified interface. The framework consists of three main components:

1. **Base Abstract Class**: Defines the common interface and workflow for all LLM callers
2. **Provider-Specific Callers**: Implement the details for each LLM provider (Anthropic, Azure, etc.)
3. **Workflow Orchestration**: Manages the process from prompt to response in a consistent way

The framework follows a template method pattern where the base class defines the skeleton of the algorithm (the `call_llm` method), while provider-specific subclasses implement the individual steps. This design ensures consistent behavior across different providers while isolating provider-specific implementation details.

When using the framework, you simply:
1. Create an instance of the appropriate caller with your configuration
2. Call the `call_llm` method with your prompt
3. Receive a standardized text response

## Architecture and Implementation

### make_imports Method

The `make_imports` method verifies that all required libraries for a specific provider are available.

**Purpose**:
- Checks if necessary dependencies are installed
- Provides helpful error messages when dependencies are missing
- Prevents runtime errors due to missing libraries

**Base Class Implementation**:
```python
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
```

**Example Implementation (Anthropic)**:
```python
@staticmethod
def make_imports() -> bool:
    try:
        import anthropic
        print("Successfully imported anthropic package.")
        return True
    except ImportError as e:
        print(f"Failed to import the 'anthropic' package: {str(e)}")
        print("Please install it using: pip install anthropic")
        return False
```

### _validate_params Method

The `_validate_params` method ensures that all required parameters for a specific provider are present.

**Purpose**:
- Validates that all required configuration parameters exist
- Provides clear error messages about missing parameters
- Prevents cryptic errors when calling the API

**Base Class Implementation**:
```python
@abstractmethod
def _validate_params(self) -> None:
    """
    Validate that all required parameters are present.
    Should raise ValueError if any required parameter is missing.
    """
    pass
```

**Example Implementation (Anthropic)**:
```python
def _validate_params(self) -> None:
    required_params = ["model", "temperature", "max_tokens", "api_key"]
    missing = [param for param in required_params if param not in self.params]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")
```

### get_client Method

The `get_client` method creates or retrieves a client object for communicating with the LLM provider's API.

**Purpose**:
- Creates a configured client for API communication
- Implements lazy initialization to create clients only when needed
- Handles authentication and connection setup

**Base Class Implementation**:
```python
@abstractmethod
def get_client(self) -> Any:
    """
    Get or create the client/session for the LLM API.
    
    Returns:
        The client or session object for making API calls
    """
    pass
```

**Example Implementation (Anthropic)**:
```python
def get_client(self) -> Any:
    if self._client is None:
        import anthropic
        self._client = anthropic.Anthropic(api_key=self.api_key)
    return self._client
```

### get_query Method

The `get_query` method executes the API call to the LLM provider.

**Purpose**:
- Makes the actual API request with the prompt
- Configures request parameters (model, temperature, etc.)
- Returns the raw response from the provider

**Base Class Implementation**:
```python
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
```

**Example Implementation (Anthropic)**:
```python
def get_query(self, prompt: str, client: Any) -> Any:
    response = client.messages.create(
        model=self.model,
        max_tokens=self.max_tokens,
        temperature=self.temperature,
        messages=[{"role": "user", "content": prompt}]
    )
    return response
```

### format_query Method

The `format_query` method extracts the text content from the provider's response.

**Purpose**:
- Extracts text from the provider-specific response format
- Handles error cases and unexpected response structures
- Returns a clean string as the final output

**Base Class Implementation**:
```python
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
```

**Example Implementation (Anthropic)**:
```python
def format_query(self, response: Any) -> str:
    try:
        return response.content[0].text
    except (IndexError, AttributeError):
        return str(response.content)
```

### call_llm Method

The `call_llm` method orchestrates the entire workflow from prompt to response.

**Purpose**:
- Implements the template method pattern
- Coordinates the workflow steps in a consistent way
- Handles the overall flow without duplicating code

**Base Class Implementation**:
```python
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
    
    # Extract and return the text
    return self.format_query(response)
```

**Note**: There is no need to implement `call_llm` in the provider-specific classes because it follows the DRY (Don't Repeat Yourself) principle. The base class implementation defines the workflow, and each provider only needs to implement the specific steps. This ensures a consistent process across all providers while allowing for provider-specific customization of each step.

## Usage Example

```python
# Create the caller with provider-specific parameters
caller = AnthropicCaller({
    "model": "claude-3-opus-20240229",
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": "your_api_key_here"
})

# Get a response
response = caller.call_llm("Explain quantum computing in simple terms.")
print(response)
```

## Best Practices for Implementation

1. **Client Caching**: Always cache your client in `get_client()` to avoid creating multiple clients unnecessarily
2. **Error Handling**: Include robust error handling in `format_query()` to handle unexpected response formats
3. **Descriptive Errors**: Provide clear error messages in `_validate_params()` to help users identify configuration issues
4. **Encapsulation**: Keep provider-specific logic isolated to the specific caller class
5. **DRY Principle**: Don't repeat workflow logic that belongs in the base class
6. **Parameter Validation**: Validate all required parameters early to prevent cryptic API errors