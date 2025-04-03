# LLM Configuration Framework Documentation

## Overview

The LLM Configuration Framework provides a standardized approach to define and manage configuration settings for different Large Language Model (LLM) providers. The framework enables easy registration, retrieval, and parameterization of model configurations through a consistent interface.

## Architecture and Implementation

### BaseModelConfig Class

The `BaseModelConfig` abstract base class defines the required interface:

```python
class BaseModelConfig(ABC):
    """
    Abstract base class for all model configurations.
    """
    
    def __init__(self):
        """
        Abstract initialization method that subclasses must implement.
        """
        pass

    @classmethod
    @abstractmethod
    def alias(cls) -> str:
        """Returns a unique string identifier for this model configuration."""
        pass

    @abstractmethod
    def get_params(self) -> dict:
        """Returns a dictionary of parameters needed by the caller."""
        pass

    @abstractmethod
    def caller_class(self):
        """Returns the reference to the appropriate caller class."""
        pass
```

### Key Method Implementations

#### __init__ Method

The initialization pattern follows a hierarchy:

**Provider Base Implementation (Groq)**:
```python
def __init__(self):
    # Initialize provider-specific parameters
    self.temperature = 0.7
    self.max_tokens = 1024
    self.api_key_env = "GROQ_API_KEY"
    self.top_p = 1.0
    self.frequency_penalty = 0.0
    self.presence_penalty = 0.0
    self.model = None  # Will be set by model subclasses
    self.system_message = "You are a helpful assistant."
    self.stream = False
    self.stop = None
```

**Model-Specific Implementation (Mixtral on Groq)**:
```python
def __init__(self):
    super().__init__()  # Get Groq provider defaults
    self.model = "mixtral-8x7b-32768"
    self.max_tokens = 32768
```

#### alias Method

Provides a unique identifier for model configuration lookup:

```python
@classmethod
def alias(cls) -> str:
    return "mixtral-8x7b"  # Example: alias for Mixtral on Groq
```

#### get_params Method

Returns a dictionary with all parameters needed for the API call:

```python
def get_params(self) -> dict:
    return {
        "model": self.model,
        "temperature": self.temperature,
        "max_tokens": self.max_tokens,
        "top_p": self.top_p,
        "frequency_penalty": self.frequency_penalty,
        "presence_penalty": self.presence_penalty,
        "api_key": os.getenv(self.api_key_env, ""),
        "system_message": self.system_message,
        "stream": self.stream,
        "stop": self.stop
    }
```

#### caller_class Method

Returns the appropriate caller class for the model:

```python
def caller_class(self):
    from ..callers.groq_caller import GroqCaller
    return GroqCaller
```

### Configuration Registry

The registration mechanism allows for automatic collection of configurations:

```python
# Global registry
CONFIG_REGISTRY = {}

# Registration decorator
def register_config(cls):
    alias = cls.alias()
    CONFIG_REGISTRY[alias] = cls
    return cls
```

## Configuration Hierarchy Example

```
BaseModelConfig (abstract)
└── GroqBaseConfig
    ├── MixtralEightXSevenBConfig
    ├── LlamaThreeSeventyBConfig
    └── GemmaTwoNineBConfig
```

## Usage Examples

### Defining a Provider Base Configuration

```python
class GroqBaseConfig(BaseModelConfig):
    def __init__(self):
        # Initialize Groq-specific parameters
        self.temperature = 0.7
        self.max_tokens = 1024
        self.api_key_env = "GROQ_API_KEY"
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.model = None  # Will be set by model subclasses
        self.system_message = "You are a helpful assistant."
        self.stream = False
        self.stop = None

    def get_params(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "api_key": os.getenv(self.api_key_env, ""),
            "system_message": self.system_message,
            "stream": self.stream,
            "stop": self.stop
        }

    def caller_class(self):
        from ..callers.groq_caller import GroqCaller
        return GroqCaller
```

### Creating Model-Specific Configurations

```python
@register_config
class LlamaThreeSeventyBConfig(GroqBaseConfig):
    @classmethod
    def alias(cls) -> str:
        return "llama3-70b"

    def __init__(self):
        super().__init__()
        self.model = "llama3-70b-8192"
        self.max_tokens = 8192
```

### Factory Function Pattern

```python
def create_groq_model(model_alias: str, **kwargs):
    """Factory function to create and configure a Groq model with custom parameters."""
    if model_alias not in CONFIG_REGISTRY:
        raise ValueError(f"Model alias '{model_alias}' not found.")
        
    config_cls = CONFIG_REGISTRY[model_alias]
    config_obj = config_cls()
    
    # Apply custom parameters
    for key, value in kwargs.items():
        if hasattr(config_obj, key):
            setattr(config_obj, key, value)
    
    return config_obj

# Usage
custom_model = create_groq_model("mixtral-8x7b", temperature=0.9)
```

## Best Practices

1. **Clear Aliases**: Use consistent naming patterns for model aliases
2. **Inheritance**: Reuse code through the provider base classes
3. **Documentation**: Include model specifics in docstrings
4. **Environment Variables**: Use environment variables for API keys
5. **Method Overriding**: Only override methods when necessary
