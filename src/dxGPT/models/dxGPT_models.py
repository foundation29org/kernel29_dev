from lapin.conf.groq_conf import GroqBaseConfig

from lapin.conf.base_conf import register_config



@register_config
class LlamaThreeEightBConfig(GroqBaseConfig):
    """
    For "llama3-8b-8192" model.
    8,192 context window.
    """
    @classmethod
    def alias(cls) -> str:
        return "llama3-8b"

    def __init__(self):
        super().__init__()
        self.model = "llama3-8b-8192"
        self.max_tokens = 8192
        self.response_format = {"type": "json_object"}



# List of models identified in the original batch_diagnosis_*.py scripts:
# Anthropic API:
#   - claude-3-opus-20240229 (alias: c3opus) - temp=0, max_tokens=2000
#   - claude-3-5-sonnet-20240620 (alias: c35sonnet) - temp=0, max_tokens=2000
# AWS Bedrock:
#   - anthropic.claude-3-sonnet-20240229-v1:0 (alias: c3sonnet) - temp=0, max_tokens=2000
#     * Potential Refactor: Needs AWSBedrockConfig base class, modelId="anthropic.claude-3-sonnet-20240229-v1:0".
#   - mistral.mixtral-8x7b-instruct-v0:1 (alias: mistralmoe) - temp=0, max_tokens=800
#     * Potential Refactor: Needs AWSBedrockConfig base class, modelId="mistral.mixtral-8x7b-instruct-v0:1".
#   - mistral.mistral-7b-instruct-v0:2 (alias: mistral7b) - temp=0, max_tokens=800
#     * Potential Refactor: Needs AWSBedrockConfig base class, modelId="mistral.mistral-7b-instruct-v0:2".
# Azure ML Endpoint:
#   - Llama-2-7b-chat-dxgpt (alias: llama2_7b) - temp=0, max_tokens=800
#   - llama-3-8b-chat-dxgpt (alias: llama3_8b) - temp=0, max_tokens=800
#   - llama-3-70b-chat-dxgpt (alias: llama3_70b) - temp=0, max_tokens=800
#   - Cohere-command-r-plus-dxgpt (alias: cohere_cplus) - temp=0, max_tokens=800
#     * Potential Refactor: Needs AzureMLConfig base class, handling endpoint_url, api_key, deployment_name, model_kwargs={"temperature": T, "max_new_tokens": M}.
# GCP Vertex AI:
#   - gemini-1.5-pro-preview-0409 (alias: geminipro) - temp=0, max_tokens=800
#     * Potential Refactor: Needs GCPVertexAIConfig base class, handling credentials, project_id, region, generation_config.
# Azure OpenAI Service:
#   - gpt-4 (0613 deployment, alias: gpt4_0613azure) - temp=0, max_tokens=2000
#   - gpt-4-turbo (1106 deployment 'nav29turbo', alias: gpt4turboazure) - temp=0, max_tokens=800
#     * Potential Refactor: Needs AzureOpenAIConfig base class, handling deployment names, api_version.
# OpenAI API:
#   - gpt-4-1106-preview (alias: gpt4turbo1106) - temp=0, max_tokens=800
#   - gpt-4-turbo-2024-04-09 (alias: gpt4turbo0409) - temp=0, max_tokens=800
#   - gpt-4o (alias: gpt4o) - temp=0, max_tokens=800
#   - o1-mini (alias: o1_mini) - temp=1.0
#   - o1-preview (alias: o1_preview) - temp=1.0
# Mistral API:
#   - open-mixtral-8x22b (alias: mistralmoebig) - temp=0, max_tokens=800
#     * Potential Refactor: Needs MistralConfig base class.




# @register_config
# from lapin.conf.openai_conf import OpenAIConfig
# class GPT4oConfig(OpenAIConfig):
#     """
#     Configuration for GPT-4o model.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4o"

#     def __init__(self):
#         super().__init__()
#         self.model = "gpt-4o" # Standard OpenAI model name
#         self.max_tokens = 4096 # Default for gpt-4o, adjust if needed
#         self.temperature = 0.0 # As used in the original script
#         # Add other relevant params if needed, e.g., response_format



# from lapin.conf.anthropic_conf import AnthropicConfig
# @register_config
# class Claude35SonnetConfig(AnthropicConfig):
#     """
#     Configuration for Claude 3.5 Sonnet (New).
#     Assumes the standard Anthropic API via lapin.
#     Model name `claude-3-5-sonnet-20240620` is inferred.
#     The `_new` suffix might indicate a specific fine-tune or version not directly mappable,
#     using the standard latest 3.5 Sonnet as the base.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "c35sonnet_new"

