# model_handler.py
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
load_dotenv()
from lapin.conf.base_conf import CONFIG_REGISTRY #relative import, this will work?

class ModelHandler:
    """
    Manages the orchestration between configuration classes and caller classes.
    """
    def __init__(self, alias: str = None, verbose: bool = False):  
        self.verbose = verbose
        if not alias:
            self.config_cls = None
            self.config_obj = None
            self.caller_cls = None
            self.model_tracker = None   
        else:
            self._set_handler(alias)

        # Optionally, you can store state here or load more context if needed
    def _set_handler(self, alias: str):

        self.config_cls = CONFIG_REGISTRY.get(alias)

        if not self.config_cls:
            raise ValueError(f"No configuration found for alias '{alias}'.")

        self.config_obj = self.config_cls() 
        if self.verbose:
            print (f"config_obj: {self.config_obj}") # Instantiate the configuration
        self.caller_cls = self.config_obj.caller_class()    
        tracker_cls = self.config_obj.tracker_class()() #TODO: dont understand why this is needed ()()
        # tracker_cls = tracker_cls()
        model_name = self.config_obj.model
        if self.verbose:
            print (f"model_name: {model_name}, alias: {alias}")
            print (f"tracker_cls: {tracker_cls}")
            print (f"tracker_cls: {tracker_cls.provider_name}")
        mname = tracker_cls.get_model(model_name=model_name) 
        self.model_tracker = tracker_cls.get_model(model_name=model_name)  
        if self.verbose:
            print (f"model_tracker: {self.model_tracker}")
            # input("Press Enter to continue...")
        return self

    def get_response(self, prompt: str, alias: str,  only_text: bool = True) -> str:
        """
        High-level method that:
          1) Looks up the config class by alias in CONFIG_REGISTRY.
          2) Instantiates the config object.
          3) Retrieves the caller class from config.caller_class().
          4) Builds the caller with config.get_params().
          5) Calls the LLM and returns the text.
        """
        if alias:
            self._set_handler(alias)

        if not self.config_obj:
            raise ValueError("You must set the alias first.")

        # Check rate limits before making the call
        should_pause, reason = self.model_tracker.should_pause()
        if should_pause:
            print(f"Rate limit approaching: {reason}")
            print("Waiting for limits to reset...")
            # In a real implementation, you would wait here
            
             # print ("c")

        params = self.config_obj.get_params()
        #TODO: try that caller_cls is same as caller, then set params,
         # to allwais have the same caller and hence set the history of messages, if not,
        #  each caller will set the messages to [], may be add if history, then set the history 
        # Mayne unneccesary if response is tracked externally, outside of this class
        caller = self.caller_cls(params)
        response, parsed_response = caller.call_llm(prompt)

        # print(response.usage)
        # print(type(response.usage)	)


        if hasattr(self.model_tracker, 'record_request_by_provider'):
            self.model_tracker.record_request_by_provider(response)
        elif hasattr(self.model_tracker, 'record_request'):
            # Fallback to generic request recording
            self.model_tracker.record_request(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
        



        if only_text:
            return parsed_response
        else:
            return response, parsed_response

    # def prompt_price(self, prompt_tokens: int, completion_tokens: int, scale: int = 1) -> float:
    #     return self.model_tracker.prompt2price(prompt_tokens, completion_tokens, scale)
    # Additional methods could be added here. For example:
    # - a method to list available aliases
    # - a method to refresh environment variables
    # - concurrency or request tracking
    def list_available_models(self) -> List[str]:
        """
        Return a list of all available model aliases.
        """
        return sorted(CONFIG_REGISTRY.keys())