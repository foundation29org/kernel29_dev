# handlers/async_model_handler.py
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()
from lapin.conf.base_conf import CONFIG_REGISTRY #relative import, this will work?

class AsyncModelHandler:
    """
    Async version of ModelHandler for working with asynchronous LLM operations.
    """
    def __init__(self):
        # Optionally, you can store state here or load more context if needed
        pass

    async def get_response(self, prompt: str, alias: str, only_text: bool = True) -> Any:
        """
        High-level method that:
          1) Looks up the config class by alias in CONFIG_REGISTRY.
          2) Instantiates the config object.
          3) Retrieves the async caller class from config.async_caller_class().
          4) Builds the caller with config.get_params().
          5) Calls the LLM asynchronously and returns the text.
          
        Args:
            prompt: The prompt to send to the LLM
            alias: Model alias in the CONFIG_REGISTRY
            only_text: Whether to return only the parsed text or the full response
            
        Returns:
            Either the parsed text response or a tuple of (raw_response, parsed_text)
        """
        from lapin.conf.base_conf import CONFIG_REGISTRY
        
        config_cls = CONFIG_REGISTRY.get(alias)
        if not config_cls:
            raise ValueError(f"No configuration found for alias '{alias}'.")
            
        config_obj = config_cls()  # Instantiate the configuration
        model_name = config_obj.model
        
        # Get the appropriate async caller class
        if hasattr(config_obj, 'async_caller_class'):
            caller_cls = config_obj.async_caller_class()
        else:
            raise ValueError(f"Model '{alias}' does not support async operations")
            
        # Get tracker for rate limiting
        tracker_cls = config_obj.tracker_class()
        model_tracker = tracker_cls.get_model(model_name)

        # Check rate limits before making the call
        should_pause, reason = model_tracker.should_pause()
        if should_pause:
            print(f"Rate limit approaching: {reason}")
            print("Waiting for limits to reset...")
            # In a real implementation, you would wait here
            # or implement backoff strategy
            
        # Get parameters and instantiate the caller
        params = config_obj.get_params()
        caller = caller_cls(params)
        
        # Call the LLM asynchronously
        response, parsed_response = await caller.call_llm_async(prompt)
        
        # Record the request in the tracker
        # Adjust this based on how your tracker is implemented
        if hasattr(model_tracker, 'record_request_by_provider'):
            model_tracker.record_request_by_provider(response)
        elif hasattr(model_tracker, 'record_request'):
            # Fallback to generic request recording
            model_tracker.record_request(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
        
        if only_text:
            return parsed_response
        else:
            return response, parsed_response
            
    def list_available_models(self) -> List[str]:
        """
        Return a list of all available model aliases.
        """
        from lapin.conf.base_conf import CONFIG_REGISTRY
        return sorted(CONFIG_REGISTRY.keys())
        
