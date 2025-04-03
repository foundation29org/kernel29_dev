import llm_calls

# Access classes directly
anthropic = llm_calls.AnthropicCaller(params=...)
openai = llm_calls.OpenAIChatCaller(params=...)
from llm_calls import OpenAIChatCaller
caller = OpenAIChatCaller(params=...)