#     def __init__(self):
#         super().__init__()
#         # Assuming the latest 3.5 sonnet model identifier
#         self.model = "claude-3-5-sonnet-20240620"
#         self.max_tokens = 4096 # Common default, adjust if needed
#         self.temperature = 0.0 # As used in the original script
#         # Anthropic might use different param names (e.g., max_tokens_to_sample)
#         # self.max_tokens_to_sample = 2000 # From original script

# @register_config
# class O1PreviewConfig(OpenAIConfig):
#     """
#     Configuration for o1-preview model.
#     Accessed via OpenAI API.
#     The original script set temperature=1 for this model.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "o1_preview"

#     def __init__(self):
#         super().__init__()
#         self.model = "o1-preview" # The literal model name used
#         self.max_tokens = 4096 # Default guess, adjust as needed
#         self.temperature = 1.0 # Specific temperature from original script


# @register_config
# class O1MiniConfig(OpenAIConfig):
#     """
#     Configuration for o1-mini model.
#     Accessed via OpenAI API.
#     The original script set temperature=1 for this model.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "o1_mini"

#     def __init__(self):
#         super().__init__()
#         self.model = "o1-mini" # The literal model name used
#         self.max_tokens = 4096 # Default guess, adjust as needed
#         self.temperature = 1.0 # Specific temperature from original script


# --- OpenAI API Models ---

# @register_config
# class GPT4Turbo1106Config(OpenAIConfig):
#     """
#     Configuration for gpt-4-1106-preview model via OpenAI API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4turbo1106"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "gpt-4-1106-preview"
#         self.max_tokens = 800 # From original script
#         self.temperature = 0.0 # From original script
#         # Base OpenAIConfig likely handles API key via OPENAI_API_KEY env var.

# @register_config
# class GPT4Turbo0409Config(OpenAIConfig):
#     """
#     Configuration for gpt-4-turbo-2024-04-09 model via OpenAI API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4turbo0409"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "gpt-4-turbo-2024-04-09"
#         self.max_tokens = 800 # From original script
#         self.temperature = 0.0 # From original script
#         # Base OpenAIConfig likely handles API key via OPENAI_API_KEY env var.

# @register_config
# class GPT4oConfig(OpenAIConfig):
#     """
#     Configuration for GPT-4o model via OpenAI API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4o"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "gpt-4o"
#         self.max_tokens = 800 # From original script (Note: API default might be higher)
#         self.temperature = 0.0 # From original script
#         # Base OpenAIConfig likely handles API key via OPENAI_API_KEY env var.

# @register_config
# class O1PreviewConfig(OpenAIConfig):
#     """
#     Configuration for o1-preview model.
#     Accessed via OpenAI API.
#     The original script set temperature=1 for this model.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "o1_preview"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "o1-preview" # The literal model name used
#         self.max_tokens = 4096 # Default guess from previous state, original unknown
#         self.temperature = 1.0 # Specific temperature from original script
#         # Base OpenAIConfig likely handles API key via OPENAI_API_KEY env var.


# @register_config
# class O1MiniConfig(OpenAIConfig):
#     """
#     Configuration for o1-mini model.
#     Accessed via OpenAI API.
#     The original script set temperature=1 for this model.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "o1_mini"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "o1-mini" # The literal model name used
#         self.max_tokens = 4096 # Default guess from previous state, original unknown
#         self.temperature = 1.0 # Specific temperature from original script
#         # Base OpenAIConfig likely handles API key via OPENAI_API_KEY env var.


# --- Anthropic API Models ---

# @register_config
# class Claude3OpusConfig(AnthropicConfig):
#     """
#     Configuration for claude-3-opus-20240229 model via Anthropic API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "c3opus"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "claude-3-opus-20240229"
#         self.max_tokens = 2000 # From original script (Base class might map to max_tokens_to_sample)
#         self.temperature = 0.0 # From original script
#         # Base AnthropicConfig likely handles API key via ANTHROPIC_API_KEY env var.


# @register_config
# class Claude35SonnetConfig(AnthropicConfig):
#     """
#     Configuration for claude-3-5-sonnet-20240620 model via Anthropic API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "c35sonnet"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "claude-3-5-sonnet-20240620"
#         self.max_tokens = 2000 # From original script (Base class might map to max_tokens_to_sample)
#         self.temperature = 0.0 # From original script
#         # Base AnthropicConfig likely handles API key via ANTHROPIC_API_KEY env var.


# --- AWS Bedrock Models ---
# Note: Require implementation of AWSBedrockConfig base class

