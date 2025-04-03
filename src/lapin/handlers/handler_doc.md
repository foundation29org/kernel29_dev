# LLM Handler Framework Documentation

## Overview

The LLM Handler Framework provides a unified interface for working with various Large Language Model (LLM) configurations and callers. It serves as the primary entry point for applications using the LLM Microframework, orchestrating the interaction between configuration classes and caller implementations.

The framework centers around the **ModelHandler** class, which serves as the central orchestration component responsible for:

1. Looking up model configurations by their aliases
2. Instantiating the appropriate configuration objects
3. Retrieving the associated caller classes
4. Building callers with the correct parameters
5. Executing calls to the LLM APIs
6. Returning text responses to the application

When using the framework, you simply:
1. Create an instance of the ModelHandler
2. Use its methods to interact with any registered model
3. The handler takes care of finding the right configuration, creating the caller, and managing the response flow

## ModelHandler Class Implementation

### Class Definition

The ModelHandler is defined with a simple interface that hides the complexity of the underlying components:

```python
class ModelHandler:
    """
    Manages the orchestration between configuration classes and caller classes.
    """
    def __init__(self):
        # Optionally, initialize state or load context if needed
        pass
```

### get_response Method

The `get_response` method is the primary interface for obtaining responses from language models.

**Purpose**:
- Provides a unified method to call any registered model
- Handles the complete workflow from model lookup to response
- Abstracts away the details of configuration and API interaction

**Implementation**:
```python
def get_response(self, alias: str, prompt: str) -> str:
    """
    High-level method that:
      1) Looks up the config class by alias in CONFIG_REGISTRY.
      2) Instantiates the config object.
      3) Retrieves the caller class from config.caller_class().
      4) Builds the caller with config.get_params().
      5) Calls the LLM and returns the text.
      
    Args:
        alias: The registered alias for the model configuration
        prompt: The text prompt to send to the LLM
        
    Returns:
        str: The text response from the LLM
        
    Raises:
        ValueError: If no configuration is found for the given alias
    """
    config_cls = CONFIG_REGISTRY.get(alias)
    if not config_cls:
        raise ValueError(f"No configuration found for alias '{alias}'.")

    config_obj = config_cls()  # Instantiate the configuration
    caller_cls = config_obj.caller_class()
    params = config_obj.get_params()

    caller = caller_cls(params)
    return caller.call_llm(prompt)
```

### list_available_models Method

The `list_available_models` method returns a list of all registered model aliases.

**Purpose**:
- Provides discovery of available models
- Allows applications to show model options to users
- Facilitates dynamic model selection

**Implementation**:
```python
def list_available_models(self) -> List[str]:
    """
    Returns a list of all available model aliases.
    
    Returns:
        List[str]: A list of registered model aliases
    """
    return list(CONFIG_REGISTRY.keys())
```

## Workflow Orchestration

The ModelHandler serves as the orchestrator of the entire LLM workflow:

1. **Model Selection**: The handler finds the appropriate model configuration by alias
2. **Configuration Instantiation**: It creates an instance of the configuration class
3. **Caller Selection**: It retrieves the appropriate caller class from the configuration
4. **Parameter Preparation**: It gets the parameter dictionary from the configuration
5. **Caller Creation**: It creates an instance of the caller with the parameters
6. **API Invocation**: It calls the caller's `call_llm` method with the prompt
7. **Response Return**: It returns the text response to the application

This orchestration pattern ensures a consistent flow regardless of which model is being used, making it easy to switch between different LLM providers and model variants.

## Usage Examples

### Basic Usage

```python
from llm_libs.handlers.base_handler import ModelHandler

# Create a handler
handler = ModelHandler()

# List all available models
available_models = handler.list_available_models()
print(f"Available models: {available_models}")

# Get a response from a specific model
response = handler.get_response("mixtral-8x7b", "Explain quantum computing in simple terms.")
print(response)
```

### Handling Multiple Models

```python
# Using multiple models for different tasks
handler = ModelHandler()

# Use a smaller, faster model for a simple query
quick_response = handler.get_response("llama3-8b", "What is the capital of France?")

# Use a more powerful model for a complex reasoning task
detailed_response = handler.get_response("c3opus", "Explain the implications of quantum computing for cryptography.")

# Use a specialized coding model for code generation
code_response = handler.get_response("qwen-coder-32b", "Write a Python function to find prime numbers using the Sieve of Eratosthenes.")
```

## Best Practices for Implementation

1. **Error Handling**: Provide clear error messages when models aren't found or fail
2. **Performance Optimization**: Consider caching configurations or callers for frequently used models
3. **Extensibility**: Design the handler to be easily extended with additional features
4. **Logging**: Include logging to track model usage and performance
5. **Configuration Validation**: Validate configurations before passing them to callers
6. **Abstraction**: Keep the handler interface simple even as underlying complexity grows
7. **Dependency Injection**: Consider allowing custom registries for testing or specialized use cases

## Potential Extensions

While the core ModelHandler maintains a simple interface, it can be extended to include:

1. **Concurrency Control**: Managing parallel requests to avoid rate limiting
2. **Caching**: Storing responses to reduce API calls for identical prompts
3. **Fallback Mechanisms**: Trying alternative models if the primary model fails
4. **Performance Monitoring**: Tracking response times and token usage
5. **Cost Management**: Enforcing budgets and optimizing for cost-effective model selection

These extensions can be implemented as subclasses or composed services while maintaining the simple core interface of the ModelHandler.
