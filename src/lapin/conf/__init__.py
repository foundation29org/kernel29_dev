# __init__.py
from .base_conf import CONFIG_REGISTRY, register_config

# Import each config file so that the @register_config decorators run
from . import anthropic_conf
from . import groq_conf
# from . import bedrock_claude_conf
# from . import azure_llama_conf
# from . import azure_cohere_conf
# from . import vertex_gemini_conf
# from . import mistral_conf
# from . import azure_openai_chat_conf
# from . import openai_chat_conf

# Optionally, define a helper function to see all aliases


# Optionally define what is public in this package
__all__ = [
    "base_conf",
    "register_config",
    "anthropic_conf",
    "groq_conf"

]

# __all__ = [
#     "CONFIG_REGISTRY",
#     "register_config",
#     "anthropic_conf",
#     "bedrock_claude_conf",
#     "azure_llama_conf",
#     "azure_cohere_conf",
#     "vertex_gemini_conf",
#     "mistral_conf",
#     "azure_openai_chat_conf",
#     "openai_chat_conf",
#     "list_registered_conf",
# ]