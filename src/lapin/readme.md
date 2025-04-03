# LLM Microframework

A lightweight, extensible framework for managing and interacting with multiple Large Language Models (LLMs) across different providers (Anthropic, Azure, AWS Bedrock, Google Vertex, Groq...).

## Overview

This microframework provides a clean, consistent interface for working with various LLM providers while keeping the codebase modular and maintainable. It follows a three-layer architecture:

1. **Configuration Layer**: Defines model configurations and their parameters
2. **Caller Layer**: Handles API communication with each provider
3. **Handler Layer**: Orchestrates the workflow and provides additional features

## Directory Structure

```
llm_libs/
├── callers/
│   ├── base_caller.py                 # Abstract base caller
│   ├── anthropic_caller.py     # Anthropic-specific implementation
│   ├── groq_caller.py         # Azure-specific implementation
├── conf/
│   ├── base_conf.py                 # Base configuration class
│   ├── anthropic_conf.py           # Azure model configurations
│   ├── groq_conf.py    # Azure OpenAI configurations
├── handlers/
│   └── base_handler.py         # Model handler orchestration

```

## How It Works

### 1. Configuration Layer

Each model is defined by a configuration class that inherits from `BaseModelConfig`. These classes specify:

- A unique alias for the model
- All parameters needed to call the model (endpoints, API keys, temperature, etc.)
- Which caller class should be used for this model

Example configuration class:

```python
@register_config
class AzureLlama3_8bConfig(AzureBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "llama3_8b"

    def __init__(self):
        super().__init__()
        self.endpoint_url_env = "AZURE_ML_ENDPOINT_3"
        self.api_key_env = "AZURE_ML_API_KEY_3"
        self.deployment_name = "llama-3-8b-chat-dxgpt"
```

The `@register_config` decorator automatically adds this class to the config registry.

### 2. Caller Layer

Callers are responsible for the actual API interactions. Each provider has a dedicated caller class that inherits from `BaseLLMCaller`. These classes know how to:

- Import required dependencies
- Validate parameters
- Initialize API clients
- Format requests according to the provider's requirements
- Parse responses and extract text

Each caller implements a standard `call_llm(prompt)` method that handles the complete workflow.

Example caller implementation:

```python
class AnthropicCaller(BaseLLMCaller):
    @staticmethod
    def make_imports() -> bool:
        try:
            import anthropic
            return True
        except ImportError:
            return False
    
    # Other required methods...
    
    def call_llm(self, prompt: str) -> str:
        client = self.get_client()
        response = self.get_query(prompt, client)
        return self.format_query(response)
```

### 3. Handler Layer

The `ModelHandler` class serves as the entry point for using the framework. It:

1. Looks up the correct configuration by alias
2. Creates an instance of that configuration
3. Gets the appropriate caller class
4. Builds the caller with the config parameters
5. Calls the LLM and returns the text response

Additional features include:
- Model listing
- Usage tracking
- Concurrency control
- Error handling
- (Optional) Response caching

## Usage

### Basic Usage

```python
from llm_libs.handlers.base_handler import ModelHandler

# Create a handler
handler = ModelHandler()

# List all available models
available_models = handler.list_available_models()
print(f"Available models: {available_models}")

# Get a response from a specific model
response = handler.get_response("llama3_8b", "Explain quantum computing in simple terms.")
print(response)
```

### Adding a New Model Configuration

1. Create a new configuration class that inherits from the appropriate base config
2. Define the `alias` class method to return a unique identifier
3. Set the required parameters in `__init__`
4. Apply the `@register_config` decorator

Example:

```python
from llm_libs.conf.base import BaseModelConfig
from llm_libs.config_registry import register_config

@register_config
class NewModelConfig(BaseModelConfig):
    @classmethod
    def alias(cls) -> str:
        return "my_new_model"

    def __init__(self):
        self.parameter1 = "value1"
        self.parameter2 = "value2"
        
    def get_params(self) -> dict:
        return {
            "param1": self.parameter1,
            "param2": self.parameter2
        }
        
    def caller_class(self):
        from llm_libs.callers.appropriate_caller import AppropriateCallerClass
        return AppropriateCallerClass
```

### Adding a New Provider

1. Create a new caller class in the `callers` directory that inherits from `BaseLLMCaller`
2. Implement all required abstract methods
3. Create corresponding configuration classes that use this caller

## Benefits

- **Separation of Concerns**: Clear distinction between configuration, API communication, and orchestration
- **Extensibility**: Easy to add new models or providers without changing existing code
- **Consistency**: Unified interface for all LLM providers
- **Maintainability**: Simple, focused classes with single responsibilities
- **Flexibility**: Configure each model independently with its own parameters

## Environment Variables

The framework uses environment variables for API keys and other sensitive information. Make sure to set these before using the corresponding models:

```
# Azure
AZURE_ML_ENDPOINT
AZURE_ML_API_KEY
AZURE_ML_ENDPOINT_2
AZURE_ML_API_KEY_2
AZURE_ML_ENDPOINT_3
AZURE_ML_API_KEY_3

# AWS Bedrock
BEDROCK_USER_KEY
BEDROCK_USER_SECRET

# Anthropic
ANTHROPIC_API_KEY

# Google Vertex
# (Uses service account JSON file path specified in config)
```