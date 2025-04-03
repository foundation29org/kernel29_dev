#!/usr/bin/env python3
"""
Example usage of the LLM Microframework with Groq models.

This script demonstrates how to use the ModelHandler to interact with
various Groq models through a consistent interface.

Before running:
1. Install the required packages: pip install groq
2. Set your GROQ_API_KEY environment variable
   export GROQ_API_KEY=your-api-key
"""
import os

import sys
# Add the parent directory of llm_libs to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


from llm_libs.handlers.base_handler import ModelHandler

# Now try to import
try:
    from llm_libs.handlers.base_handler import ModelHandler
    print("Successfully imported ModelHandler")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Looking for file at: {os.path.join(parent_dir, 'llm_libs', 'handlers', 'base_handler.py')}")
    print(f"This file exists: {os.path.exists(os.path.join(parent_dir, 'llm_libs', 'handlers', 'base_handler.py'))}")
    
    # Check for config_registry
    registry_path = os.path.join(parent_dir, 'llm_libs', 'conf', 'config_registry.py')
    print(f"Looking for config_registry at: {registry_path}")
    print(f"This file exists: {os.path.exists(registry_path)}")
    
    # List files in the conf directory
    conf_dir = os.path.join(parent_dir, 'llm_libs', 'conf')
    if os.path.exists(conf_dir):
        print(f"Files in conf directory: {os.listdir(conf_dir)}")
    else:
        print(f"Conf directory doesn't exist: {conf_dir}")
    
    sys.exit(1)
import time
from handlers.base_handler import ModelHandler


from dotenv import load_dotenv
load_dotenv()


def print_separator():
    """Print a separator line for better readability."""
    print("\n" + "=" * 80 + "\n")

def main():
    """Demonstrate the LLM Microframework with various Groq models."""
    # Check if API key is set
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Please set it using: export GROQ_API_KEY=your-api-key")
        return

    # Create a handler
    handler = ModelHandler()

    # List all available models
    all_models = handler.list_available_models()
    print(f"All available models: {all_models}")
    
    # Filter to get only Groq models (assuming all Groq models start with certain prefixes)
    groq_model_prefixes = [
        "llama", "mixtral", "gemma", "qwen", "mistral-saba", "deepseek"
    ]
    groq_models = [model for model in all_models if any(model.startswith(prefix) for prefix in groq_model_prefixes)]
    
    print(f"\nAvailable Groq models: {groq_models}")
    print_separator()

    # Define a set of queries to test with different models
    test_queries = [
        "Explain quantum computing in simple terms.",
        "Write a short poem about artificial intelligence.",
        "What are the main challenges in climate change mitigation?",
        "Compare and contrast REST APIs and GraphQL."
    ]

    # Test a subset of Groq models with different queries
    models_to_test = [
        "mixtral-8x7b",      # Mixtral 8x7B
        "llama3-8b",         # Llama 3 8B
        "gemma2-9b"          # Gemma 2 9B
    ]

    for i, model_alias in enumerate(models_to_test):
        if model_alias not in all_models:
            print(f"Model {model_alias} is not available. Skipping...")
            continue
            
        print(f"Testing model: {model_alias}")
        
        # Use a different query for each model
        query = test_queries[i % len(test_queries)]
        print(f"Query: {query}")
        
        # Measure response time
        start_time = time.time()
        

        response = handler.get_response(model_alias, query)
        elapsed_time = time.time() - start_time
        
        print(f"Response (in {elapsed_time:.2f} seconds):")
        print(response)

        
        print_separator()
    
    # Advanced usage: JSON mode with Mixtral
    print("Advanced usage: JSON mode with Mixtral model")
    json_query = "List the top 3 programming languages and their key features in JSON format."
    
    try:
        # Create a handler for each example to demonstrate different configurations
        json_handler = ModelHandler()
        
        # This requires modifying the configuration before using it
        # For example purposes, we'll just include instructions in the prompt
        json_prompt = f"""
        You must respond with valid JSON only, using the following format:
        {{
          "programming_languages": [
            {{
              "name": "language name",
              "key_features": ["feature1", "feature2", "feature3"],
              "typical_use_cases": ["use case 1", "use case 2"]
            }},
            ...
          ]
        }}

        Query: {json_query}
        """
        
        response = json_handler.get_response("mixtral-8x7b", json_prompt)
        print(response)
    except Exception as e:
        print(f"Error with JSON mode: {str(e)}")
    
    print_separator()

if __name__ == "__main__":
    main()
