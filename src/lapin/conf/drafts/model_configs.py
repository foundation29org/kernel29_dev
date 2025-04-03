# model_configs.py
from config_registry import CONFIG_REGISTRY

# Import each config file so that classes are registered
import anthropic_configs
import bedrock_claude_configs
import azure_llama_configs
import azure_cohere_configs
import vertex_gemini_configs
import mistral_configs
import azure_openai_chat_configs
import openai_chat_configs

# Now, all model config classes are registered in CONFIG_REGISTRY.
# You can inspect or use CONFIG_REGISTRY here.
def list_registered_configs():
    return list(CONFIG_REGISTRY.keys())

if __name__ == "__main__":
    print("Available Config Aliases:")
    for alias in list_registered_configs():
        print(" -", alias)