# @register_config
# class Claude3SonnetBedrockConfig(AWSBedrockConfig):
#     """
#     Configuration for anthropic.claude-3-sonnet-20240229-v1:0 via AWS Bedrock.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "c3sonnet"
#
#     def __init__(self):
#         super().__init__()
#         self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0" # Bedrock modelId is often distinct from model name
#         self.max_tokens = 2000
#         self.temperature = 0.0
#         self.aws_region = "us-east-1" # From original script
#         self.request_accept = "application/json"
#         self.request_content_type = "application/json"
#         # Base AWSBedrockConfig would use these attributes to init Boto3 client,
#         # likely retrieving credentials via BEDROCK_USER_KEY and BEDROCK_USER_SECRET env vars,
#         # format the request body (e.g., with {"anthropic_version": "bedrock-2023-05-31", "messages": ...}),
#         # and call invoke_model.

# @register_config
# class MistralMoEBedrockConfig(AWSBedrockConfig):
#     """
#     Configuration for mistral.mixtral-8x7b-instruct-v0:1 via AWS Bedrock.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "mistralmoe"
#
#     def __init__(self):
#         super().__init__()
#         self.model_id = "mistral.mixtral-8x7b-instruct-v0:1"
#         self.max_tokens = 800
#         self.temperature = 0.0
#         self.aws_region = "us-east-1"
#         self.request_accept = "application/json"
#         self.request_content_type = "application/json"
#         self.prompt_template = "<s>[INST] {prompt} [/INST]" # Prompt formatting used
#         self.request_body_params = {"top_p": 1} # Other params used in original script
#         # Base AWSBedrockConfig would use these attributes, format the prompt,
#         # likely retrieving credentials via BEDROCK_USER_KEY and BEDROCK_USER_SECRET env vars,
#         # build the request body, and call invoke_model.

# @register_config
# class Mistral7bBedrockConfig(AWSBedrockConfig):
#     """
#     Configuration for mistral.mistral-7b-instruct-v0:2 via AWS Bedrock.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "mistral7b"
#
#     def __init__(self):
#         super().__init__()
#         self.model_id = "mistral.mistral-7b-instruct-v0:2"
#         self.max_tokens = 800
#         self.temperature = 0.0
#         self.aws_region = "us-east-1"
#         self.request_accept = "application/json"
#         self.request_content_type = "application/json"
#         self.prompt_template = "<s>[INST] {prompt} [/INST]"
#         self.request_body_params = {"top_p": 1}
#         # Base AWSBedrockConfig would use these attributes, format the prompt,
#         # likely retrieving credentials via BEDROCK_USER_KEY and BEDROCK_USER_SECRET env vars,
#         # build the request body, and call invoke_model.


# --- Azure ML Endpoint Models ---
# Note: Require implementation of AzureMLConfig base class

# @register_config
# class Llama27bAzureMLConfig(AzureMLConfig):
#     """
#     Configuration for Llama-2-7b-chat-dxgpt via Azure ML Endpoint.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "llama2_7b"
#
#     def __init__(self):
#         super().__init__()
#         self.deployment_name = "Llama-2-7b-chat-dxgpt"
#         self.max_tokens = 800 # Original script uses "max_new_tokens"
#         self.temperature = 0.0
#         self.api_type = "serverless"
#         # self.content_formatter = CustomOpenAIChatContentFormatter() # Needs import/definition
#         # Base AzureMLConfig would use these attributes, potentially mapping max_tokens
#         # back to max_new_tokens in model_kwargs, retrieving endpoint URL via AZURE_ML_ENDPOINT env var,
#         # retrieving API key via AZURE_ML_API_KEY env var, and initialize/call AzureMLChatOnlineEndpoint.

# @register_config
# class Llama38bAzureMLConfig(AzureMLConfig):
#      """
#      Configuration for llama-3-8b-chat-dxgpt via Azure ML Endpoint.
#      """
#      @classmethod
#      def alias(cls) -> str:
#          return "llama3_8b"
#
#      def __init__(self):
#          super().__init__()
#          self.deployment_name = "llama-3-8b-chat-dxgpt"
#          self.max_tokens = 800 # Original script uses "max_new_tokens"
#          self.temperature = 0.0
#          self.api_type = "serverless"
#          # self.content_formatter = CustomOpenAIChatContentFormatter()
#          # Base AzureMLConfig would use these attributes, retrieve endpoint URL via AZURE_ML_ENDPOINT_3 env var,
#          # retrieve API key via AZURE_ML_API_KEY_3 env var, and call endpoint.

# @register_config
# class Llama370bAzureMLConfig(AzureMLConfig):
#      """
#      Configuration for llama-3-70b-chat-dxgpt via Azure ML Endpoint.
#      """
#      @classmethod
#      def alias(cls) -> str:
#          return "llama3_70b"
#
#      def __init__(self):
#          super().__init__()
#          self.deployment_name = "llama-3-70b-chat-dxgpt"
#          self.max_tokens = 800 # Original script uses "max_new_tokens"
#          self.temperature = 0.0
#          self.api_type = "serverless"
#          # self.content_formatter = CustomOpenAIChatContentFormatter()
#          # Base AzureMLConfig would use these attributes, retrieve endpoint URL via AZURE_ML_ENDPOINT_4 env var,
#          # retrieve API key via AZURE_ML_API_KEY_4 env var, and call endpoint.

