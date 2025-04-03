import os

import sys
# Add the parent directory of llm_libs to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


from llm_libs.handlers.base_handler import ModelHandler

from dotenv import load_dotenv
load_dotenv()


query =  "Explain quantum computing in simple terms."
model = "llama3-8b"         # Llama 3 8B
handler = ModelHandler()
all_models = handler.list_available_models()
print (all_models)
response = handler.get_response(model, query)
print (response)