# @register_config
# class CohereCommandRPlusAzureMLConfig(AzureMLConfig):
#      """
#      Configuration for Cohere-command-r-plus-dxgpt via Azure ML Endpoint.
#      """
#      @classmethod
#      def alias(cls) -> str:
#          return "cohere_cplus"
#
#      def __init__(self):
#          super().__init__()
#          self.deployment_name = "Cohere-command-r-plus-dxgpt"
#          self.max_tokens = 800 # Original script uses "max_new_tokens"
#          self.temperature = 0.0
#          self.api_type = "serverless"
#          # self.content_formatter = CustomOpenAIChatContentFormatter()
#          # Base AzureMLConfig would use these attributes, retrieve endpoint URL via AZURE_ML_ENDPOINT_2 env var,
#          # retrieve API key via AZURE_ML_API_KEY_2 env var, and call endpoint.


# --- GCP Vertex AI Models ---
# Note: Require implementation of GCPVertexAIConfig base class

# @register_config
# class GeminiProVertexConfig(GCPVertexAIConfig):
#     """
#     Configuration for gemini-1.5-pro-preview-0409 via GCP Vertex AI.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "geminipro"
#
#     def __init__(self):
#         super().__init__()
#         self.model_name = "gemini-1.5-pro-preview-0409"
#         self.max_tokens = 800 # Original script uses "max_output_tokens"
#         self.temperature = 0.0
#         self.project_id = "nav29-21389"
#         self.region = "us-central1"
#         self.credentials_file = "./nav29-21389-c1a94e300dcb.json" # Or path from env var
#         self.generation_config_params = {"top_p": 1, "top_k": 32} # Other gen config params
#         self.safety_settings = {} # Safety settings used
#         # Base GCPVertexAIConfig would use these attributes to init vertexai,
#         # get credentials (potentially via self.credentials_file or GOOGLE_APPLICATION_CREDENTIALS env var),
#         # build generation_config (mapping max_tokens), and call generate_content.


# --- Azure OpenAI Service Models ---
# Note: Require implementation of AzureOpenAIConfig base class

# @register_config
# class GPT40613AzureConfig(AzureOpenAIConfig):
#     """
#     Configuration for gpt-4 (0613 deployment) via Azure OpenAI Service.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4_0613azure"
#
#     def __init__(self):
#         super().__init__()
#         # Deployment name was fetched via env var in original script
#         # Base class should handle retrieving this via DEPLOYMENT_NAME env var.
#         self.deployment_name = os.getenv("DEPLOYMENT_NAME", "YOUR_GPT4_0613_DEPLOYMENT_NAME") # Example fallback if not handled by base
#         self.model = "gpt-4" # Underlying model name
#         self.max_tokens = 2000
#         self.temperature = 0.0
#         self.model_kwargs = {"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0}
#         # Base AzureOpenAIConfig likely inherits from OpenAIConfig, adding handling
#         # for deployment_name, API version via OPENAI_API_VERSION env var,
#         # endpoint via AZURE_OPENAI_ENDPOINT env var, and using the specific Azure key
#         # via AZURE_OPENAI_API_KEY env var.

# @register_config
# class GPT4TurboAzureConfig(AzureOpenAIConfig):
#     """
#     Configuration for gpt-4-turbo (1106 deployment 'nav29turbo') via Azure OpenAI Service.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "gpt4turboazure"
#
#     def __init__(self):
#         super().__init__()
#         self.deployment_name = "nav29turbo" # Specific deployment name from original
#         self.model = "gpt-4-turbo" # Underlying model (likely 1106-preview based on deployment name)
#         self.max_tokens = 800
#         self.temperature = 0.0
#         self.model_kwargs = {"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0}
#         # Base AzureOpenAIConfig handles the specifics, likely retrieving API version via
#         # OPENAI_API_VERSION env var, endpoint via AZURE_OPENAI_ENDPOINT env var,
#         # and key via AZURE_OPENAI_API_KEY env var.


# --- Mistral API Models ---
# Note: Require implementation of MistralConfig base class

# @register_config
# class MistralMoEBigMistralConfig(MistralConfig):
#     """
#     Configuration for open-mixtral-8x22b via Mistral API.
#     """
#     @classmethod
#     def alias(cls) -> str:
#         return "mistralmoebig"
#
#     def __init__(self):
#         super().__init__()
#         self.model = "open-mixtral-8x22b"
#         self.max_tokens = 800
#         self.temperature = 0.0
#         # Base MistralConfig would initialize the Mistral client, likely retrieving the
#         # API key via MISTRAL_API_KEY env var, and call client.chat.complete().

